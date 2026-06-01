"""
Тесты компилятора GameScript.

Проверяют полный цикл: исходный код → C++ код.
"""

import tempfile
from pathlib import Path
from gamescript.compiler import compile_text, compile_header
from gamescript.parser import ParseError


def tokenize(source):
    """Вспомогательная функция (для совместимости)."""
    from gamescript.lexer import Lexer
    return Lexer(source).tokenize()


# ===== Базовая компиляция =====

def test_simple_compile():
    """Простой словарь → struct."""
    source = 'HERO = { "hp": 100 }'
    cpp = compile_text(source)
    assert "struct HERO_t" in cpp
    assert "const HERO_t HERO" in cpp
    assert "int hp;" in cpp


def test_compile_header():
    """Генерация .h файла."""
    cpp = compile_header(
        'HERO = { "hp": 100 }\nclass Hero(Entity):\n    def on_create(self):\n        self.hp = 100',
        "/dev/null"
    )
    assert "struct HERO_t" in cpp
    assert "void on_create()" in cpp


def test_compile_pragma_once():
    """#pragma once в .h файлах."""
    cpp = compile_header('HERO = { "hp": 100 }', "/dev/null")
    assert '#pragma once' in cpp


# ===== Импорты =====

def test_compile_with_load():
    """@load → #include."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "sword.gs").write_text('SWORD = { "attack": 8 }', encoding='utf-8')
        cpp = compile_text('@load "sword.gs"\nHERO = { "hp": 100 }', base_path=base)
        assert '#include "sword.h"' in cpp
        assert "struct HERO_t" in cpp
        assert "SWORD_t" not in cpp  # не встраивается


def test_compile_with_optional_missing():
    """@load? не падает если файла нет."""
    cpp = compile_text('@load? "nonexistent.gs"\nHERO = { "hp": 100 }')
    assert "struct HERO_t" in cpp


def test_compile_with_optional_present():
    """@load? работает если файл есть."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "plugin.gs").write_text('PLUGIN_DATA = { "enabled": true }', encoding='utf-8')
        cpp = compile_text('@load? "plugin.gs"', base_path=base)
        assert '#include "plugin.h"' in cpp
        assert "PLUGIN_DATA_t" not in cpp


def test_compile_error_on_missing_required():
    """@load без ? падает если файла нет."""
    try:
        compile_text('@load "nonexistent.gs"')
        assert False, "Должна быть ошибка"
    except ParseError:
        pass


def test_compile_load_like():
    """@load like → using."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "hero.gs").write_text('HERO = { "hp": 100 }', encoding='utf-8')
        cpp = compile_text('@load "hero" like "Player"', base_path=base)
        assert '#include "hero.h"' in cpp
        assert "using Player = hero;" in cpp


def test_compile_load_like_star():
    """@load like * → using namespace."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "hero.gs").write_text('HERO = { "hp": 100 }', encoding='utf-8')
        cpp = compile_text('@load "hero" like "*"', base_path=base)
        assert '#include "hero.h"' in cpp
        assert "using namespace hero;" in cpp


# ===== Присваивания =====

def test_compile_compound_assignment():
    """+= и -=."""
    cpp = compile_text(
        'class Hero(Entity):\n    def on_turn(self):\n        self.hp += 10\n        self.mp -= 5'
    )
    assert "this->hp += 10;" in cpp
    assert "this->mp -= 5;" in cpp


def test_compile_increment():
    """++."""
    cpp = compile_text('class Hero(Entity):\n    def tick(self):\n        self.hp++')
    assert 'this->hp++;' in cpp


def test_compile_decrement():
    """--."""
    cpp = compile_text('class Hero(Entity):\n    def tick(self):\n        self.hp--')
    assert 'this->hp--;' in cpp


def test_compile_modulo():
    cpp = compile_text('class Hero(Entity):\n    def tick(self):\n        self.frame = self.frame % 10')
    assert '%' in cpp


def test_compile_xor():
    cpp = compile_text('class Hero(Entity):\n    def flip(self):\n        self.flags = self.flags ^ 1')
    assert '^' in cpp


# ===== Управляющие конструкции =====

def test_compile_comparison():
    """< и >="""
    cpp = compile_text(
        'class Enemy(Entity):\n    def on_turn(self):\n'
        '        if self.hp < 0:\n            self.is_alive = false\n'
        '        if self.hp >= 100:\n            self.is_alive = true'
    )
    assert "this->hp < 0" in cpp
    assert "this->hp >= 100" in cpp


def test_compile_while():
    """while."""
    cpp = compile_text(
        'class Hero(Entity):\n    def rest(self):\n'
        '        while self.hp < self.max_hp:\n            self.hp = self.hp + 1'
    )
    assert "while" in cpp


def test_compile_for():
    """for."""
    cpp = compile_text(
        'class Hero(Entity):\n    def use_all(self, items):\n        for i in items:\n            self:use(i)'
    )
    assert "for (auto& i : items)" in cpp


def test_compile_elif():
    """elif → else if."""
    cpp = compile_text('''class Hero(Entity):
    def check(self):
        if self.hp > 50:
            self.status = "good"
        elif self.hp > 20:
            self.status = "ok"
        else:
            self.status = "bad"''')
    assert 'else if (this->hp > 20)' in cpp


def test_compile_not():
    """not → !"""
    cpp = compile_text(
        'class Hero(Entity):\n    def check(self):\n        if not self.is_alive:\n            self.hp = 0'
    )
    assert '!this->is_alive' in cpp


def test_compile_logical_operators():
    """and/or → &&/||."""
    cpp = compile_text('''class Hero(Entity):
    def check(self):
        if self.hp > 0 and self.mp > 0:
            self.is_alive = true''')
    assert '&&' in cpp


# ===== Типы =====

def test_compile_typed_parameters():
    """Типизированные параметры."""
    cpp = compile_text(
        'class Hero(Entity):\n    def set_name(self, name: str, age: int):\n        self.name = name'
    )
    assert "std::string name" in cpp
    assert "int age" in cpp


def test_compile_null_check():
    """None → nullptr."""
    cpp = compile_text('''class Hero(Entity):
    def check(self):
        if self.target != None:
            self.hp = 100''')
    assert 'this->target != nullptr' in cpp


# ===== Функции =====

def test_compile_method_call():
    """Вызов метода через ':'."""
    cpp = compile_text('class Hero(Entity):\n    def on_start(self):\n        self:heal(10)')
    assert "this->heal(10);" in cpp


def test_compile_constructor():
    """new ClassName()."""
    cpp = compile_text(
        'class Hero(Entity):\n    def create(self):\n        self.hero = Hero("Артур", 100)'
    )
    assert 'new Hero("Артур", 100)' in cpp


def test_compile_constructor_no_args():
    """new ClassName() без аргументов."""
    cpp = compile_text('class Hero(Entity):\n    def create(self):\n        self.hero = Hero()')
    assert 'new Hero()' in cpp


def test_compile_print():
    """print → std::cout."""
    cpp = compile_text('''class Hero(Entity):
    def debug(self):
        print(self.hp)''')
    assert 'std::cout' in cpp
    assert 'std::endl' in cpp


def test_compile_assert():
    """assert → assert()."""
    cpp = compile_text('''class Hero(Entity):
    def check(self):
        assert self.hp >= 0''')
    assert 'assert(' in cpp


def test_compile_lambda():
    """Лямбда."""
    cpp = compile_text('class Hero(Entity):\n    def setup(self):\n        self.callback = fn(): 42')
    assert '[&]' in cpp


# ===== Файлы =====

def test_compile_file_operations():
    """open/write/close."""
    cpp = compile_text('''class Hero(Entity):
    def save(self):
        f = open("save.txt", "out")
        write(f, self.name)
        close(f)''')
    assert 'std::fstream' in cpp
    assert 'std::ios::out' in cpp


# ===== Списки =====

def test_compile_list_literal():
    """[1, 2, 3] → {1, 2, 3}."""
    cpp = compile_text('class Hero(Entity):\n    def init(self):\n        self.items = [1, 2, 3]')
    assert '{1, 2, 3}' in cpp


# ===== Структуры =====

def test_compile_struct_formatting():
    """Отступы в struct."""
    cpp = compile_text('HERO = { "hp": 100, "mp": 50 }')
    assert '    int hp;\n    int mp;' in cpp or '    int hp;' in cpp


def test_compile_class_without_parent():
    """Класс без родителя."""
    cpp = compile_text('''class Entity:
    def on_create(self):
        self.hp = 100''')
    assert 'class Entity {' in cpp
    assert ': public' not in cpp.split('class Entity')[1].split('{')[0]


# ===== Комплексные тесты =====

def test_compile_full_game_example():
    """Полный пример с @load."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "hero.gs").write_text(
            'HERO = { "hp": 100, "name": "Артур" }\nclass Hero(Entity): pass',
            encoding='utf-8'
        )
        (base / "weapons.gs").write_text('SWORD = { "attack": 8 }', encoding='utf-8')
        cpp = compile_text(
            '@load "hero.gs"\n@load "weapons.gs"\nGAME_CONFIG = { "title": "Test" }',
            base_path=base
        )
        assert '#include "hero.h"' in cpp
        assert '#include "weapons.h"' in cpp
        assert "struct GAME_CONFIG_t" in cpp
        assert "HERO_t" not in cpp
        assert "SWORD_t" not in cpp


def test_file_not_found_error():
    """Дружелюбная ошибка при отсутствии файла."""
    try:
        compile_text('@load "nonexistent_file_12345"')
        assert False
    except ParseError as e:
        assert "не найден" in str(e)


if __name__ == "__main__":
    # Базовая компиляция
    test_simple_compile()
    test_compile_header()
    test_compile_pragma_once()
    # Импорты
    test_compile_with_load()
    test_compile_with_optional_missing()
    test_compile_with_optional_present()
    test_compile_error_on_missing_required()
    test_compile_load_like()
    test_compile_load_like_star()
    # Присваивания
    test_compile_compound_assignment()
    test_compile_increment()
    test_compile_decrement()
    test_compile_modulo()
    test_compile_xor()
    # Управляющие конструкции
    test_compile_comparison()
    test_compile_while()
    test_compile_for()
    test_compile_elif()
    test_compile_not()
    test_compile_logical_operators()
    # Типы
    test_compile_typed_parameters()
    test_compile_null_check()
    # Функции
    test_compile_method_call()
    test_compile_constructor()
    test_compile_constructor_no_args()
    test_compile_print()
    test_compile_assert()
    test_compile_lambda()
    # Файлы
    test_compile_file_operations()
    # Списки
    test_compile_list_literal()
    # Структуры
    test_compile_struct_formatting()
    test_compile_class_without_parent()
    # Комплексные
    test_compile_full_game_example()
    test_file_not_found_error()
    print("✓ Все тесты компилятора пройдены!")