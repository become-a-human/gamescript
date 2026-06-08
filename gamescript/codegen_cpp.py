"""
Генератор C++ кода из AST GameScript.

Обходит AST и генерирует валидный C++17 код.
Словари → struct, классы → class, методы → функции.
"""

from typing import List, Tuple, Optional
from pathlib import Path
from .ast_nodes import *


# ===== Конфигурация =====

# Встроенные библиотеки GameScript → C++ заголовки
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
    'sdl2': '<SDL2/SDL.h>',
    'sdl2_image': '<SDL2/SDL_image.h>',
    'sdl_mixer': '<SDL2/SDL_mixer.h>',
    'curl': '<curl/curl.h>',
    'sqlite': '<sqlite3.h>',
    'thread': '<thread>',
    'chrono': '<chrono>',
    'imgui': '<imgui.h>',
    'imgui_impl': '<imgui_impl_sdl2.h>',
    'ncurses': '"gs_ncurses.h"',
}

# Встроенные функции (генерируются как вызов, а не new)
BUILTIN_FUNCTIONS = {
    'sqrt', 'sin', 'cos', 'tan', 'abs', 'pow',
    'random', 'gs_time', 'gs_delay',
    'play_sound', 'play_music', 'stop_music',
    'http_get', 'http_post',
    'socket_connect', 'socket_send', 'socket_recv',
    'db_open', 'db_exec', 'db_close',
    'thread_sleep',
    'str', 'int', 'float', 'bool',
    'ncurses_init', 'ncurses_end', 'ncurses_clear', 'ncurses_refresh',
    'ncurses_getch', 'ncurses_print', 'read_file_lines', 'write_file_lines',
    'chr', 'len', 'range', 'substr', 'ncurses_status',
    'read_file', 'write_file', 'gs_len', 'gs_substr',
}


class CodeGenError(Exception):
    """Ошибка генерации C++ кода."""
    pass


class CppCodeGen:
    """
    Генератор C++ кода из AST.
    
    Использование:
        gen = CppCodeGen()
        gen.add_load(stmt)       # для каждого @load
        cpp = gen.generate(ast)  # генерация .cpp
        h = gen.generate_header(ast)  # генерация .h
    """

    def __init__(self, base_path: Path = None):
        """
        Инициализация генератора кода.
        
        Атрибуты:
            includes:           список #include "..." или <...>
            globals:            глобальные struct и const
            classes:            сгенерированные class определения
            _used_std:          какие стандартные заголовки <...> нужны
            _field_types:       словарь для проверки типов полей
            _warnings:          предупреждения о несоответствии типов
            _local_vars:        отслеживание объявленных локальных переменных
            _optional_modules:  модули, подключённые через @load? (для #ifdef)
            base_path:          базовая папка для поиска .gs файлов
        """
        self.includes: List[str] = []
        self.globals: List[str] = []
        self.classes: List[str] = []
        self._used_std: set = set()
        self._field_types: dict = {}
        self._warnings: List[str] = []
        self._local_vars: set = set()
        self._optional_modules: set = set()
        self.base_path = base_path or Path.cwd()

    # ===== Импорты =====

    def add_load(self, stmt: LoadStmt):
        """
        Добавляет @load в вывод.
        
        @load "file"       → #include "file.h"
        @load? "file"      → #ifdef HAS_FILE / #include "file.h" / #endif
        @load "file" like "X" → #include "file.h" + using X = file;
        @load "file" like "*" → #include "file.h" + using namespace file;
        
        Опциональные модули (@load?) запоминаются для последующей
        генерации #ifdef вокруг вызовов их функций.
        """
        stem = stmt.filename.rsplit('.', 1)[0].split('/')[-1]
    
        # Запоминаем опциональные модули для #ifdef
        if stmt.optional:
            self._optional_modules.add(stem.upper())
    
        if stem in BUILTIN_LIBS:
            header = BUILTIN_LIBS[stem]
            if stmt.optional:
                self.includes.append(f'#ifdef HAS_{stem.upper()}')
                self.includes.append(f'#include {header}')
                self.includes.append(f'#endif')
            else:
                self.includes.append(f'#include {header}')
            if stmt.alias and stmt.alias != '*':
                self.includes.append(f'namespace {stmt.alias} = {stem};')
        else:
            if stmt.optional:
                self.includes.append(f'#ifdef HAS_{stem.upper()}')
                self.includes.append(f'#include "{stem}.h"')
                self.includes.append(f'#endif')
            else:
                self.includes.append(f'#include "{stem}.h"')
            if stmt.alias:
                if stmt.alias == '*':
                    self.includes.append(f'using namespace {stem};')
                else:
                    self.includes.append(f'using {stmt.alias} = {stem};')

    # ===== Главные методы генерации =====

    def generate(self, ast: Program) -> str:
        """Генерирует .cpp файл."""
        for stmt in ast.statements:
            if isinstance(stmt, DictDef):
                self._generate_dict_def(stmt)
            elif isinstance(stmt, ClassDef):
                self._generate_class_def(stmt)
        return self._assemble(is_header=False)

    def generate_header(self, ast: Program) -> str:
        """Генерирует .h файл (только объявления)."""
        for stmt in ast.statements:
            if isinstance(stmt, DictDef):
                self._generate_dict_def(stmt)
            elif isinstance(stmt, ClassDef):
                self._generate_class_decl(stmt)
        return self._assemble(is_header=True)

    def generate_main(self, ast: Program) -> str:
        """Генерирует int main() из первого класса, наследующего System."""
        main_class = None
        for stmt in ast.statements:
            if isinstance(stmt, ClassDef) and stmt.parent == 'System':
                main_class = stmt
                break
            elif isinstance(stmt, ClassDef) and not stmt.parent:
                main_class = stmt
                break

        if not main_class:
            raise CodeGenError("Не найден класс для точки входа")

        self._local_vars = set()

        body_lines = []
        for method in main_class.methods:
            for stmt in method.body:
                line = self._generate_statement(stmt, indent=1)
                line = line.replace('this->', 'main.')
                line = line.replace('return;', 'return 0;')
                body_lines.append(line)

        body = '\n'.join(body_lines)

        return f'''int main() {{
    {main_class.name} main;
{body}
    return 0;
}}'''

    # ===== Сборка =====

    def _assemble(self, is_header: bool = True) -> str:
        """Собирает все части в один файл."""
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

        if self.globals:
            parts.append('// ========================================')
            parts.append('// ГЛОБАЛЬНЫЕ ДАННЫЕ (сгенерировано GameScript)')
            parts.append('// ========================================')
            parts.append('')
            parts.extend(self.globals)

        if self.classes:
            parts.append('// ========================================')
            parts.append('// КЛАССЫ (сгенерировано GameScript)')
            parts.append('// ========================================')
            parts.append('')
            parts.extend(self.classes)

        return '\n'.join(parts)

    # ===== Словари → struct =====

    def _generate_dict_def(self, node: DictDef):
        """Генерирует C++ struct и const экземпляр из DictDef."""
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
            return 'int', str(node.value)

        elif isinstance(node, BoolLiteral):
            return 'bool', 'true' if node.value else 'false'

        elif isinstance(node, NoneLiteral):
            return 'std::nullptr_t', 'nullptr'

        elif isinstance(node, TypeCall):
            return self._type_call_to_cpp(node)

        elif isinstance(node, DictLiteral):
            return self._inline_dict_to_cpp(node)

        elif isinstance(node, ListLiteral):
            self._use_std('vector')
            if node.elements:
                first_type, _ = self._value_to_cpp(node.elements[0])
                elements = ', '.join(self._value_to_cpp(e)[1] for e in node.elements)
                return f'std::vector<{first_type}>', '{' + elements + '}'
            return 'std::vector<std::string>', '{}'

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
        """Вложенный словарь — создаёт анонимную struct."""
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
        return 'std::map<std::string, std::any>', code

    def _use_std(self, header: str):
        """Отмечает, что стандартный заголовок используется."""
        self._used_std.add(header)

    # ===== Классы → C++ class =====

    def _generate_class_def(self, node: ClassDef):
        """Генерирует C++ class с полями и методами."""
        self._generate_class(node, header_only=False)

    def _generate_class_decl(self, node: ClassDef):
        """Генерирует объявление класса (для .h файла)."""
        self._generate_class(node, header_only=True)

    def _generate_class(self, node: ClassDef, header_only: bool = False):
        """Общая логика генерации класса."""
        lines = []
        fields = {}

        # Собираем поля из self.xxx = ... в методах
        for method in node.methods:
            self._collect_fields(method.body, fields, method.params)

        # Загружаем поля родителя (кроме Entity/System — они в runtime)
        parent_field_names = set()
        if node.parent in ('Entity', 'System'):
            base_fields = self._load_base_class(node.parent)
            parent_field_names = set(base_fields.keys())
        elif node.parent:
            parent_fields = self._get_parent_fields(node.parent)
            parent_field_names = set(parent_fields.keys())

        # Только свои поля
        own_fields = {k: v for k, v in fields.items() if k not in parent_field_names}

        # Объявление класса
        if node.parent:
            lines.append(f'class {node.name} : public {node.parent} {{')
        else:
            lines.append(f'class {node.name} {{')
        lines.append('public:')

        if node.doc:
            lines.append(f'    // {node.doc}')

        # Поля
        type_map = {
            'int': 'int', 'float': 'float', 'str': 'std::string',
            'bool': 'bool', 'null': 'std::nullptr_t',
        }
        for fname, ftype in own_fields.items():
            if ftype in type_map:
                cpp_type = type_map[ftype]
            elif ftype.startswith('vector'):
                inner = ftype.replace('vector<', '').replace('>', '')
                cpp_type = f'std::vector<{type_map.get(inner, inner)}>'
            elif ftype == 'map':
                cpp_type = 'std::map<std::string, std::any>'
            else:
                cpp_type = ftype
            lines.append(f'    {cpp_type} {fname};')

        if own_fields:
            lines.append('')

        # Отмечаем используемые std-типы
        for fname, ftype in own_fields.items():
            if ftype == 'str':
                self._used_std.add('string')
            elif ftype.startswith('vector'):
                self._used_std.add('vector')
            elif ftype == 'map':
                self._used_std.add('map')
                self._used_std.add('any')

        # Конструктор (только для не-Entity)
        if node.parent != 'Entity' and own_fields:
            init_list = []
            for fname, ftype in own_fields.items():
                if ftype in type_map:
                    init_list.append(f'{fname}({self._default_value(ftype)})')
                else:
                    init_list.append(f'{fname}()')  # Hero(), Enemy()
            lines.append(f'    {node.name}() : {", ".join(init_list)} {{}}')
            lines.append('')

        # Методы (всегда с телами — inline в .h и реализация в .cpp)
        if node.methods:
            for method in node.methods:
                lines.extend(self._generate_method(method))
        else:
            lines.append('    // Пустой класс')

        lines.append('};')
        lines.append('')
        self.classes.extend(lines)

    # ===== Методы =====

    def _generate_method(self, method: MethodDef) -> List[str]:
        """Генерирует определение метода."""
        self._local_vars = set()  # сбрасываем для нового метода
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

    # ===== Инструкции =====

    def _get_module_for_function(self, name: str) -> Optional[str]:
        """
        Возвращает имя модуля (для #ifdef HAS_...) по имени встроенной функции.
        
        Используется чтобы обернуть вызовы функций из опциональных модулей
        в #ifdef, чтобы код компилировался даже без установленной библиотеки.
        
        Например:
            play_sound → SDL_MIXER    (#ifdef HAS_SDL_MIXER)
            http_get  → CURL          (#ifdef HAS_CURL)
            db_open   → SQLITE        (#ifdef HAS_SQLITE)
        """
        mapping = {
            # Звук (SDL_mixer)
            'play_sound': 'SDL_MIXER',
            'play_music': 'SDL_MIXER',
            'stop_music': 'SDL_MIXER',
            # Сеть (curl)
            'http_get': 'CURL',
            'http_post': 'CURL',
            'socket_connect': 'CURL',
            'socket_send': 'CURL',
            'socket_recv': 'CURL',
            # База данных (SQLite)
            'db_open': 'SQLITE',
            'db_exec': 'SQLITE',
            'db_close': 'SQLITE',
            # Потоки
            'thread_sleep': 'THREAD',
        }
        return mapping.get(name, None)

    def _generate_statement(self, stmt, indent: int = 2) -> str:
        """Генерирует одну C++ инструкцию с правильным отступом."""
        pad = '    ' * indent

        if stmt is None:
            return f'{pad};'

        # Присваивание
        if isinstance(stmt, Assignment):
            name = stmt.name.replace('self.', 'this->')
            if not stmt.name.startswith('self.') and stmt.name not in self._local_vars:
                self._local_vars.add(stmt.name)
                cpp_type = self._infer_type(stmt.value)
                type_map = {'int': 'int', 'float': 'float', 'str': 'std::string', 'bool': 'bool'}
                cpp_type = type_map.get(cpp_type, 'auto')
                return f'{pad}{cpp_type} {name} = {self._expr_to_cpp(stmt.value)};'
            if isinstance(stmt.value, FileOpen):
                self._used_std.add('fstream')
                return f'{pad}std::fstream {name}("{self._expr_to_cpp(stmt.value.filename)}", std::ios::{stmt.value.mode});'
            return f'{pad}{name} = {self._expr_to_cpp(stmt.value)};'

        # Составное присваивание
        elif isinstance(stmt, CompoundAssignment):
            name = stmt.name.replace('self.', 'this->')
            if stmt.op == '++':
                return f'{pad}{name}++;'
            elif stmt.op == '--':
                return f'{pad}{name}--;'
            return f'{pad}{name} {stmt.op} {self._expr_to_cpp(stmt.value)};'

        # Условный оператор
        elif isinstance(stmt, IfStmt):
            return self._generate_if(stmt, indent)

        # Циклы
        elif isinstance(stmt, WhileStmt):
            return self._generate_while(stmt, indent)
        elif isinstance(stmt, ForStmt):
            return self._generate_for(stmt, indent)

        # Возврат
        elif isinstance(stmt, ReturnStmt):
            if stmt.value:
                return f'{pad}return {self._expr_to_cpp(stmt.value)};'
            return f'{pad}return;'

        # continue / break
        elif isinstance(stmt, ContinueStmt):
            return f'{pad}continue;'
        elif isinstance(stmt, BreakStmt):
            return f'{pad}break;'

        # Вызов метода
        elif isinstance(stmt, MethodCall):
            obj = self._expr_to_cpp(stmt.obj)
            if obj == 'self':
                obj = 'this'
            return f'{pad}{obj}.{stmt.method}({", ".join(self._expr_to_cpp(a) for a in stmt.args)});'

        # Вызов функции или конструктора
        elif isinstance(stmt, FunCall):
            if stmt.name in BUILTIN_FUNCTIONS:
                # Встроенные функции: sqrt, sin, random, play_sound, ...
                args_str = ', '.join(self._expr_to_cpp(a) for a in stmt.args)
        
                # Конвертация типов: str(), int(), float(), bool()
                if stmt.name == 'str':
                    self._use_std('string')
                    return f'{pad}std::to_string({args_str});'
                elif stmt.name == 'int':
                    return f'{pad}static_cast<int>({args_str});'
                elif stmt.name == 'float':
                    return f'{pad}static_cast<float>({args_str});'
                elif stmt.name == 'bool':
                    return f'{pad}static_cast<bool>({args_str});'
        
                # Опциональные модули (@load?): оборачиваем вызов в #ifdef
                # Например: @load? "sdl_mixer" → play_sound() под #ifdef HAS_SDL_MIXER
                module = self._get_module_for_function(stmt.name)
                if module and module in self._optional_modules:
                    return (
                        f'{pad}#ifdef HAS_{module}\n'
                        f'{pad}{stmt.name}({args_str});\n'
                        f'{pad}#endif'
                    )
        
                # Обычная встроенная функция (sqrt, random, ...)
                return f'{pad}{stmt.name}({args_str});'
        
            # Создание объекта: Hero(), Enemy("гоблин")
            # Генерируем объект на стеке (не указатель)
            var_name = stmt.name.lower()
            args_str = ', '.join(self._expr_to_cpp(a) for a in stmt.args)
            if args_str:
                return f'{pad}{stmt.name} {var_name}({args_str});'
            return f'{pad}{stmt.name} {var_name};'

        # Унарные операции
        elif isinstance(stmt, UnaryOp):
            if stmt.op in ('++', '--'):
                name = self._expr_to_cpp(stmt.expr).replace('self.', 'this->')
                return f'{pad}{stmt.op}{name};'
            return f'{pad}{stmt.op}{self._expr_to_cpp(stmt.expr)};'

        # print
        elif isinstance(stmt, PrintStmt):
            self._use_std('iostream')
            return f'{pad}std::cout << {self._expr_to_cpp(stmt.value)} << std::endl;'

        # assert
        elif isinstance(stmt, AssertStmt):
            self._use_std('cassert')
            return f'{pad}assert({self._expr_to_cpp(stmt.condition)});'

        # Файловые операции
        elif isinstance(stmt, FileWrite):
            return f'{pad}{self._expr_to_cpp(stmt.file)} << {self._expr_to_cpp(stmt.content)};'
        elif isinstance(stmt, FileClose):
            return f'{pad}{self._expr_to_cpp(stmt.file)}.close();'

        # Словарь (внутри метода)
        elif isinstance(stmt, DictDef):
            return f'{pad}// DictDef: {stmt.name}'

        return f'{pad}// TODO: {type(stmt).__name__}'

    def _collect_fields(self, stmts, fields, method_params=None):
        """Рекурсивно собирает поля из self.xxx = ..."""
        for stmt in stmts:
            if isinstance(stmt, Assignment) and stmt.name.startswith('self.'):
                name = stmt.name[5:]  # убираем 'self.'
                if '.' in name:
                    continue  # self.hero.x — доступ к объекту, не поле
                if name not in fields:
                    fields[name] = self._infer_type(stmt.value, method_params)
            elif isinstance(stmt, CompoundAssignment) and stmt.name.startswith('self.'):
                name = stmt.name.replace('self.', '')
                if name not in fields:
                    fields[name] = 'int'
            elif isinstance(stmt, IfStmt):
                self._collect_fields(stmt.body, fields, method_params)
                if stmt.else_body:
                    self._collect_fields(stmt.else_body, fields, method_params)
            elif isinstance(stmt, WhileStmt):
                self._collect_fields(stmt.body, fields, method_params)
            elif isinstance(stmt, ForStmt):
                self._collect_fields(stmt.body, fields, method_params)
        return fields

    # ===== Управляющие конструкции =====

    def _generate_if(self, stmt: IfStmt, indent: int = 2) -> str:
        """Генерирует if / else if / else с правильными отступами."""
        pad = '    ' * indent
        result = f'{pad}if ({self._expr_to_cpp(stmt.condition)}) {{\n'
        for s in stmt.body:
            result += self._generate_statement(s, indent + 1) + '\n'
        result += f'{pad}}}'

        if stmt.else_body:
            if len(stmt.else_body) == 1 and isinstance(stmt.else_body[0], IfStmt):
                # elif → else if
                result += f' else {self._generate_if(stmt.else_body[0], indent)[len(pad):]}'
            else:
                result += f' else {{\n'
                for s in stmt.else_body:
                    result += self._generate_statement(s, indent + 1) + '\n'
                result += f'{pad}}}'
    
        return result

    def _generate_while(self, stmt: WhileStmt, indent: int = 2) -> str:
        """Генерирует цикл while."""
        pad = '    ' * indent
        result = f'{pad}while ({self._expr_to_cpp(stmt.condition)}) {{\n'
        for s in stmt.body:
            result += self._generate_statement(s, indent + 1) + '\n'
        result += f'{pad}}}'
        return result

    def _generate_for(self, stmt: ForStmt, indent: int = 2) -> str:
        """Генерирует range-based цикл for."""
        pad = '    ' * indent
        result = f'{pad}for (auto& {stmt.var} : {self._expr_to_cpp(stmt.iterable)}) {{\n'
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

        elif isinstance(expr, NoneLiteral):
            return 'nullptr'

        elif isinstance(expr, Identifier):
            return expr.name

        elif isinstance(expr, FieldAccess):
            obj = self._expr_to_cpp(expr.obj)
            if obj == 'self':
                return f'this->{expr.field}'
            return f'{obj}.{expr.field}'

        elif isinstance(expr, BinaryOp):
            op_map = {'and': '&&', 'or': '||'}
            op = op_map.get(expr.op, expr.op)
            return f'{self._expr_to_cpp(expr.left)} {op} {self._expr_to_cpp(expr.right)}'

        elif isinstance(expr, UnaryOp):
            if expr.op in ('++', '--'):
                return f'{expr.op}{self._expr_to_cpp(expr.expr)}'
            return f'{expr.op}{self._expr_to_cpp(expr.expr)}'

        elif isinstance(expr, MethodCall):
            obj = self._expr_to_cpp(expr.obj)
            if obj == 'self':
                obj = 'this'
            return f'{obj}.{expr.method}({", ".join(self._expr_to_cpp(a) for a in expr.args)})'

        elif isinstance(expr, FunCall):
            if expr.name in BUILTIN_FUNCTIONS:
                args_str = ', '.join(self._expr_to_cpp(a) for a in expr.args)
                if expr.name == 'str':
                    self._use_std('string')
                    return f'std::to_string({args_str})'
                elif expr.name == 'int':
                    return f'static_cast<int>({args_str})'
                elif expr.name == 'float':
                    return f'static_cast<float>({args_str})'
                elif expr.name == 'bool':
                    return f'static_cast<bool>({args_str})'
                return f'{expr.name}({args_str})'
            return f'{expr.name}({", ".join(self._expr_to_cpp(a) for a in expr.args)})'

        elif isinstance(expr, LambdaExpr):
            params_str = ', '.join(f'int {n}' for n, t in expr.params)
            if len(expr.body) == 1 and isinstance(expr.body[0], (ReturnStmt, Assignment)):
                body_str = self._generate_statement(expr.body[0], indent=0).strip().rstrip(';')
            else:
                body_str = '; '.join(
                    self._generate_statement(s, indent=0).strip()
                    for s in expr.body
                )
            return f'[&]({params_str}) {{ {body_str} }}'

        elif isinstance(expr, TypeCall):
            return self._type_call_to_cpp(expr)[1]

        elif isinstance(expr, DictLiteral):
            return self._inline_dict_to_cpp(expr)[1]

        elif isinstance(expr, ListLiteral):
            elements = ', '.join(self._expr_to_cpp(e) for e in expr.elements)
            return '{' + elements + '}'

        elif isinstance(expr, FileOpen):
            self._use_std('fstream')
            return f'std::fstream("{self._expr_to_cpp(expr.filename)}", std::ios::{expr.mode})'

        elif isinstance(expr, FileRead):
            return f'std::getline({self._expr_to_cpp(expr.file)})'

        return f'/* {type(expr).__name__} */'

    # ===== Вывод типов =====

    def _infer_type(self, value, method_params: List[tuple] = None) -> str:
        """
        Определяет тип значения для авто-полей класса.
        Используется при генерации полей из self.xxx = ... в методах.
        """
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
            return value.name  # Имя класса

        elif isinstance(value, BinaryOp):
            return self._infer_type(value.left, method_params)

        elif isinstance(value, ListLiteral):
            if value.elements:
                inner = self._infer_type(value.elements[0], method_params)
                return f'vector<{inner}>'
            return 'vector'

        elif isinstance(value, FunCall):
            if value.name in BUILTIN_FUNCTIONS:
                return 'float'
            return value.name

        return 'int'

    # ===== Вспомогательные методы =====

    def _default_value(self, ftype: str) -> str:
        """Возвращает значение по умолчанию для типа."""
        if ftype == 'int':
            return '0'
        elif ftype == 'float':
            return '0.0f'
        elif ftype == 'str':
            return '""'
        elif ftype == 'bool':
            return 'false'
        elif ftype == 'null':
            return 'nullptr'
        elif ftype.startswith('vector'):
            return ''
        else:
            return 'nullptr'

    def _load_base_class(self, parent_name: str) -> dict:
        """
        Загружает поля базового класса из entity.gs или system.gs.
        Используется при наследовании от Entity/System.
        """
        base_file = f'{parent_name.lower()}.gs'
        base_path = self.base_path / base_file
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

    def _get_parent_fields(self, parent_name: str) -> dict:
        """
        Возвращает поля родительского класса (не Entity/System).
        Ищет среди уже сгенерированных классов.
        """
        if parent_name in ('Entity', 'System'):
            return {}

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