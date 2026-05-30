"""
Главный модуль компилятора GameScript → C++.
"""

import subprocess
from pathlib import Path
from typing import Optional, Set, List

from .lexer import Lexer
from .parser import Parser, ParseError
from .codegen_cpp import CppCodeGen, BUILTIN_LIBS
from .ast_nodes import Program, DictDef, ClassDef, LoadStmt, ASTNode, Assignment, StringLiteral, NumberLiteral, BoolLiteral, FieldAccess, Identifier


ALLOWED_EXTENSIONS = {'.gs', '.gscript'}


def compile_text(source: str, output_path: Optional[str] = None,
                 base_path: Optional[Path] = None, build: bool = False) -> str:
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    ast = parser.parse()

    gen = CppCodeGen(base_path=base_path or Path.cwd())

    for stmt in ast.statements:
        if isinstance(stmt, LoadStmt):
            if not stmt.optional:
                stem = stmt.filename.rsplit('.', 1)[0].split('/')[-1]
                if stem not in BUILTIN_LIBS:
                    filepath = _find_file(stmt.filename, base_path or Path.cwd())
                    if filepath is None:
                        raise ParseError(f"@load: файл не найден: {stmt.filename}", 0, 0)
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


def _infer_cpp_type(value) -> str:
    """Определяет C++ тип значения."""
    if isinstance(value, NumberLiteral):
        return 'float' if isinstance(value.value, float) else 'int'
    elif isinstance(value, StringLiteral):
        return 'str'
    elif isinstance(value, BoolLiteral):
        return 'bool'
    elif isinstance(value, FieldAccess):
        return 'str' if value.field in ('name', 'title', 'description', 'image_path') else 'int'
    elif isinstance(value, Identifier):
        return value.name
    return 'int'


def compile_file(input_path: str, output_path: Optional[str] = None, 
                 header_only: bool = False, build: bool = False) -> str:
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
        return compile_header(source, output_path, base_path=input_file.parent)
    
    cpp_code = compile_text(source, output_path, base_path=input_file.parent, build=build)
    
    if build:
        binary_path = str(Path(output_path).with_suffix(''))
        result = subprocess.run(
            ['g++', '-std=c++17', '-DHAS_SDL2', '-I', str(output_dir), 
             output_path, '-o', binary_path, '-lSDL2', '-lSDL2_image'],
            capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Ошибка компиляции:\n{result.stderr}")
        else:
            print(f'✓ Собран бинарник: {binary_path}')
    
    return cpp_code


def compile_header(source: str, output_path: str, base_path: Path = None) -> str:
    lexer = Lexer(source); tokens = lexer.tokenize()
    parser = Parser(tokens); ast = parser.parse()
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


def _find_file(filename: str, base_path: Path) -> Optional[Path]:
    path = base_path / filename
    if path.exists(): return path
    for ext in ALLOWED_EXTENSIONS:
        path = base_path / (filename + ext)
        if path.exists(): return path
    
    # Дружелюбная ошибка
    tried = [str(base_path / filename)]
    for ext in ALLOWED_EXTENSIONS:
        tried.append(str(base_path / (filename + ext)))
    raise ParseError(
        f"Файл не найден: {filename}",
        0, 0,
        f"Искал:\n  " + "\n  ".join(tried)
    )


def main():
    import sys
    
    if '--version' in sys.argv or '-v' in sys.argv:
        from . import __version__
        print(f"GameScript v{__version__}")
        sys.exit(0)
    
    header_only = '--header' in sys.argv
    build = '--build' in sys.argv
    args = [a for a in sys.argv[1:] if a not in ('--header', '--build', '-o')]
    
    output_name = None
    if '-o' in sys.argv:
        idx = sys.argv.index('-o')
        if idx + 1 < len(sys.argv):
            output_name = sys.argv[idx + 1]
    
    if len(args) < 1:
        print("Использование: python -m gamescript.compiler <файл.gs> [выход] [--header] [--build] [-o name]")
        sys.exit(1)
    
    input_file = args[0]
    output_file = args[1] if len(args) > 1 else None
    
    try:
        cpp = compile_file(input_file, output_file, header_only=header_only, build=build)
        if build and output_name:
            import shutil
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