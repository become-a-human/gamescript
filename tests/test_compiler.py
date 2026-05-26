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
    """@load с реальным файлом."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        (base / "sword.gs").write_text(
            'SWORD = { "attack": int(8) }', encoding='utf-8'
        )
        
        source = '@load "sword.gs"\nHERO = { "hp": int(100) }'
        cpp = compile_text(source, base_path=base)
        
        assert "struct SWORD_t" in cpp
        assert "struct HERO_t" in cpp


def test_compile_with_grab():
    """~grab захватывает конкретное имя."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        (base / "weapons.gs").write_text(
            'SWORD = { "attack": int(8) }\nAXE = { "attack": int(12) }',
            encoding='utf-8'
        )
        
        source = '~grab <SWORD>'
        cpp = compile_text(source, base_path=base)
        
        assert "struct SWORD_t" in cpp
        assert "AXE" not in cpp


def test_compile_with_grab_alias():
    """~grab с переименованием."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        (base / "hero.gs").write_text(
            'HERO = { "hp": int(100) }', encoding='utf-8'
        )
        
        source = '~grab <HERO> like <Player>'
        cpp = compile_text(source, base_path=base)
        
        assert "struct Player_t" in cpp
        assert "const Player_t Player" in cpp


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
            'PLUGIN_DATA = { "enabled": bool(true) }', encoding='utf-8'
        )
        
        source = '@load? "plugin.gs"'
        cpp = compile_text(source, base_path=base)
        assert "struct PLUGIN_DATA_t" in cpp


def test_compile_error_on_missing_required():
    """@load без ? должен падать если файла нет."""
    try:
        compile_text('@load "nonexistent.gs"')
        assert False, "Должна была быть ошибка"
    except ParseError:
        pass


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


def test_compile_full_game_example():
    """Компиляция примера full_game.gs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        
        (base / "hero.gs").write_text(
            'HERO = { "hp": int(100), "name": str("Артур") }\nclass Hero(Entity): pass',
            encoding='utf-8'
        )
        (base / "weapons.gs").write_text(
            'SWORD = { "attack": int(8) }', encoding='utf-8'
        )
        (base / "armor.gs").write_text(
            'ARMOR = { "defense": int(5) }', encoding='utf-8'
        )
        
        source = '''
@load "hero.gs"
@load "weapons.gs"
@load "armor.gs"
~grab <SWORD>
GAME_CONFIG = { "title": str("Test") }
'''
        cpp = compile_text(source, base_path=base)
        
        assert "struct HERO_t" in cpp
        assert "struct SWORD_t" in cpp
        assert "struct ARMOR_t" in cpp
        assert "struct GAME_CONFIG_t" in cpp
        assert "class Hero : public Entity" in cpp


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
    test_compile_full_game_example()
    print("✓ Все тесты компилятора пройдены!")