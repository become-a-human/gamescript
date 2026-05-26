"""
Тесты генератора C++ кода.

Проверяют, что кодген правильно генерирует C++ код из AST.
"""

import tempfile
from pathlib import Path
from gamescript.compiler import compile_text, compile_file
from gamescript.parser import ParseError


def test_simple_compile():
    """Компиляция без импортов."""
    source = 'HERO = { "hp": int(100) }'
    cpp = compile_text(source)
    assert "struct HERO_t" in cpp
    assert "const HERO_t HERO" in cpp
    assert "int hp;" in cpp


def test_compile_with_load():
    """@load → #include"""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        (base / "sword.gs").write_text(
            'SWORD = { "attack": 8 }', encoding='utf-8'
        )
        
        source = '@load "sword.gs"\nHERO = { "hp": 100 }'
        cpp = compile_text(source, base_path=base)
        
        assert '#include "sword.h"' in cpp
        assert "struct HERO_t" in cpp
        # SWORD НЕ должен быть в этом файле
        assert "SWORD_t" not in cpp


def test_compile_with_grab():
    """~grab захватывает конкретное имя."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        (base / "weapons.gs").write_text(
            'SWORD = { "attack": 8 }\nAXE = { "attack": 12 }',
            encoding='utf-8'
        )
        
        source = '~grab <SWORD>'
        cpp = compile_text(source, base_path=base)
        
        # ~grab добавляет using, а не встраивает struct
        assert "using SWORD" in cpp or "// using SWORD" in cpp
        assert "AXE" not in cpp


def test_compile_with_grab_alias():
    """~grab с переименованием."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        (base / "hero.gs").write_text(
            'HERO = { "hp": 100 }', encoding='utf-8'
        )
        
        source = '~grab <HERO> like <Player>'
        cpp = compile_text(source, base_path=base)
        
        assert "using Player = HERO" in cpp


def test_compile_with_optional_missing():
    """@load? не падает если файла нет."""
    source = '@load? "nonexistent.gs"\nHERO = { "hp": int(100) }'
    cpp = compile_text(source)
    assert "struct HERO_t" in cpp


def test_compile_with_optional_present():
    """@load? работает если файл есть."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        (base / "plugin.gs").write_text(
            'PLUGIN_DATA = { "enabled": true }', encoding='utf-8'
        )
        
        source = '@load? "plugin.gs"'
        cpp = compile_text(source, base_path=base)
        assert '#include "plugin.h"' in cpp
        assert "PLUGIN_DATA_t" not in cpp  # не встраивается, только include


def test_compile_error_on_missing_required():
    """@load без ? должен падать если файла нет."""
    try:
        compile_text('@load "nonexistent.gs"')
        assert False, "Должна была быть ошибка"
    except (ParseError, FileNotFoundError):
        pass  # или FileNotFoundError, если проверка в кодгене


def test_compile_with_compound_assignment():
    """+= и -= в методах."""
    source = '''
class Hero(Entity):
    def on_turn(self):
        self.hp += 10
        self.mp -= 5
'''
    cpp = compile_text(source)
    assert "this->hp += 10;" in cpp
    assert "this->mp -= 5;" in cpp


def test_compile_with_comparison():
    """< и >= в if."""
    source = '''
class Enemy(Entity):
    def on_turn(self):
        if self.hp < 0:
            self.is_alive = false
        if self.hp >= 100:
            self.is_alive = true
'''
    cpp = compile_text(source)
    assert "this->hp < 0" in cpp
    assert "this->hp >= 100" in cpp


def test_compile_method_call():
    """Вызов метода через :"""
    source = '''
class Hero(Entity):
    def on_start(self):
        self:heal(10)
'''
    cpp = compile_text(source)
    assert "this->heal(10);" in cpp


def test_compile_while():
    """Цикл while."""
    source = '''
class Hero(Entity):
    def rest(self):
        while self.hp < self.max_hp:
            self.hp = self.hp + 1
'''
    cpp = compile_text(source)
    assert "while" in cpp


def test_compile_for():
    """Цикл for."""
    source = '''
class Hero(Entity):
    def use_all(self, items):
        for i in items:
            self:use(i)
'''
    cpp = compile_text(source)
    assert "for (auto& i : items)" in cpp


def test_compile_typed_parameters():
    """Типизированные параметры."""
    source = '''
class Hero(Entity):
    def set_name(self, name: str, age: int):
        self.name = name
'''
    cpp = compile_text(source)
    assert "std::string name" in cpp
    assert "int age" in cpp


def test_compile_header():
    """Компиляция в .h (только объявления)."""
    source = '''
HERO = { "hp": 100 }
class Hero(Entity):
    def on_create(self):
        self.hp = 100
'''
    from gamescript.compiler import compile_header
    cpp = compile_header(source, "/dev/null")
    assert "struct HERO_t" in cpp
    assert "const HERO_t HERO" in cpp
    assert "void on_create();" in cpp
    # В .h не должно быть тел методов с {}
    # Проверяем что после "void on_create();" нет "{"
    after_decl = cpp.split("void on_create();")[1]
    after_decl = after_decl.split("};")[0]  # до конца класса
    assert "{" not in after_decl  # нет открывающих скобок


def test_compile_with_like_and_grab_and_link():
    """@load like + ~grab like + &link like"""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        (base / "hero.gs").write_text(
            'HERO = { "hp": 100 }\nclass Hero(Entity):\n    def on_create(self):\n        self.hp = 100\n',
            encoding='utf-8'
        )
        
        source = '''
@load "hero" like "Player"
~grab <Hero> like <MainHero>
&link <on_create> like <init>
'''
        cpp = compile_text(source, base_path=base)
        assert '#include "hero.h"' in cpp
        # namespace только для builtin, hero - не builtin
        assert "using MainHero = Hero;" in cpp
        assert "// &link: init = on_create;" in cpp


def test_compile_full_game_example():
    """Компиляция с @load → #include и ~grab."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        (base / "hero.gs").write_text(
            'HERO = { "hp": 100, "name": "Артур" }\nclass Hero(Entity): pass',
            encoding='utf-8'
        )
        (base / "weapons.gs").write_text(
            'SWORD = { "attack": 8 }', encoding='utf-8'
        )
        
        source = '''
@load "hero.gs"
@load "weapons.gs"
~grab? <SWORD>
GAME_CONFIG = { "title": "Test" }
'''
        cpp = compile_text(source, base_path=base)
        
        assert '#include "hero.h"' in cpp
        assert '#include "weapons.h"' in cpp
        assert "struct GAME_CONFIG_t" in cpp


if __name__ == "__main__":
    test_simple_compile()
    test_compile_with_load()
    test_compile_with_grab()
    test_compile_with_grab_alias()
    test_compile_with_optional_missing()
    test_compile_with_optional_present()
    test_compile_error_on_missing_required()
    test_compile_with_compound_assignment()
    test_compile_with_comparison()
    test_compile_method_call()
    test_compile_while()
    test_compile_for()
    test_compile_typed_parameters()
    test_compile_header()
    test_compile_with_like_and_grab_and_link()
    test_compile_full_game_example()
    print("✓ Все тесты компилятора пройдены!")