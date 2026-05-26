"""
Тесты парсера.

Проверяют, что парсер правильно строит AST из токенов.
"""

from gamescript.lexer import Lexer
from gamescript.parser import Parser, ParseError
from gamescript.ast_nodes import *


def tokenize(source):
    """Вспомогательная функция: исходник → токены."""
    return Lexer(source).tokenize()


# ===== Словари =====

def test_dict_def():
    """Простое определение словаря."""
    source = 'SWORD = { "name": str("Меч"), "attack": int(10) }'
    ast = Parser(tokenize(source)).parse()
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, DictDef)
    assert stmt.name == "SWORD"
    assert isinstance(stmt.value, DictLiteral)
    assert len(stmt.value.pairs) == 2
    assert stmt.value.pairs[0][0] == "name"
    assert stmt.value.pairs[1][0] == "attack"


def test_multiple_dicts():
    """Несколько словарей."""
    source = '''
HERO = { "hp": int(100) }
SWORD = { "attack": int(8) }
MAP = { "name": str("Village") }
'''
    ast = Parser(tokenize(source)).parse()
    assert len(ast.statements) == 3


def test_nested_dict():
    """Вложенный словарь с dict()."""
    source = '''
QUEST = {
    "rewards": dict(
        str("gold"), int(50),
        str("exp"), int(100),
    ),
}
'''
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, DictDef)


def test_list():
    """Список значений."""
    source = 'INVENTORY = { "items": list(str("sword"), str("shield")) }'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, DictDef)


# ===== Классы =====

def test_class_def():
    """Определение класса."""
    source = 'class Hero(Entity): pass'
    ast = Parser(tokenize(source)).parse()
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, ClassDef)
    assert stmt.name == "Hero"
    assert stmt.parent == "Entity"


def test_class_with_method():
    """Класс с методом и присваиванием."""
    source = '''
class Hero(Entity):
    def on_create(self):
        self.hp = 100
'''
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, ClassDef)
    assert len(stmt.methods) == 1
    method = stmt.methods[0]
    assert method.name == "on_create"
    assert len(method.params) == 1
    assert method.params[0] == ("self", "int")
    assert len(method.body) == 1
    assert isinstance(method.body[0], Assignment)


def test_class_with_multiple_methods():
    """Класс с несколькими методами."""
    source = '''
class Hero(Entity):
    def on_create(self):
        self.hp = 100
        self.mp = 50
    
    def on_turn(self, enemy):
        damage = self.attack - enemy.defense
        enemy.hp -= damage
'''
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, ClassDef)
    assert len(stmt.methods) == 2
    assert stmt.methods[0].name == "on_create"
    assert stmt.methods[1].name == "on_turn"
    assert stmt.methods[0].params == [("self", "int")]
    assert stmt.methods[1].params == [("self", "int"), ("enemy", "int")]
    assert len(stmt.methods[0].body) == 2
    assert len(stmt.methods[1].body) == 2


def test_class_with_triple_quoted_docstring():
    """Класс с док-строкой в тройных кавычках."""
    source = '''
class Hero(Entity):
    """Главный герой"""
    def on_create(self):
        pass
'''
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert stmt.doc == "Главный герой"


# ===== Выражения и присваивания =====

def test_simple_assignment():
    """Простое присваивание на верхнем уровне."""
    source = 'x = 42'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.name == "x"
    assert isinstance(stmt.value, NumberLiteral)
    assert stmt.value.value == 42


def test_field_assignment():
    """Присваивание полю (self.hp = ...)"""
    source = 'self.hp = 100'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, Assignment)
    assert stmt.name == "self.hp"


def test_compound_assignment():
    """Составное присваивание."""
    source = 'self.hp += 10'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, CompoundAssignment)
    assert stmt.name == "self.hp"
    assert stmt.op == "+="


def test_method_call():
    """Вызов метода через :"""
    source = '''
class Hero(Entity):
    def on_start(self):
        self:heal(10)
'''
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    method = stmt.methods[0]
    assert len(method.body) == 1
    assert isinstance(method.body[0], MethodCall)
    assert method.body[0].method == "heal"


def test_method_call_on_object():
    """Вызов метода на объекте через :"""
    source = '''
class Game(System):
    def on_start(self):
        player:heal(10)
'''
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    method = stmt.methods[0]
    assert isinstance(method.body[0], MethodCall)
    assert method.body[0].method == "heal"


def test_typed_parameters():
    """Метод с типизированными параметрами."""
    source = '''
class Hero(Entity):
    def heal(self, amount: int):
        self.hp = self.hp + amount
'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert method.params == [("self", "int"), ("amount", "int")]


# ===== Импорты =====

def test_load_import():
    """@load "filename" """
    source = '@load "hero.gs"'
    ast = Parser(tokenize(source)).parse()
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, LoadStmt)
    assert stmt.filename == "hero.gs"
    assert stmt.optional == False


def test_load_optional_import():
    """@load? "filename" """
    source = '@load? "optional.gs"'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, LoadStmt)
    assert stmt.filename == "optional.gs"
    assert stmt.optional == True


def test_grab_import():
    """~grab <Name> like <Alias>, <Name2>"""
    source = '~grab <Hero> like <Player>, <Sword>'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, GrabStmt)
    assert stmt.names == [("Hero", "Player"), ("Sword", None)]
    assert stmt.optional == False


def test_grab_optional_import():
    """~grab? <Name>"""
    source = '~grab? <Hero>'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, GrabStmt)
    assert stmt.optional == True
    assert stmt.names == [("Hero", None)]


def test_link_import():
    """&link <func> like <alias>"""
    source = '&link <on_create> like <init_hero>'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, LinkStmt)
    assert stmt.names == [("on_create", "init_hero")]
    assert stmt.optional == False


def test_link_optional_import():
    """&link? <func>"""
    source = '&link? <rumble>'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, LinkStmt)
    assert stmt.optional == True
    assert stmt.names == [("rumble", None)]


def test_full_import_mix():
    """Смесь импортов и определений (без @load с реальным файлом)."""
    source = '''
~grab <Hero> like <Player>
HERO_ALT = { "hp": int(200) }
&link <on_create> like <init>
'''
    ast = Parser(tokenize(source)).parse()
    assert len(ast.statements) == 3
    assert isinstance(ast.statements[0], GrabStmt)
    assert isinstance(ast.statements[1], DictDef)
    assert isinstance(ast.statements[2], LinkStmt)


# ===== Управляющие конструкции =====

def test_if_statement():
    """if внутри метода."""
    source = '''
class Enemy(Entity):
    def on_turn(self):
        if self.hp == 0:
            self.is_alive = false
'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert len(method.body) == 1
    assert isinstance(method.body[0], IfStmt)


def test_if_else_statement():
    """if/else внутри метода."""
    source = '''
class Enemy(Entity):
    def on_turn(self):
        if self.hp == 0:
            self.is_alive = false
        else:
            self.is_alive = true
'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert len(method.body) == 1
    if_stmt = method.body[0]
    assert isinstance(if_stmt, IfStmt)
    assert if_stmt.else_body is not None


def test_if_with_greater_equal():
    """if с >=."""
    source = '''
class Enemy(Entity):
    def on_turn(self):
        if self.hp >= 100:
            self.is_alive = true
'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert isinstance(method.body[0], IfStmt)


def test_while_statement():
    """while внутри метода."""
    source = '''
class Hero(Entity):
    def rest(self):
        while self.hp < self.max_hp:
            self.hp = self.hp + 1
'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert isinstance(method.body[0], WhileStmt)


def test_for_statement():
    """for внутри метода."""
    source = '''
class Hero(Entity):
    def use_all(self, items):
        for i in items:
            self:use(i)
'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert isinstance(method.body[0], ForStmt)
    assert method.body[0].var == "i"


def test_return_statement():
    """return из метода."""
    source = '''
class Enemy(Entity):
    def get_hp(self):
        return self.hp
'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert len(method.body) == 1
    assert isinstance(method.body[0], ReturnStmt)


def test_continue_break():
    """continue и break."""
    source1 = '''
class Hero(Entity):
    def loop(self):
        while self.hp > 0:
            break
'''
    ast = Parser(tokenize(source1)).parse()
    while_body = ast.statements[0].methods[0].body[0].body
    assert isinstance(while_body[0], BreakStmt)
    
    source2 = '''
class Hero(Entity):
    def loop(self):
        while self.hp > 0:
            continue
'''
    ast = Parser(tokenize(source2)).parse()
    while_body = ast.statements[0].methods[0].body[0].body
    assert isinstance(while_body[0], ContinueStmt)


# ===== Запуск =====

if __name__ == "__main__":
    # Словари
    test_dict_def()
    test_multiple_dicts()
    test_nested_dict()
    test_list()
    
    # Классы
    test_class_def()
    test_class_with_method()
    test_class_with_multiple_methods()
    test_class_with_triple_quoted_docstring()
    
    # Выражения и присваивания
    test_simple_assignment()
    test_field_assignment()
    test_compound_assignment()
    test_method_call()
    test_method_call_on_object()
    test_typed_parameters()
    
    # Импорты
    test_load_import()
    test_load_optional_import()
    test_grab_import()
    test_grab_optional_import()
    test_link_import()
    test_link_optional_import()
    test_full_import_mix()
    
    # Управляющие конструкции
    test_if_statement()
    test_if_else_statement()
    test_if_with_greater_equal()
    test_while_statement()
    test_for_statement()
    test_return_statement()
    test_continue_break()
    
    print("✓ Все тесты парсера пройдены!")