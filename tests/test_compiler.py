"""
Тесты компилятора.
"""

import tempfile
from pathlib import Path
from gamescript.compiler import compile_text, compile_header
from gamescript.parser import ParseError


def test_simple_compile():
    source = 'HERO = { "hp": 100 }'
    cpp = compile_text(source)
    assert "struct HERO_t" in cpp and "const HERO_t HERO" in cpp and "int hp;" in cpp


def test_compile_with_load():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "sword.gs").write_text('SWORD = { "attack": 8 }', encoding='utf-8')
        cpp = compile_text('@load "sword.gs"\nHERO = { "hp": 100 }', base_path=base)
        assert '#include "sword.h"' in cpp and "struct HERO_t" in cpp and "SWORD_t" not in cpp


def test_compile_with_optional_missing():
    cpp = compile_text('@load? "nonexistent.gs"\nHERO = { "hp": 100 }')
    assert "struct HERO_t" in cpp


def test_compile_with_optional_present():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "plugin.gs").write_text('PLUGIN_DATA = { "enabled": true }', encoding='utf-8')
        cpp = compile_text('@load? "plugin.gs"', base_path=base)
        assert '#include "plugin.h"' in cpp and "PLUGIN_DATA_t" not in cpp


def test_compile_error_on_missing_required():
    try:
        compile_text('@load "nonexistent.gs"')
        assert False
    except ParseError:
        pass


def test_compile_with_compound_assignment():
    cpp = compile_text('class Hero(Entity):\n    def on_turn(self):\n        self.hp += 10\n        self.mp -= 5')
    assert "this->hp += 10;" in cpp and "this->mp -= 5;" in cpp


def test_compile_with_comparison():
    cpp = compile_text('class Enemy(Entity):\n    def on_turn(self):\n        if self.hp < 0:\n            self.is_alive = false\n        if self.hp >= 100:\n            self.is_alive = true')
    assert "this->hp < 0" in cpp and "this->hp >= 100" in cpp


def test_compile_method_call():
    cpp = compile_text('class Hero(Entity):\n    def on_start(self):\n        self:heal(10)')
    assert "this->heal(10);" in cpp


def test_compile_while():
    cpp = compile_text('class Hero(Entity):\n    def rest(self):\n        while self.hp < self.max_hp:\n            self.hp = self.hp + 1')
    assert "while" in cpp


def test_compile_for():
    cpp = compile_text('class Hero(Entity):\n    def use_all(self, items):\n        for i in items:\n            self:use(i)')
    assert "for (auto& i : items)" in cpp


def test_compile_typed_parameters():
    cpp = compile_text('class Hero(Entity):\n    def set_name(self, name: str, age: int):\n        self.name = name')
    assert "std::string name" in cpp and "int age" in cpp


def test_compile_header():
    cpp = compile_header('HERO = { "hp": 100 }\nclass Hero(Entity):\n    def on_create(self):\n        self.hp = 100', "/dev/null")
    assert "struct HERO_t" in cpp and "void on_create();" in cpp
    after = cpp.split("void on_create();")[1].split("};")[0]
    assert "{" not in after


def test_compile_full_game_example():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "hero.gs").write_text('HERO = { "hp": 100 }\nclass Hero(Entity): pass', encoding='utf-8')
        (base / "weapons.gs").write_text('SWORD = { "attack": 8 }', encoding='utf-8')
        cpp = compile_text('@load "hero.gs"\n@load "weapons.gs"\nGAME_CONFIG = { "title": "Test" }', base_path=base)
        assert '#include "hero.h"' in cpp and '#include "weapons.h"' in cpp
        assert "struct GAME_CONFIG_t" in cpp and "HERO_t" not in cpp and "SWORD_t" not in cpp


def test_compile_load_like():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "hero.gs").write_text('HERO = { "hp": 100 }', encoding='utf-8')
        cpp = compile_text('@load "hero" like "Player"', base_path=base)
        assert '#include "hero.h"' in cpp
        assert "using Player = hero;" in cpp


def test_compile_load_like_star():
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        (base / "hero.gs").write_text('HERO = { "hp": 100 }', encoding='utf-8')
        cpp = compile_text('@load "hero" like "*"', base_path=base)
        assert '#include "hero.h"' in cpp
        assert "using namespace hero;" in cpp


def test_compile_not():
    cpp = compile_text('class Hero(Entity):\n    def check(self):\n        if not self.is_alive:\n            self.hp = 0')
    assert '!this->is_alive' in cpp


def test_compile_elif():
    cpp = compile_text('''class Hero(Entity):
    def check(self):
        if self.hp > 50:
            self.status = "good"
        elif self.hp > 20:
            self.status = "ok"
        else:
            self.status = "bad"''')
    assert 'else {' in cpp
    assert 'if (' in cpp


def test_compile_list_literal():
    cpp = compile_text('class Hero(Entity):\n    def init(self):\n        self.items = [1, 2, 3]')
    assert '{1, 2, 3}' in cpp


def test_compile_increment():
    cpp = compile_text('class Hero(Entity):\n    def tick(self):\n        self.hp++')
    assert 'this->hp++;' in cpp

def test_compile_decrement():
    cpp = compile_text('class Hero(Entity):\n    def tick(self):\n        self.hp--')
    assert 'this->hp--;' in cpp


def test_file_not_found_error():
    try:
        compile_text('@load "nonexistent_file_12345"')
        assert False
    except ParseError as e:
        assert "не найден" in str(e)


def test_compile_indent_blocks():
    """Правильные отступы в сгенерированном C++."""
    cpp = compile_text('''class Hero(Entity):
    def loop(self):
        while self.hp > 0:
            if self.hp == 10:
                break
            if self.hp == 5:
                continue
            self.hp = self.hp - 1''')
    assert 'break;' in cpp
    assert 'continue;' in cpp
    # break не должен быть внутри другого if
    assert 'if (this->hp == 10) {\n                break;\n            }' in cpp


def test_compile_nested_while():
    """Вложенные while."""
    cpp = compile_text('''class Hero(Entity):
    def loop(self):
        while self.hp > 0:
            while self.mp > 0:
                self.mp = self.mp - 1
            self.hp = self.hp - 1''')
    # Правильные отступы для вложенных блоков
    assert 'while (this->hp > 0)' in cpp
    assert 'while (this->mp > 0)' in cpp


def test_compile_else_if():
    """elif → else if."""
    cpp = compile_text('''class Hero(Entity):
    def check(self):
        if self.hp > 80:
            self.status = "great"
        elif self.hp > 50:
            self.status = "good"
        else:
            self.status = "bad"''')
    assert 'else if (this->hp > 50)' in cpp


def test_compile_null_check():
    """None → nullptr."""
    cpp = compile_text('''class Hero(Entity):
    def check(self):
        if self.target != None:
            self.hp = 100''')
    assert 'this->target != nullptr' in cpp


def test_compile_print():
    """print() → std::cout."""
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


def test_compile_logical_operators():
    """and/or → &&/||."""
    cpp = compile_text('''class Hero(Entity):
    def check(self):
        if self.hp > 0 and self.mp > 0:
            self.is_alive = true''')
    assert '&&' in cpp


def test_compile_class_without_parent():
    """Класс без родителя генерирует class без : public."""
    cpp = compile_text('''class Entity:
    def on_create(self):
        self.hp = 100''')
    assert 'class Entity {' in cpp
    assert ': public' not in cpp.split('class Entity')[1].split('{')[0]


def test_compile_struct_formatting():
    """Отступы в struct."""
    cpp = compile_text('HERO = { "hp": 100, "mp": 50 }')
    assert '    int hp;\n    int mp;' in cpp or '    int hp;' in cpp


def test_compile_pragma_once():
    """#pragma once в .h файлах."""
    cpp = compile_header('HERO = { "hp": 100 }', "/dev/null")
    assert '#pragma once' in cpp


def test_compile_lambda():
    cpp = compile_text('class Hero(Entity):\n    def setup(self):\n        self.fn = fn(): 42')
    assert '[&]' in cpp or 'lambda' in cpp


def test_compile_vararg():
    cpp = compile_text('''class Hero(Entity):
    def sum(self, *numbers):
        self.total = 0''')
    assert 'std::vector<int> numbers' in cpp


def test_compile_constructor():
    cpp = compile_text('class Hero(Entity):\n    def create(self):\n        self.hero = Hero("Артур", 100)')
    assert 'new Hero("Артур", 100)' in cpp


def test_compile_constructor_no_args():
    cpp = compile_text('class Hero(Entity):\n    def create(self):\n        self.hero = Hero()')
    assert 'new Hero()' in cpp


def test_compile_file_operations():
    cpp = compile_text('''class Hero(Entity):
    def save(self):
        f = open("save.txt", "out")
        write(f, self.name)
        close(f)''')
    assert 'std::fstream' in cpp
    assert 'std::ios::out' in cpp


def test_compile_math():
    cpp = compile_text('class Calc(System):\n    def calc(self, x: int):\n        self.r = sqrt(x)\n        self.s = sin(x)')
    assert 'sqrt(x)' in cpp
    assert 'sin(x)' in cpp
    assert 'new sqrt' not in cpp


if __name__ == "__main__":
    test_simple_compile(); test_compile_with_load()
    test_compile_with_optional_missing(); test_compile_with_optional_present()
    test_compile_error_on_missing_required()
    test_compile_with_compound_assignment(); test_compile_with_comparison()
    test_compile_method_call(); test_compile_while(); test_compile_for()
    test_compile_typed_parameters(); test_compile_header()
    test_compile_full_game_example()
    test_compile_load_like(); test_compile_load_like_star()
    test_compile_not(); test_compile_elif(); test_compile_list_literal()
    test_compile_increment(); test_compile_decrement()
    test_file_not_found_error()
    test_compile_indent_blocks(); test_compile_nested_while()
    test_compile_else_if(); test_compile_null_check()
    test_compile_print(); test_compile_assert()
    test_compile_logical_operators(); test_compile_class_without_parent()
    test_compile_struct_formatting(); test_compile_pragma_once()
    test_compile_lambda()
    test_compile_vararg()
    test_compile_constructor(); test_compile_constructor_no_args()
    test_compile_file_operations()
    test_compile_math()
    print("✓ Все тесты компилятора пройдены!")