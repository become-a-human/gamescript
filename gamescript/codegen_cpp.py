"""
Генератор C++ кода из AST.

Обходит AST и генерирует валидный C++ код.
Словари → struct, классы → class, методы → функции.
"""

from typing import List, Tuple
from .ast_nodes import *


# Встроенные библиотеки Python → C++ заголовки
BUILTIN_LIBS = {
    'math': '<cmath>',
    'random': '<random>',
    'time': '<chrono>',
    'os': '<filesystem>',
    'sys': '<iostream>',
    'json': '<nlohmann/json.hpp>',
    're': '<regex>',
    'collections': '<map>',
    'runtime': '"runtime.h"',
}


class CodeGenError(Exception):
    """Ошибка генерации кода."""
    pass


class CppCodeGen:
    """
    Генератор C++ кода.
    
    Использование:
        gen = CppCodeGen()
        gen.add_load(load_stmt)  # для каждого @load
        gen.add_grab(grab_stmt)  # для каждого ~grab
        gen.add_link(link_stmt)  # для каждого &link
        cpp_code = gen.generate(ast)
    """
    
    # Отображение GameScript типов в C++ типы
    TYPE_MAP = {
        'int': 'int',
        'float': 'float',
        'str': 'std::string',
        'bool': 'bool',
        'list': 'std::vector',
        'dict': 'std::map<std::string, std::any>',
    }

    def __init__(self):
        self.includes: List[str] = []   # #include "..." и #include <...>
        self.globals: List[str] = []    # struct и inline const
        self.classes: List[str] = []    # class определения
        self._used_std: set = set()     # какие std:: типы используются

    # ===== Добавление импортов =====

    def add_load(self, stmt: LoadStmt):
        stem = stmt.filename.rsplit('.', 1)[0].split('/')[-1]
        
        if stem in BUILTIN_LIBS:
            self.includes.append(f'#include {BUILTIN_LIBS[stem]}')
            if stmt.alias and stem in BUILTIN_LIBS:
                self.includes.append(f'namespace {stmt.alias} = {stem};')
            return
        
        self.includes.append(f'#include "{stem}.h"')
        if stmt.alias and stem in BUILTIN_LIBS:
            self.includes.append(f'namespace {stmt.alias} = {stem};')
        for name, alias in stmt.grabs:
            if alias:
                self.includes.append(f'using {alias} = {name};')

    def add_grab(self, stmt: GrabStmt):
        """
        Добавляет ~grab в вывод.
        ~grab <Hero> like <Player> → using Player = Hero;
        """
        for name, alias in stmt.names:
            if alias:
                self.includes.append(f'using {alias} = {name};')
            else:
                self.includes.append(f'// using {name};')

    def add_link(self, stmt: LinkStmt):
        """
        Добавляет &link в вывод.
        &link <on_create> like <init> → auto& init = on_create;
        """
        for name, alias in stmt.names:
            if alias:
                self.includes.append(f'// &link: {alias} = {name};')
            else:
                self.includes.append(f'// &link: {name};')

    # ===== Главный метод =====

    def generate(self, ast: Program) -> str:
        """Генерирует полный C++ код из AST."""
        for stmt in ast.statements:
            if isinstance(stmt, DictDef):
                self._generate_dict_def(stmt)
            elif isinstance(stmt, ClassDef):
                self._generate_class_def(stmt)
            # Импорты обрабатываются отдельно через add_load/add_grab/add_link
        return self._assemble()

    # ===== Сборка =====

    def _assemble(self) -> str:
        parts = []
        
        # runtime.h всегда первым
        parts.append('#include "runtime.h"')
        parts.append('')
        
        for inc in self.includes:
            parts.append(inc)
        if self.includes:
            parts.append('')
        
        # Стандартные инклюды (только нужные)
        for header in sorted(self._used_std):
            parts.append(f'#include <{header}>')
        if self._used_std:
            parts.append('')
        
        # Глобальные данные
        parts.append('// ========================================')
        parts.append('// ГЛОБАЛЬНЫЕ ДАННЫЕ (сгенерировано GameScript)')
        parts.append('// ========================================')
        parts.append('')
        parts.extend(self.globals)
        
        # Классы
        parts.append('// ========================================')
        parts.append('// КЛАССЫ (сгенерировано GameScript)')
        parts.append('// ========================================')
        parts.append('')
        parts.extend(self.classes)
        
        return '\n'.join(parts)

    # ===== Словари → struct =====
    
    def generate_header(self, ast: Program) -> str:
        """Генерирует только заголовочный файл (.h)."""
        for stmt in ast.statements:
            if isinstance(stmt, DictDef):
                self._generate_dict_def(stmt)
            elif isinstance(stmt, ClassDef):
                self._generate_class_decl(stmt)
        return self._assemble()
    
    def _generate_class_decl(self, node: ClassDef):
        """Только объявление класса (без тел методов)."""
        lines = []
        lines.append(f'class {node.name} : public {node.parent} {{')
        lines.append('public:')
        
        if node.doc:
            lines.append(f'    // {node.doc}')
        
        if node.methods:
            for method in node.methods:
                real_params = [(n, t) for n, t in method.params if n != 'self']
                type_map = {'int': 'int', 'float': 'float', 'str': 'std::string', 'bool': 'bool'}
                params_str = ', '.join(f'{type_map.get(t, t)} {n}' for n, t in real_params)
                lines.append(f'    void {method.name}({params_str});')
        else:
            lines.append(f'    // Пустой класс')
        
        lines.append('};')
        lines.append('')
        self.classes.extend(lines)
    
    def _generate_dict_def(self, node: DictDef):
        """Генерирует C++ struct и inline const экземпляр из DictDef."""
        if not isinstance(node.value, DictLiteral):
            raise CodeGenError(f"DictDef {node.name}: значение должно быть словарём")

        fields = []
        values = []
        for key, val in node.value.pairs:
            cpp_type, cpp_val = self._value_to_cpp(val)
            fields.append(f'    {cpp_type} {key};')
            values.append(f'        .{key} = {cpp_val},')

        struct_name = f'{node.name}_t'
        
        self.globals.append(f'struct {struct_name} {{')
        self.globals.extend(fields)
        self.globals.append('};')
        self.globals.append('')
        self.globals.append(f'const {struct_name} {node.name} = {{')
        self.globals.extend(values)
        self.globals.append('};')
        self.globals.append('')

    # ===== Значения → C++ =====

    def _value_to_cpp(self, node: ASTNode) -> Tuple[str, str]:
        """
        Конвертирует AST-значение в пару (C++ тип, C++ значение-строка).
        """
        if isinstance(node, StringLiteral):
            self._use_std('string')
            return 'std::string', f'"{node.value}"'
        elif isinstance(node, NumberLiteral):
            if isinstance(node.value, float):
                return 'float', f'{node.value}f'
            else:
                return 'int', str(node.value)
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
        """int(100), str("hello"), list(...), dict(...)"""
        if node.typename == 'int':
            return 'int', self._value_to_cpp(node.args[0])[1]
        elif node.typename == 'float':
            val = self._value_to_cpp(node.args[0])[1]
            if not val.endswith('f'):
                val += 'f'
            return 'float', val
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
            self._use_std('map')
            self._use_std('any')
            pairs = []
            for i in range(0, len(node.args), 2):
                k = self._value_to_cpp(node.args[i])[1]
                v = self._value_to_cpp(node.args[i+1])[1]
                pairs.append(f'{{{k}, {v}}}')
            return 'std::map<std::string, std::any>', '{' + ', '.join(pairs) + '}'
        else:
            raise CodeGenError(f"Неизвестный тип: {node.typename}")

    def _inline_dict_to_cpp(self, node: DictLiteral) -> Tuple[str, str]:
        """Вложенный словарь — создаёт анонимную struct на лету."""
        fields = []
        vals = []
        for key, val in node.pairs:
            cpp_type, cpp_val = self._value_to_cpp(val)
            fields.append(f'{cpp_type} {key};')
            vals.append(f'.{key} = {cpp_val}')
        
        fields_str = ' '.join(fields)
        vals_str = ', '.join(vals)
        
        code = (
            f'[](){{\n'
            f'        struct {{ {fields_str} }} tmp{{{vals_str}}};\n'
            f'        return tmp;\n'
            f'    }}()'
        )
        return 'auto', code

    def _use_std(self, header: str):
        """Отмечает, что стандартный заголовок используется."""
        self._used_std.add(header)

    # ===== Классы → C++ class =====

    def _generate_class_def(self, node: ClassDef):
        """Генерирует C++ class из ClassDef с авто-полями."""
        lines = []
        
        # Собираем все поля из self.xxx = ... в методах
        fields = {}
        for method in node.methods:
            for stmt in method.body:
                if isinstance(stmt, Assignment) and stmt.name.startswith('self.'):
                    field_name = stmt.name.replace('self.', '')
                    if field_name not in fields:
                        fields[field_name] = self._infer_type(stmt.value)
                elif isinstance(stmt, CompoundAssignment) and stmt.name.startswith('self.'):
                    field_name = stmt.name.replace('self.', '')
                    if field_name not in fields:
                        fields[field_name] = 'int'
        
        lines.append(f'class {node.name} : public {node.parent} {{')
        lines.append('public:')
        
        if node.doc:
            lines.append(f'    // {node.doc}')
        
        # Генерируем поля
        type_map = {'int': 'int', 'float': 'float', 'str': 'std::string', 'bool': 'bool'}
        for field_name, field_type in fields.items():
            cpp_type = type_map.get(field_type, 'int')
            lines.append(f'    {cpp_type} {field_name};')
        
        if fields:
            lines.append('')
        
        if node.methods:
            for method in node.methods:
                lines.extend(self._generate_method(method))
        else:
            lines.append(f'    // Пустой класс — только данные родителя')
        
        lines.append('};')
        lines.append('')
        self.classes.extend(lines)
    
    def _infer_type(self, value) -> str:
        if isinstance(value, NumberLiteral):
            if isinstance(value.value, float):
                return 'float'
            return 'int'
        elif isinstance(value, StringLiteral):
            return 'str'
        elif isinstance(value, BoolLiteral):
            return 'bool'
        elif isinstance(value, FieldAccess):
            # self.xxx = HERO.name → строка (если поле 'name')
            if value.field in ('name', 'title', 'description'):
                return 'str'
            return 'int'
        return 'int'
    
    def _generate_method(self, method: MethodDef) -> List[str]:
        """Генерирует определение метода."""
        lines = []
        real_params = [(n, t) for n, t in method.params if n != 'self']
        type_map = {'int': 'int', 'float': 'float', 'str': 'std::string', 'bool': 'bool'}
        params_str = ', '.join(f'{type_map.get(t, t)} {n}' for n, t in real_params)
        lines.append(f'    void {method.name}({params_str}) {{')
        
        if method.body:
            for stmt in method.body:
                lines.append(self._generate_statement(stmt, indent=2))
        else:
            lines.append(f'        // (пустое тело)')
        
        lines.append(f'    }}')
        lines.append('')
        return lines

    # ===== Инструкции внутри методов =====

    def _generate_statement(self, stmt, indent: int = 2) -> str:
        """Генерирует одну C++ инструкцию с отступом."""
        pad = '    ' * indent
        
        if stmt is None:
            return f'{pad};'
        
        if isinstance(stmt, Assignment):
            name = stmt.name.replace('self.', 'this->')
            return f'{pad}{name} = {self._expr_to_cpp(stmt.value)};'
        
        elif isinstance(stmt, CompoundAssignment):
            name = stmt.name.replace('self.', 'this->')
            return f'{pad}{name} {stmt.op} {self._expr_to_cpp(stmt.value)};'
        
        elif isinstance(stmt, IfStmt):
            return self._generate_if(stmt, indent)
        
        elif isinstance(stmt, WhileStmt):
            return self._generate_while(stmt, indent)
        
        elif isinstance(stmt, ForStmt):
            return self._generate_for(stmt, indent)
        
        elif isinstance(stmt, ReturnStmt):
            if stmt.value:
                return f'{pad}return {self._expr_to_cpp(stmt.value)};'
            else:
                return f'{pad}return;'
        
        elif isinstance(stmt, ContinueStmt):
            return f'{pad}continue;'
        
        elif isinstance(stmt, BreakStmt):
            return f'{pad}break;'
        
        elif isinstance(stmt, MethodCall):
            obj = self._expr_to_cpp(stmt.obj)
            if obj == 'self':
                obj = 'this'
            args_str = ', '.join(self._expr_to_cpp(a) for a in stmt.args)
            return f'{pad}{obj}->{stmt.method}({args_str});'
        
        elif isinstance(stmt, DictDef):
            return f'{pad}// DictDef: {stmt.name}'
        
        else:
            return f'{pad}// TODO: {type(stmt).__name__}'

    def _generate_if(self, stmt: IfStmt, indent: int = 2) -> str:
        """Генерирует if/else с правильными отступами."""
        pad = '    ' * indent
        cond = self._expr_to_cpp(stmt.condition)
        result = f'{pad}if ({cond}) {{\n'
        for s in stmt.body:
            result += self._generate_statement(s, indent + 1) + '\n'
        result += f'{pad}}}'
        if stmt.else_body:
            result += f' else {{\n'
            for s in stmt.else_body:
                result += self._generate_statement(s, indent + 1) + '\n'
            result += f'{pad}}}'
        return result

    def _generate_while(self, stmt: WhileStmt, indent: int = 2) -> str:
        """Генерирует цикл while."""
        pad = '    ' * indent
        cond = self._expr_to_cpp(stmt.condition)
        result = f'{pad}while ({cond}) {{\n'
        for s in stmt.body:
            result += self._generate_statement(s, indent + 1) + '\n'
        result += f'{pad}}}'
        return result

    def _generate_for(self, stmt: ForStmt, indent: int = 2) -> str:
        """Генерирует цикл for (range-based)."""
        pad = '    ' * indent
        iter_str = self._expr_to_cpp(stmt.iterable)
        result = f'{pad}for (auto& {stmt.var} : {iter_str}) {{\n'
        for s in stmt.body:
            result += self._generate_statement(s, indent + 1) + '\n'
        result += f'{pad}}}'
        return result

    # ===== Выражения → C++ =====

    def _expr_to_cpp(self, expr) -> str:
        """Превращает AST-выражение в C++ строку."""
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
            if obj == 'self':
                return f'this->{expr.field}'
            return f'{obj}.{expr.field}'
        elif isinstance(expr, BinaryOp):
            return f'{self._expr_to_cpp(expr.left)} {expr.op} {self._expr_to_cpp(expr.right)}'
        elif isinstance(expr, MethodCall):
            obj = self._expr_to_cpp(expr.obj)
            if obj == 'self':
                obj = 'this'
            args_str = ', '.join(self._expr_to_cpp(a) for a in expr.args)
            return f'{obj}->{expr.method}({args_str})'
        elif isinstance(expr, TypeCall):
            _, val = self._type_call_to_cpp(expr)
            return val
        elif isinstance(expr, DictLiteral):
            _, val = self._inline_dict_to_cpp(expr)
            return val
        else:
            return f'/* {type(expr).__name__} */'