"""
Генератор C++ кода из AST.
"""

from typing import List, Tuple
from pathlib import Path
from .ast_nodes import *


BUILTIN_LIBS = {
    'math': '<cmath>',
    'random': '<random>',
    'os': '<filesystem>',
    'sys': '<iostream>',
    'json': '<nlohmann/json.hpp>',
    're': '<regex>',
    'collections': '<map>',
    'sdl2': '<SDL2/SDL.h>',
    'sdl2_image': '<SDL2/SDL_image.h>',
    'time': '<chrono>',
    'thread': '<thread>',
    'sdl_mixer': '<SDL2/SDL_mixer.h>',
    'curl': '<curl/curl.h>',
    'socket': '<sys/socket.h>',
    'netdb': '<netdb.h>',
    'curl': '<curl/curl.h>',
    'sqlite': '<sqlite3.h>',
}

BUILTIN_FUNCTIONS = {'sqrt', 'sin', 'cos', 'tan', 'abs', 'pow', 'random', 'time', 'delay', 'play_sound', 'play_music', 'stop_music', 'http_get', 'http_post', 'socket_connect', 'socket_send', 'socket_recv', 'db_open', 'db_exec', 'db_close', 'thread_sleep',}


class CodeGenError(Exception):
    pass


class CppCodeGen:
    def __init__(self, base_path: Path = None):
        self.base_path = base_path or Path.cwd()
        self.includes: List[str] = []
        self.globals: List[str] = []
        self.classes: List[str] = []
        self._used_std: set = set()
        self._field_types: dict = {}  # имя_класса -> {имя_поля: тип}
        self._warnings: List[str] = []

    def add_load(self, stmt: LoadStmt):
        stem = stmt.filename.rsplit('.', 1)[0].split('/')[-1]
        if stem in BUILTIN_LIBS:
            if stmt.optional:
                self.includes.append(f'#ifdef HAS_{stem.upper()}')
                self.includes.append(f'#include {BUILTIN_LIBS[stem]}')
                self.includes.append(f'#endif')
            else:
                self.includes.append(f'#include {BUILTIN_LIBS[stem]}')
        else:
            if stmt.optional:
                self.includes.append(f'#ifdef HAS_{stem.upper()}')
                self.includes.append(f'#include "{stem}.h"')
                self.includes.append(f'#endif')
            else:
                self.includes.append(f'#include "{stem}.h"')

    def _load_base_class(self, parent_name: str) -> dict:
        """Загружает поля базового класса из entity.gs или system.gs."""
        base_file = f'{parent_name.lower()}.gs'
        base_path = self.base_path / 'examples' / base_file
        if not base_path.exists():
            return {}
        
        source = base_path.read_text(encoding='utf-8')
        from .lexer import Lexer
        from .parser import Parser
        tokens = Lexer(source).tokenize()
        ast = Parser(tokens).parse()
        
        fields = {}
        for stmt in ast.statements:
            if isinstance(stmt, ClassDef) and stmt.name == parent_name:
                for method in stmt.methods:
                    for s in method.body:
                        if isinstance(s, Assignment) and s.name.startswith('self.'):
                            name = s.name.replace('self.', '')
                            if name not in fields:
                                fields[name] = self._infer_type(s.value, method.params)
        return fields

    def generate(self, ast: Program) -> str:
        for stmt in ast.statements:
            if isinstance(stmt, DictDef):
                self._generate_dict_def(stmt)
            elif isinstance(stmt, ClassDef):
                self._generate_class_def(stmt)
        return self._assemble(is_header=False)

    def generate_main(self, ast: Program) -> str:
        game_class = 'Game'
        for stmt in ast.statements:
            if isinstance(stmt, ClassDef) and stmt.parent == 'System':
                game_class = stmt.name
                break
        
        return f'''
int main() {{
    {game_class} game;
    game.on_start();
    
    bool running = true;
    while (running) {{
        game.on_update();
    }}
    
    return 0;
}}
'''

    def _assemble(self, is_header: bool = True) -> str:
        parts = []
        if is_header:
            parts.append('#pragma once')
            parts.append('')
        for inc in self.includes:
            parts.append(inc)
        if self.includes:
            parts.append('')
        for header in sorted(self._used_std):
            parts.append(f'#include <{header}>')
        if self._used_std:
            parts.append('')
        parts.append('// ========================================')
        parts.append('// ГЛОБАЛЬНЫЕ ДАННЫЕ (сгенерировано GameScript)')
        parts.append('// ========================================')
        parts.append('')
        parts.extend(self.globals)
        parts.append('// ========================================')
        parts.append('// КЛАССЫ (сгенерировано GameScript)')
        parts.append('// ========================================')
        parts.append('')
        parts.extend(self.classes)
        return '\n'.join(parts)

    def generate_header(self, ast: Program) -> str:
        for stmt in ast.statements:
            if isinstance(stmt, DictDef):
                self._generate_dict_def(stmt)
            elif isinstance(stmt, ClassDef):
                self._generate_class_decl(stmt)
        return self._assemble()
    
    def _generate_class(self, node: ClassDef, header_only: bool = False):
        lines = []
        fields = {}
        
        for method in node.methods:
            for stmt in method.body:
                if isinstance(stmt, Assignment) and stmt.name.startswith('self.'):
                    name = stmt.name.replace('self.', '')
                    if name not in fields:
                        fields[name] = self._infer_type(stmt.value, method.params)
                elif isinstance(stmt, CompoundAssignment) and stmt.name.startswith('self.'):
                    name = stmt.name.replace('self.', '')
                    if name not in fields:
                        fields[name] = 'int'
        
        # Загружаем поля из entity.gs / system.gs (но НЕ выводим их)
        parent_field_names = set()
        if node.parent in ('Entity', 'System'):
            base_fields = self._load_base_class(node.parent)
            parent_field_names = set(base_fields.keys())
        elif node.parent:
            parent_fields = self._get_parent_fields(node.parent)
            parent_field_names = set(parent_fields.keys())
        
        # Выводим ТОЛЬКО свои поля (не родительские)
        own_fields = {k: v for k, v in fields.items() if k not in parent_field_names}
        
        if node.parent:
            lines.append(f'class {node.name} : public {node.parent} {{')
        else:
            lines.append(f'class {node.name} {{')
        lines.append('public:')
        if node.doc:
            lines.append(f'    // {node.doc}')
        
        # Все поля для вывода: свои + родительские (родительские только не от Entity/System)
        display_fields = dict(own_fields)
        if node.parent and node.parent not in ('Entity', 'System'):
            for pfield in parent_field_names:
                if pfield not in display_fields:
                    parent_type = parent_fields.get(pfield, 'int')
                    display_fields[pfield] = parent_type
        
        type_map = {'int': 'int', 'float': 'float', 'str': 'std::string', 'bool': 'bool', 'null': 'std::nullptr_t'}
        for fname, ftype in display_fields.items():
            if ftype in type_map:
                cpp_type = type_map[ftype]
            elif ftype.startswith('vector'):
                inner = ftype.replace('vector<', '').replace('>', '')
                cpp_type = f'std::vector<{type_map.get(inner, inner)}>'
            elif ftype == 'map':
                cpp_type = 'std::map<std::string, std::any>'
            else:
                cpp_type = f'{ftype}*'
            lines.append(f'    {cpp_type} {fname};')
        
        if display_fields:
            lines.append('')
        
        for fname, ftype in display_fields.items():
            if ftype == 'str':
                self._used_std.add('string')
            elif ftype.startswith('vector'):
                self._used_std.add('vector')
            elif ftype == 'map':
                self._used_std.add('map')
                self._used_std.add('any')
        
        if node.parent and node.parent not in ('Entity', 'System'):
            if own_fields:
                init_list = [f'{fname}({self._default_value(ftype)})' for fname, ftype in own_fields.items()]
                lines.append(f'    {node.name}() : {", ".join(init_list)} {{}}')
                lines.append('')
        
        if node.methods:
            for method in node.methods:
                if header_only:
                    real_params = [(n, t) for n, t in method.params if n != 'self']
                    params_str = ', '.join(f'{type_map.get(t, t)} {n}' for n, t in real_params)
                    lines.append(f'    void {method.name}({params_str});')
                else:
                    lines.extend(self._generate_method(method))
        else:
            lines.append('    // Пустой класс')
        
        lines.append('};')
        lines.append('')
        self.classes.extend(lines)
    
    def _generate_class_def(self, node: ClassDef):
        self._generate_class(node, header_only=False)
    
    def _generate_class_decl(self, node: ClassDef):
        self._generate_class(node, header_only=True)
    
    def _default_value(self, ftype: str) -> str:
        if ftype == 'int': return '0'
        elif ftype == 'float': return '0.0f'
        elif ftype == 'str': return '""'
        elif ftype == 'bool': return 'false'
        elif ftype == 'null': return 'nullptr'
        elif ftype.startswith('vector'): return ''
        else: return 'nullptr'

    def _generate_dict_def(self, node: DictDef):
        if not isinstance(node.value, DictLiteral):
            raise CodeGenError(f"DictDef {node.name}: значение должно быть словарём")
        fields = []
        values = []
        for key, val in node.value.pairs:
            cpp_type, cpp_val = self._value_to_cpp(val)
            fields.append(f'    {cpp_type} {key};')
            values.append(f'    .{key} = {cpp_val},')
        struct_name = f'{node.name}_t'
        self.globals.append(f'struct {struct_name} {{')
        self.globals.extend(fields)
        self.globals.append('};')
        self.globals.append('')
        self.globals.append(f'const {struct_name} {node.name} = {{')
        self.globals.extend(values)
        self.globals.append('};')
        self.globals.append('')

    def _value_to_cpp(self, node: ASTNode) -> Tuple[str, str]:
        if isinstance(node, StringLiteral):
            self._use_std('string')
            return 'std::string', f'"{node.value}"'
        elif isinstance(node, NumberLiteral):
            return ('float', f'{node.value}f') if isinstance(node.value, float) else ('int', str(node.value))
        elif isinstance(node, BoolLiteral):
            return 'bool', 'true' if node.value else 'false'
        elif isinstance(node, NoneLiteral):
            return 'std::nullptr_t', 'nullptr'
        elif isinstance(node, TypeCall):
            return self._type_call_to_cpp(node)
        elif isinstance(node, DictLiteral):
            return self._inline_dict_to_cpp(node)
        else:
            raise CodeGenError(f"Неизвестный тип значения: {type(node).__name__}")

    def _type_call_to_cpp(self, node: TypeCall) -> Tuple[str, str]:
        if node.typename == 'int':
            return 'int', self._value_to_cpp(node.args[0])[1]
        elif node.typename == 'float':
            val = self._value_to_cpp(node.args[0])[1]
            return 'float', val if val.endswith('f') else val + 'f'
        elif node.typename == 'str':
            self._use_std('string')
            return 'std::string', self._value_to_cpp(node.args[0])[1]
        elif node.typename == 'bool':
            return 'bool', self._value_to_cpp(node.args[0])[1]
        elif node.typename == 'list':
            self._use_std('vector')
            vals = ', '.join(self._value_to_cpp(a)[1] for a in node.args)
            return 'std::vector<std::string>', '{' + vals + '}'
        elif node.typename == 'dict':
            self._use_std('map'); self._use_std('any')
            pairs = []
            for i in range(0, len(node.args), 2):
                pairs.append(f'{{{self._value_to_cpp(node.args[i])[1]}, {self._value_to_cpp(node.args[i+1])[1]}}}')
            return 'std::map<std::string, std::any>', '{' + ', '.join(pairs) + '}'
        else:
            raise CodeGenError(f"Неизвестный тип: {node.typename}")

    def _inline_dict_to_cpp(self, node: DictLiteral) -> Tuple[str, str]:
        fields = []; vals = []
        for key, val in node.pairs:
            cpp_type, cpp_val = self._value_to_cpp(val)
            fields.append(f'{cpp_type} {key};')
            vals.append(f'.{key} = {cpp_val}')
        code = f'[](){{\n        struct {{ {" ".join(fields)} }} tmp{{{", ".join(vals)}}};\n        return tmp;\n    }}()'
        return 'std::map<std::string, std::any>', code

    def _use_std(self, header: str):
        self._used_std.add(header)
    
    def _get_parent_fields(self, parent_name: str) -> dict:
        # Entity и System — базовые классы, их поля не дублируем
        if parent_name in ('Entity', 'System'):
            return {}
        
        # Ищем среди сгенерированных классов
        for class_code in self.classes:
            if class_code.startswith(f'class {parent_name} :'):
                fields = {}
                for line in class_code.split('\n'):
                    line = line.strip()
                    if ';' in line and '(' not in line and '{' not in line and '}' not in line:
                        parts = line.split()
                        if len(parts) == 2 and parts[1].endswith(';'):
                            fields[parts[1][:-1]] = parts[0]
                return fields
        return {}

    def _infer_type(self, value, method_params: List[tuple] = None) -> str:
        if isinstance(value, NumberLiteral):
            return 'float' if isinstance(value.value, float) else 'int'
        elif isinstance(value, StringLiteral):
            return 'str'
        elif isinstance(value, BoolLiteral):
            return 'bool'
        elif isinstance(value, NoneLiteral):
            return 'null'
        elif isinstance(value, TypeCall):
            if value.typename == 'list':
                if value.args:
                    inner = self._infer_type(value.args[0], method_params)
                    return f'vector<{inner}>'
                return 'vector'
            elif value.typename == 'dict':
                return 'map'
            return value.typename
        elif isinstance(value, FieldAccess):
            if value.field in ('name', 'title', 'description', 'image_path', 'sprite_path'):
                return 'str'
            return 'int'
        elif isinstance(value, Identifier):
            # Проверяем, не параметр ли это метода
            if method_params:
                for pname, ptype in method_params:
                    if pname == value.name:
                        return ptype
            return value.name
        elif isinstance(value, BinaryOp):
            return self._infer_type(value.left, method_params)
        elif isinstance(value, FunCall):
            return value.name
        return 'int'

    def _generate_method(self, method: MethodDef) -> List[str]:
        lines = []
        real_params = [(n, t) for n, t in method.params if n != 'self']
        type_map = {'int': 'int', 'float': 'float', 'str': 'std::string', 'bool': 'bool'}
        params_str = ', '.join(f'{type_map.get(t, t)} {n}' for n, t in real_params)
        if method.vararg:
            params_str += f', std::vector<int> {method.vararg}'
        lines.append(f'    void {method.name}({params_str}) {{')
        if method.body:
            for stmt in method.body:
                lines.append(self._generate_statement(stmt, indent=2))
        else:
            lines.append('        // (пустое тело)')
        lines.append('    }')
        lines.append('')
        return lines

    def _generate_statement(self, stmt, indent: int = 2) -> str:
        pad = '    ' * indent
        if stmt is None:
            return f'{pad};'
        if isinstance(stmt, Assignment):
            name = stmt.name.replace('self.', 'this->')
            if isinstance(stmt.value, FileOpen):
                self._used_std.add('fstream')
                return f'{pad}std::fstream {name}("{self._expr_to_cpp(stmt.value.filename)}", std::ios::{stmt.value.mode});'
            return f'{pad}{name} = {self._expr_to_cpp(stmt.value)};'
        elif isinstance(stmt, IfStmt):
            return self._generate_if(stmt, indent)
        elif isinstance(stmt, WhileStmt):
            return self._generate_while(stmt, indent)
        elif isinstance(stmt, ForStmt):
            return self._generate_for(stmt, indent)
        elif isinstance(stmt, ReturnStmt):
            return f'{pad}return {self._expr_to_cpp(stmt.value)};' if stmt.value else f'{pad}return;'
        elif isinstance(stmt, ContinueStmt):
            return f'{pad}continue;'
        elif isinstance(stmt, BreakStmt):
            return f'{pad}break;'
        elif isinstance(stmt, MethodCall):
            obj = self._expr_to_cpp(stmt.obj)
            if obj == 'self': obj = 'this'
            return f'{pad}{obj}->{stmt.method}({", ".join(self._expr_to_cpp(a) for a in stmt.args)});'
        elif isinstance(stmt, FunCall):
            if stmt.name in BUILTIN_FUNCTIONS:
                if stmt.name.startswith('play_') or stmt.name.startswith('stop_'):
                    self._used_std.add('SDL2/SDL_mixer.h')
                return f'{pad}{stmt.name}({", ".join(self._expr_to_cpp(a) for a in stmt.args)});'
        elif isinstance(stmt, DictDef):
            return f'{pad}// DictDef: {stmt.name}'
        elif isinstance(stmt, PrintStmt):
            self._used_std.add('iostream')
            return f'{pad}std::cout << {self._expr_to_cpp(stmt.value)} << std::endl;'
        elif isinstance(stmt, AssertStmt):
            self._used_std.add('cassert')
            return f'{pad}assert({self._expr_to_cpp(stmt.condition)});'
        elif isinstance(stmt, CompoundAssignment):
            name = stmt.name.replace('self.', 'this->')
            if stmt.op == '++':
                return f'{pad}{name}++;'
            elif stmt.op == '--':
                return f'{pad}{name}--;'
            return f'{pad}{name} {stmt.op} {self._expr_to_cpp(stmt.value)};'
        elif isinstance(stmt, UnaryOp):
            if stmt.op in ('++', '--'):
                name = self._expr_to_cpp(stmt.expr).replace('self.', 'this->')
                return f'{pad}{stmt.op}{name};'
            return f'{pad}{stmt.op}{self._expr_to_cpp(stmt.expr)};'
        elif isinstance(stmt, FileOpen):
            self._used_std.add('fstream')
            return f'{pad}std::fstream {stmt.file}("{self._expr_to_cpp(stmt.filename)}", std::ios::{stmt.mode});'
        elif isinstance(stmt, FileRead):
            return f'{pad}std::getline({stmt.file}, {self._expr_to_cpp(stmt.content)});'
        elif isinstance(stmt, FileWrite):
            return f'{pad}{stmt.file} << {self._expr_to_cpp(stmt.content)};'
        elif isinstance(stmt, FileClose):
            return f'{pad}{stmt.file}.close();'
        return f'{pad}// TODO: {type(stmt).__name__}'

    def _generate_if(self, stmt: IfStmt, indent: int = 2) -> str:
        pad = '    ' * indent
        result = f'{pad}if ({self._expr_to_cpp(stmt.condition)}) {{\n'
        for s in stmt.body:
            result += self._generate_statement(s, indent + 1) + '\n'
        result += f'{pad}}}'
        if stmt.else_body:
            # Проверяем, elif ли это (одна инструкция IfStmt)
            if len(stmt.else_body) == 1 and isinstance(stmt.else_body[0], IfStmt):
                result += f' else {self._generate_if(stmt.else_body[0], indent)[len(pad):]}'
            else:
                result += f' else {{\n'
                for s in stmt.else_body:
                    result += self._generate_statement(s, indent + 1) + '\n'
                result += f'{pad}}}'
        return result

    def _generate_while(self, stmt: WhileStmt, indent: int = 2) -> str:
        pad = '    ' * indent
        result = f'{pad}while ({self._expr_to_cpp(stmt.condition)}) {{\n'
        for s in stmt.body:
            result += self._generate_statement(s, indent + 1) + '\n'
        result += f'{pad}}}'
        return result

    def _generate_for(self, stmt: ForStmt, indent: int = 2) -> str:
        pad = '    ' * indent
        result = f'{pad}for (auto& {stmt.var} : {self._expr_to_cpp(stmt.iterable)}) {{\n'
        for s in stmt.body:
            result += self._generate_statement(s, indent + 1) + '\n'
        result += f'{pad}}}'
        return result

    def _expr_to_cpp(self, expr) -> str:
        if isinstance(expr, NumberLiteral):
            return str(expr.value)
        elif isinstance(expr, StringLiteral):
            return f'"{expr.value}"'
        elif isinstance(expr, BoolLiteral):
            return 'true' if expr.value else 'false'
        elif isinstance(expr, Identifier):
            return expr.name
        elif isinstance(expr, FieldAccess):
            obj = self._expr_to_cpp(expr.obj)
            return f'this->{expr.field}' if obj == 'self' else f'{obj}.{expr.field}'
        elif isinstance(expr, MethodCall):
            obj = self._expr_to_cpp(expr.obj)
            if obj == 'self': obj = 'this'
            return f'{obj}->{expr.method}({", ".join(self._expr_to_cpp(a) for a in expr.args)})'
        elif isinstance(expr, FunCall):
            if expr.name in BUILTIN_FUNCTIONS:
                return f'{expr.name}({", ".join(self._expr_to_cpp(a) for a in expr.args)})'
            return f'new {expr.name}({", ".join(self._expr_to_cpp(a) for a in expr.args)})'
        elif isinstance(expr, TypeCall):
            return self._type_call_to_cpp(expr)[1]
        elif isinstance(expr, DictLiteral):
            return self._inline_dict_to_cpp(expr)[1]
        elif isinstance(expr, BinaryOp):
            op_map = {'and': '&&', 'or': '||'}
            op = op_map.get(expr.op, expr.op)
            return f'{self._expr_to_cpp(expr.left)} {op} {self._expr_to_cpp(expr.right)}'
        elif isinstance(expr, UnaryOp):
            if expr.op in ('++', '--'):
                return f'{expr.op}{self._expr_to_cpp(expr.expr)}'
            return f'{expr.op}{self._expr_to_cpp(expr.expr)}'
        elif isinstance(expr, ListLiteral):
            elements = ', '.join(self._expr_to_cpp(e) for e in expr.elements)
            return '{' + elements + '}'
        elif isinstance(expr, NoneLiteral):
            return 'nullptr'
        elif isinstance(expr, LambdaExpr):
            params_str = ', '.join(f'int {n}' for n, t in expr.params)
            body_str = '; '.join(self._generate_statement(s, indent=0).strip() for s in expr.body)
            return f'[&]({params_str}) {{ {body_str} }}'
        return f'/* {type(expr).__name__} */'