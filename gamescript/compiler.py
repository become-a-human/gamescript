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


def generate_runtime(ast: Program, output_dir: Path):
    """Генерирует runtime.h на основе AST."""
    gen = CppCodeGen()
    runtime_h = gen.generate_runtime(ast)
    (output_dir / 'runtime.h').write_text(runtime_h, encoding='utf-8')


def compile_text(source: str, output_path: Optional[str] = None,
                 base_path: Optional[Path] = None, build: bool = False) -> str:
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
        return compile_header(source, output_path)
    
    # Генерируем runtime.h ДО компиляции главного файла
    all_fields = {}
    all_bases = set()
    lexer = Lexer(source); tokens = lexer.tokenize()
    parser = Parser(tokens); ast = parser.parse()
    for stmt in ast.statements:
        if isinstance(stmt, ClassDef):
            all_bases.add(stmt.parent)
            for method in stmt.methods:
                for s in method.body:
                    if isinstance(s, Assignment) and s.name.startswith('self.'):
                        field = s.name.replace('self.', '')
                        if field not in all_fields:
                            all_fields[field] = _infer_cpp_type(s.value)
        elif isinstance(stmt, LoadStmt):
            dep_path = _find_file(stmt.filename, input_file.parent)
            if dep_path:
                dep_source = dep_path.read_text(encoding='utf-8')
                dep_lexer = Lexer(dep_source); dep_tokens = dep_lexer.tokenize()
                dep_parser = Parser(dep_tokens); dep_ast = dep_parser.parse()
                for ds in dep_ast.statements:
                    if isinstance(ds, ClassDef):
                        all_bases.add(ds.parent)
                        for method in ds.methods:
                            for s in method.body:
                                if isinstance(s, Assignment) and s.name.startswith('self.'):
                                    field = s.name.replace('self.', '')
                                    if field not in all_fields:
                                        all_fields[field] = _infer_cpp_type(s.value)
    gen_runtime = CppCodeGen()
    runtime_h = gen_runtime.generate_runtime_from_data(all_bases, all_fields)
    (output_dir / 'runtime.h').write_text(runtime_h, encoding='utf-8')
    
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


def compile_header(source: str, output_path: str) -> str:
    lexer = Lexer(source); tokens = lexer.tokenize()
    parser = Parser(tokens); ast = parser.parse()
    gen = CppCodeGen()
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
    return None


if __name__ == '__main__':
    import sys
    header_only = '--header' in sys.argv
    build = '--build' in sys.argv
    args = [a for a in sys.argv[1:] if a not in ('--header', '--build')]
    if len(args) < 1:
        print("Использование: python -m gamescript.compiler <файл.gs> [выход] [--header] [--build]")
        sys.exit(1)
    try:
        cpp = compile_file(args[0], args[1] if len(args) > 1 else None, header_only=header_only, build=build)
        if len(args) <= 1: print(cpp)
    except (SyntaxError, ValueError, ParseError) as e:
        print(f"Ошибка: {e}", file=sys.stderr)
        sys.exit(1)