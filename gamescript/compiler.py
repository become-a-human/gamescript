"""
Главный модуль компилятора GameScript → C++.
"""

import subprocess
import sys
import time
import shutil
from pathlib import Path
from typing import Optional

from .lexer import Lexer
from .parser import Parser, ParseError
from .codegen_cpp import CppCodeGen, BUILTIN_LIBS
from .ast_nodes import (
    Program, DictDef, ClassDef, LoadStmt, ASTNode,
    Assignment, StringLiteral, NumberLiteral, BoolLiteral, FieldAccess, Identifier
)

ALLOWED_EXTENSIONS = {'.gs', '.gscript'}


def compile_text(source: str, output_path: Optional[str] = None,
                 base_path: Optional[Path] = None, build: bool = False,
                 debug: bool = False, short: bool = False) -> str:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    if debug:
        if short:
            _debug_short(tokens, ast)
        else:
            _debug_full(tokens, ast)

    gen = CppCodeGen(base_path=base_path or Path.cwd())

    for stmt in ast.statements:
        if isinstance(stmt, LoadStmt):
            stem = stmt.filename.rsplit('.', 1)[0].split('/')[-1]
            if stem in BUILTIN_LIBS:
                gen.add_load(stmt)  # builtin всегда добавляем
            elif not stmt.optional:
                filepath = _find_file(stmt.filename, base_path or Path.cwd())
                if filepath is None:
                    raise ParseError(f"@load: файл не найден: {stmt.filename}", 0, 0)
                gen.add_load(stmt)
            else:
                # @load? — просто проверяем существование
                filepath = _find_file(stmt.filename, base_path or Path.cwd())
                if filepath is not None:
                    gen.add_load(stmt)

    cpp_code = gen.generate(ast)

    if build:
        cpp_code += '\n' + gen.generate_main(ast)

    if output_path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(cpp_code, encoding='utf-8')
        print(f'✓ Сгенерирован {output_path}')

    return cpp_code


def compile_header(source: str, output_path: str, base_path: Path = None,
                   debug: bool = False, short: bool = False) -> str:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    if debug:
        if short:
            _debug_short(tokens, ast)
        else:
            _debug_full(tokens, ast)

    gen = CppCodeGen()

    for stmt in ast.statements:
        if isinstance(stmt, LoadStmt):
            stem = stmt.filename.rsplit('.', 1)[0].split('/')[-1]
            if stem not in BUILTIN_LIBS:
                filepath = _find_file(stmt.filename, base_path or Path.cwd())
                if filepath is None:
                    raise ParseError(f"@load: файл не найден: {stmt.filename}", 0, 0)
            gen.add_load(stmt)

    cpp_code = gen.generate_header(ast)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(cpp_code, encoding='utf-8')
    print(f'✓ Сгенерирован {output_path}')
    return cpp_code


def _debug_short(tokens, ast):
    print(f"=== DEBUG ===\nТокенов: {len(tokens)}\nИнструкций: {len(ast.statements)}")
    for stmt in ast.statements:
        if isinstance(stmt, ClassDef):
            print(f"  Класс {stmt.name}({stmt.parent or 'нет'}): {len(stmt.methods)} методов")
        elif isinstance(stmt, DictDef):
            print(f"  Словарь {stmt.name}: {len(stmt.value.pairs)} полей")
        elif isinstance(stmt, LoadStmt):
            print(f"  @load {stmt.filename}")
    print()


def _debug_full(tokens, ast):
    print("=== ТОКЕНЫ ===")
    for t in tokens:
        print(f"  {t.type.value:15} {str(t.value):20}")
    print("\n=== AST ===")
    for stmt in ast.statements:
        print(f"  {type(stmt).__name__}: {stmt}")
    print()


def compile_file(input_path: str, output_path: Optional[str] = None,
                 header_only: bool = False, build: bool = False,
                 debug: bool = False, short: bool = False) -> str:
    input_file = Path(input_path)
    if input_file.suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Неверное расширение: '{input_file.suffix}'")
    source = input_file.read_text(encoding='utf-8')
    first_line = source.split('\n')[0].strip()
    if first_line == '# --header':
        header_only = True
    if output_path is None:
        output_path = str(input_file.with_suffix('.h' if header_only else '.cpp'))
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)

    if header_only:
        return compile_header(source, output_path, base_path=input_file.parent, debug=debug, short=short)

    cpp_code = compile_text(source, output_path, base_path=input_file.parent, build=build, debug=debug, short=short)

    if build:
        binary_path = str(Path(output_path).with_suffix(''))
        cmd = ['g++', '-std=c++17', '-I', str(output_dir), output_path]
        
        # Звук
        sound_cpp = Path(__file__).parent.parent / 'runtime' / 'sound.cpp'
        has_sdl_mixer = False
        try:
            result = subprocess.run(['pkg-config', '--exists', 'SDL2_mixer'], capture_output=True)
            has_sdl_mixer = result.returncode == 0
        except:
            pass
        if has_sdl_mixer and sound_cpp.exists():
            cmd.append(str(sound_cpp))
            cmd.extend(['-lSDL2', '-lSDL2_image', '-lSDL2_mixer', '-DHAS_SDL_MIXER'])
        
        # Сеть
        network_cpp = Path(__file__).parent.parent / 'runtime' / 'network.cpp'
        has_curl = False
        try:
            result = subprocess.run(['pkg-config', '--exists', 'libcurl'], capture_output=True)
            has_curl = result.returncode == 0
        except:
            pass
        if has_curl and network_cpp.exists():
            cmd.append(str(network_cpp))
            cmd.append('-lcurl')
        
        # SQLite
        db_cpp = Path(__file__).parent.parent / 'runtime' / 'database.cpp'
        has_sqlite = False
        try:
            result = subprocess.run(['pkg-config', '--exists', 'sqlite3'], capture_output=True)
            has_sqlite = result.returncode == 0
        except:
            pass
        if has_sqlite and db_cpp.exists():
            cmd.append(str(db_cpp))
            cmd.append('-lsqlite3')
        
        # Потоки
        thread_cpp = Path(__file__).parent.parent / 'runtime' / 'thread.cpp'
        if thread_cpp.exists():
            cmd.append(str(thread_cpp))
            cmd.append('-pthread')
        
        cmd.extend(['-o', binary_path])
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Ошибка компиляции:\n{result.stderr}")
        else:
            print(f'✓ Собран бинарник: {binary_path}')
    
    return cpp_code


def _find_file(filename: str, base_path: Path) -> Optional[Path]:
    path = base_path / filename
    if path.exists():
        return path
    for ext in ALLOWED_EXTENSIONS:
        path = base_path / (filename + ext)
        if path.exists():
            return path
    tried = [str(base_path / filename)]
    for ext in ALLOWED_EXTENSIONS:
        tried.append(str(base_path / (filename + ext)))
    raise ParseError(
        f"Файл не найден: {filename}",
        0, 0,
        f"Искал:\n  " + "\n  ".join(tried)
    )


def main():

    if '--version' in sys.argv or '-v' in sys.argv:
        from . import __version__
        print(f"GameScript v{__version__}")
        sys.exit(0)

    if '--help' in sys.argv or '-h' in sys.argv:
        print("GameScript — DSL для геймдева, компилируется в C++")
        print()
        print("Использование:")
        print("  gamescript <файл.gs> [выход] [опции]")
        print()
        print("Опции:")
        print("  --header       Сгенерировать заголовочный файл (.h)")
        print("  --build        Скомпилировать в бинарник")
        print("  -o <имя>       Имя выходного файла")
        print("  --debug        Вывести токены и AST")
        print("  --short        Краткий дебаг (с --debug)")
        print("  --init [папка] Создать новый проект")
        print("  --watch        Следить за файлом и перекомпилировать")
        print("  --version, -v  Версия компилятора")
        print("  --help, -h     Эта справка")
        print()
        print("Примеры:")
        print("  gamescript hero.gs              # вывод в консоль")
        print("  gamescript hero.gs hero.h       # заголовочный файл")
        print("  gamescript __main__.gs --build -o game  # бинарник")
        print("  gamescript --version            # версия")
        print("  gamescript --init               # создать проект")
        print("  gamescript --debug hero.gs      # отладка")
        sys.exit(0)

    debug = '--debug' in sys.argv
    short = '--short' in sys.argv

    if '--init' in sys.argv:
        args = [a for a in sys.argv[1:] if a not in ('--init', '--debug', '--short')]
        project_dir = Path.cwd()
        if args:
            project_dir = Path(args[0])
        project_dir.mkdir(parents=True, exist_ok=True)
        files = {
            'entity.gs': '# --header\nclass Entity:\n    def on_create(self):\n        self.name = ""\n        self.hp = 100\n        self.is_alive = true\n',
            'system.gs': '# --header\nclass System:\n    def on_start(self):\n        pass\n    def on_update(self):\n        pass\n',
            'hero.gs': '# --header\n@load "entity"\n\nHERO = { "name": "Артур", "hp": 100 }\n\nclass Hero(Entity):\n    def on_create(self):\n        self.hp = HERO.hp\n',
            '__main__.gs': '@load "entity"\n@load "system"\n@load "hero"\n\nclass Main(System):\n    def on_start(self):\n        self.gold = 100\n    def on_update(self):\n        self.gold = self.gold + 1\n',
        }
        for name, content in files.items():
            (project_dir / name).write_text(content)
            print(f"✓ Создан {project_dir / name}")
        print(f"Проект создан в {project_dir}")
        sys.exit(0)

    if '--watch' in sys.argv:
        args = [a for a in sys.argv[1:] if a not in ('--watch', '-o', '--debug', '--short')]
        input_file = args[0] if args else '__main__.gs'
        output_file = args[1] if len(args) > 1 else None
        print(f"Наблюдаю за {input_file}...")
        last_mtime = 0
        while True:
            try:
                mtime = Path(input_file).stat().st_mtime
                if mtime > last_mtime:
                    last_mtime = mtime
                    compile_file(input_file, output_file)
            except KeyboardInterrupt:
                print("\nОстановлено")
                break
            time.sleep(1)
        sys.exit(0)

    header_only = '--header' in sys.argv
    build = '--build' in sys.argv
    args = [a for a in sys.argv[1:] if a not in ('--header', '--build', '-o', '--debug', '--short')]

    output_name = None
    if '-o' in sys.argv:
        idx = sys.argv.index('-o')
        if idx + 1 < len(sys.argv):
            output_name = sys.argv[idx + 1]

    if not args:
        print("GameScript — DSL для геймдева")
        print("Использование: gamescript <файл.gs> [опции]")
        print("gamescript --help для справки")
        sys.exit(1)

    input_file = args[0]
    output_file = args[1] if len(args) > 1 else None

    try:
        cpp = compile_file(input_file, output_file, header_only=header_only, build=build, debug=debug, short=short)
        if build and output_name:
            binary_path = str(Path(output_file).with_suffix(''))
            target = str(Path(output_file).parent / output_name)
            shutil.move(binary_path, target)
            print(f'✓ Бинарник переименован в {target}')
        if not output_file:
            print(cpp)
    except (SyntaxError, ValueError, ParseError) as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()