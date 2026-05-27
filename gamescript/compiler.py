"""
Главный модуль компилятора GameScript → C++.

Собирает все этапы вместе:
    1. Лексинг (строка → токены)
    2. Парсинг (токены → AST)
    3. Разрешение импортов (@load, ~grab, &link)
    4. Генерация C++ кода
"""

import subprocess

from pathlib import Path
from typing import Optional, Set, List

from .lexer import Lexer
from .parser import Parser, ParseError
from .codegen_cpp import CppCodeGen, BUILTIN_LIBS
from .ast_nodes import (
    Program, DictDef, ClassDef, MethodDef,
    LoadStmt, GrabStmt, LinkStmt, ASTNode
)


# Допустимые расширения файлов GameScript
ALLOWED_EXTENSIONS = {'.gs', '.gscript'}


RUNTIME_H = '''#pragma once
#include <string>
#include <vector>
#include <map>
#include <any>
#include <iostream>
#ifdef HAS_SDL2
#include <SDL2/SDL.h>
#include <SDL2/SDL_image.h>
#endif

class Entity {
public:
    std::string name;
    std::string image_path;
    int x = 0, y = 0;
    int hp = 100, max_hp = 100;
    int mp = 50, max_mp = 50;
    int attack = 10, defense = 5;
    float speed = 1.0f;
    int level = 1, exp = 0;
    bool is_alive = true;
    
#ifdef HAS_SDL2
    SDL_Texture* texture = nullptr;
    
    virtual void load(SDL_Renderer* renderer) {
        if (!image_path.empty()) {
            SDL_Surface* surface = IMG_Load(image_path.c_str());
            if (surface) {
                texture = SDL_CreateTextureFromSurface(renderer, surface);
                SDL_FreeSurface(surface);
            }
        }
    }
    
    virtual void draw(SDL_Renderer* renderer) {
        if (texture) {
            SDL_Rect dst = {x, y, 32, 32};
            SDL_RenderCopy(renderer, texture, nullptr, &dst);
        }
    }
    
    virtual ~Entity() {
        if (texture) SDL_DestroyTexture(texture);
    }
#endif
    
    virtual void on_create() {}
    virtual void on_turn(Entity& target) {}
};

class System {
public:
    virtual ~System() = default;
    virtual void on_start() {}
    virtual void on_update() {}
};
'''

def ensure_runtime(output_dir: Path):
    """Создаёт runtime.h если его нет."""
    runtime_path = output_dir / 'runtime.h'
    if not runtime_path.exists():
        runtime_path.write_text(RUNTIME_H, encoding='utf-8')


def compile_text(source: str, output_path: Optional[str] = None,
                 base_path: Optional[Path] = None,
                 already_imported: Optional[Set[str]] = None,
                 build: bool = False) -> str:
    if already_imported is None:
        already_imported = set()
    
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = CppCodeGen()

    for stmt in ast.statements:
        if isinstance(stmt, LoadStmt):
            if not stmt.optional:
                stem = stmt.filename.rsplit('.', 1)[0].split('/')[-1]
                if stem not in BUILTIN_LIBS:
                    filepath = _find_file(stmt.filename, base_path or Path.cwd())
                    if filepath is None:
                        raise ParseError(f"@load: файл не найден: {stmt.filename}", 0, 0)
            gen.add_load(stmt)
        elif isinstance(stmt, GrabStmt):
            gen.add_grab(stmt)
        elif isinstance(stmt, LinkStmt):
            gen.add_link(stmt)
    
    cpp_code = gen.generate(ast)
    
    if build:
        cpp_code += '\n' + gen.generate_main(ast)
    
    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cpp_code, encoding='utf-8')
        print(f'✓ Сгенерирован {output_path}')
    
    return cpp_code


def resolve_imports(ast: Program, base_path: Path, 
                    already_imported: Set[str]) -> Program:
    """
    Рекурсивно разрешает все импорты.
    
    Для @load загружает содержимое файла и добавляет его определения в AST.
    Для ~grab ищет указанные имена в загруженных файлах.
    Для &link ищет указанные функции в загруженных файлах.
    """
    new_statements = []
    
    for stmt in ast.statements:
        if isinstance(stmt, LoadStmt):
            # Просто оставляем как есть — кодген добавит #include
            new_statements.append(stmt)
        elif isinstance(stmt, GrabStmt):
            # ~grab / ~grab? — захватывает конкретные имена
            grabbed = _handle_grab(stmt, base_path, already_imported)
            new_statements.extend(grabbed)
        elif isinstance(stmt, LinkStmt):
            # &link / &link? — захватывает функции
            linked = _handle_link(stmt, base_path, already_imported)
            new_statements.extend(linked)
        else:
            # Обычное определение (словарь, класс) — оставляем как есть
            new_statements.append(stmt)
    
    ast.statements = new_statements
    return ast


def _handle_grab(stmt: GrabStmt, base_path: Path,
                 already_imported: Set[str]) -> List[ASTNode]:
    results = []
    
    for name, alias in stmt.names:
        found = None
        
        # Ищем во всех .gs файлах
        for f in base_path.glob("*.gs"):
            source = f.read_text(encoding='utf-8')
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            for s in ast.statements:
                if isinstance(s, (DictDef, ClassDef)) and s.name == name:
                    if alias:
                        s.name = alias
                    found = s
                    break
            if found:
                break
        
        if found:
            results.append(found)
        elif not stmt.optional:
            raise ParseError(f"~grab: имя не найдено: {name}", 0, 0)
    
    return results


def _handle_link(stmt: LinkStmt, base_path: Path,
                 already_imported: Set[str]) -> List[ASTNode]:
    results = []
    
    for name, alias in stmt.names:
        found = None
        
        for f in base_path.glob("*.gs"):
            source = f.read_text(encoding='utf-8')
            lexer = Lexer(source)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            for s in ast.statements:
                if isinstance(s, ClassDef):
                    for method in s.methods:
                        if method.name == name:
                            if alias:
                                method.name = alias
                            found = method
                            break
            if found:
                break
        
        if found:
            results.append(found)
        elif not stmt.optional:
            raise ParseError(f"&link: функция не найдена: {name}", 0, 0)
    
    return results


def _find_and_extract_name(name: str, alias: Optional[str],
                           already_imported: Set[str],
                           base_path: Path) -> Optional[ASTNode]:
    """
    Ищет класс или словарь по имени во всех уже загруженных файлах.
    Если найден и указан alias — переименовывает.
    """
    for filename in list(already_imported):
        filepath = _find_file(filename, base_path)
        if filepath is None:
            continue
        
        source = filepath.read_text(encoding='utf-8')
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        for s in ast.statements:
            if isinstance(s, (DictDef, ClassDef)) and s.name == name:
                if alias:
                    s.name = alias
                return s
    
    return None


def _find_and_extract_function(name: str, alias: Optional[str],
                                already_imported: Set[str],
                                base_path: Path) -> Optional[ASTNode]:
    """
    Ищет функцию (MethodDef) по имени во всех уже загруженных файлах.
    """
    for filename in list(already_imported):
        filepath = _find_file(filename, base_path)
        if filepath is None:
            continue
        
        source = filepath.read_text(encoding='utf-8')
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        
        for s in ast.statements:
            if isinstance(s, ClassDef):
                for method in s.methods:
                    if method.name == name:
                        if alias:
                            method.name = alias
                        return method
    
    return None


def _find_file(filename: str, base_path: Path) -> Optional[Path]:
    """
    Ищет файл по имени.
    Пробует как есть, потом добавляет .gs, потом .gscript.
    """
    # Пробуем как есть
    path = base_path / filename
    if path.exists():
        return path
    
    # Пробуем с расширениями
    for ext in ALLOWED_EXTENSIONS:
        path = base_path / (filename + ext)
        if path.exists():
            return path
    
    return None


def compile_file(input_path: str, output_path: Optional[str] = None, 
                 header_only: bool = False, build: bool = False) -> str:
    input_file = Path(input_path)
    
    if input_file.suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Неверное расширение файла: '{input_file.suffix}'. "
            f"GameScript принимает только {', '.join(ALLOWED_EXTENSIONS)} файлы."
        )
    
    source = input_file.read_text(encoding='utf-8')
    
    # Проверяем директиву в первой строке
    first_line = source.split('\n')[0].strip()
    if first_line == '# --header':
        header_only = True
    
    if output_path is None:
        suffix = '.h' if header_only else '.cpp'
        output_path = str(input_file.with_suffix(suffix))
    
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    ensure_runtime(output_dir)
    
    if header_only:
        return compile_header(source, output_path)
    
    cpp_code = compile_text(source, output_path, base_path=input_file.parent, build=build)
    
    if build:
        binary_path = str(Path(output_path).with_suffix(''))
        import subprocess
        result = subprocess.run(
            ['g++', '-std=c++17', '-DHAS_SDL2', '-I', str(output_dir), 
             output_path, '-o', binary_path, '-lSDL2', '-lSDL2_image'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"Ошибка компиляции:\n{result.stderr}")
        else:
            print(f'✓ Собран бинарник: {binary_path}')
    
    return cpp_code


def compile_header(source: str, output_path: str) -> str:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()
    
    gen = CppCodeGen()
    cpp_code = gen.generate_header(ast)
    
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(cpp_code, encoding='utf-8')
    print(f'✓ Сгенерирован {output_path}')
    
    return cpp_code


# ===== CLI =====
if __name__ == '__main__':
    import sys
    
    header_only = '--header' in sys.argv
    build = '--build' in sys.argv
    args = [a for a in sys.argv[1:] if a not in ('--header', '--build')]
    
    if len(args) < 1:
        print("Использование: python -m gamescript.compiler <файл.gs> [выход] [--header] [--build]")
        sys.exit(1)
    
    input_file = args[0]
    output_file = args[1] if len(args) > 1 else None
    
    try:
        cpp = compile_file(input_file, output_file, header_only=header_only, build=build)
        if not output_file:
            print(cpp)
    except (SyntaxError, ValueError, ParseError) as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)