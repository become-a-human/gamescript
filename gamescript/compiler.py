"""
Главный модуль компилятора GameScript → C++.

Собирает все этапы вместе:
    1. Лексинг (строка → токены)
    2. Парсинг (токены → AST)
    3. Разрешение импортов (@load, ~grab, &link)
    4. Генерация C++ кода
"""

from pathlib import Path
from typing import Optional, Set, List

from .lexer import Lexer
from .parser import Parser, ParseError
from .codegen_cpp import CppCodeGen
from .ast_nodes import (
    Program, DictDef, ClassDef, MethodDef,
    LoadStmt, GrabStmt, LinkStmt, ASTNode
)


# Допустимые расширения файлов GameScript
ALLOWED_EXTENSIONS = {'.gs', '.gscript'}


def compile_text(source: str, output_path: Optional[str] = None,
                 base_path: Optional[Path] = None,
                 already_imported: Optional[Set[str]] = None) -> str:
    """
    Компилирует строку с исходным кодом GameScript в C++.
    
    Args:
        source:           исходный код на GameScript
        output_path:      если указан — сохраняет результат в файл
        base_path:        базовая папка для разрешения импортов
        already_imported: множество уже импортированных файлов (для рекурсии)
    
    Returns:
        строка с валидным C++ кодом
    
    Raises:
        SyntaxError: если исходный код содержит ошибки
    """
    if already_imported is None:
        already_imported = set()
    
    # Этап 1: лексинг
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    
    # Этап 2: парсинг
    parser = Parser(tokens)
    ast = parser.parse()
    
    # Этап 3: разрешение импортов
    ast = resolve_imports(ast, base_path or Path.cwd(), already_imported)
    
    # Этап 4: генерация C++
    gen = CppCodeGen()
    
    # Добавляем импорты в вывод (#include, using, namespace)
    for stmt in ast.statements:
        if isinstance(stmt, LoadStmt):
            gen.add_load(stmt)
        elif isinstance(stmt, GrabStmt):
            gen.add_grab(stmt)
        elif isinstance(stmt, LinkStmt):
            gen.add_link(stmt)
    
    cpp_code = gen.generate(ast)
    
    # Сохраняем если нужно
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
            # @load / @load? — загружает весь файл
            loaded = _handle_load(stmt, base_path, already_imported)
            new_statements.extend(loaded)
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


def _handle_load(stmt: LoadStmt, base_path: Path,
                 already_imported: Set[str]) -> List[ASTNode]:
    """
    Обрабатывает @load / @load?.
    Загружает весь файл и рекурсивно разрешает его импорты.
    """
    # Проверяем, не загружен ли уже этот файл
    if stmt.filename in already_imported:
        return []
    
    # Ищем файл
    filepath = _find_file(stmt.filename, base_path)
    if filepath is None:
        if stmt.optional:
            return []  # @load? — молча пропускаем
        raise ParseError(f"@load: файл не найден: {stmt.filename}", 0, 0)
    
    already_imported.add(stmt.filename)
    
    # Читаем и парсим файл
    source = filepath.read_text(encoding='utf-8')
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    imported_ast = parser.parse()
    
    # Рекурсивно разрешаем импорты внутри файла
    imported_ast = resolve_imports(imported_ast, filepath.parent, already_imported)
    
    return imported_ast.statements


def _handle_grab(stmt: GrabStmt, base_path: Path,
                 already_imported: Set[str]) -> List[ASTNode]:
    """
    Обрабатывает ~grab / ~grab?.
    Захватывает конкретные классы/словари по имени.
    """
    results = []
    
    for name, alias in stmt.names:
        # Ищем в уже загруженных файлах
        found = _find_and_extract_name(name, alias, already_imported, base_path)
        
        # Если не нашли — ищем во всех .gs файлах в base_path
        if found is None:
            for f in base_path.glob("*.gs"):
                if f.name not in already_imported:
                    already_imported.add(f.name)
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
    """
    Обрабатывает &link / &link?.
    Захватывает конкретные функции/методы по имени.
    """
    results = []
    
    for name, alias in stmt.names:
        found = _find_and_extract_function(name, alias, already_imported, base_path)
        
        if found is None:
            for f in base_path.glob("*.gs"):
                if f.name not in already_imported:
                    already_imported.add(f.name)
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


def compile_file(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Компилирует .gs или .gscript файл в C++.
    
    Args:
        input_path:  путь к .gs или .gscript файлу
        output_path: путь для .cpp файла (по умолчанию: input.cpp)
    
    Returns:
        строка с C++ кодом
    
    Raises:
        ValueError: если расширение файла не .gs и не .gscript
    """
    input_file = Path(input_path)
    
    # Проверка расширения
    if input_file.suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"Неверное расширение файла: '{input_file.suffix}'. "
            f"GameScript принимает только {', '.join(ALLOWED_EXTENSIONS)} файлы."
        )
    
    source = input_file.read_text(encoding='utf-8')
    
    if output_path is None:
        output_path = str(input_file.with_suffix('.cpp'))
    
    return compile_text(source, output_path, base_path=input_file.parent)


# ===== CLI =====
if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Использование: python -m gamescript.compiler <файл.gs> [выход.cpp]")
        print(f"  Поддерживаемые расширения: {', '.join(ALLOWED_EXTENSIONS)}")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        cpp = compile_file(input_file, output_file)
        if not output_file:
            print(cpp)
    except (SyntaxError, ValueError, ParseError) as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)