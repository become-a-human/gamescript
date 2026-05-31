"""
Тесты парсера.
"""

from gamescript.lexer import Lexer
from gamescript.parser import Parser, ParseError
from gamescript.ast_nodes import *


def tokenize(source):
    return Lexer(source).tokenize()


def test_dict_def():
    source = 'SWORD = { "name": "Меч", "attack": 10 }'
    ast = Parser(tokenize(source)).parse()
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, DictDef) and stmt.name == "SWORD"
    assert isinstance(stmt.value, DictLiteral) and len(stmt.value.pairs) == 2


def test_multiple_dicts():
    source = '''HERO = { "hp": 100 }\nSWORD = { "attack": 8 }\nMAP = { "name": "Village" }'''
    ast = Parser(tokenize(source)).parse()
    assert len(ast.statements) == 3


def test_nested_dict():
    source = '''QUEST = { "rewards": dict(str("gold"), int(50), str("exp"), int(100)) }'''
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0], DictDef)


def test_list():
    source = 'INVENTORY = { "items": list("sword", "shield") }'
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0], DictDef)


def test_class_def():
    source = 'class Hero(Entity): pass'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, ClassDef) and stmt.name == "Hero" and stmt.parent == "Entity"


def test_class_with_method():
    source = '''class Hero(Entity):\n    def on_create(self):\n        self.hp = 100'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert method.name == "on_create" and method.params == [("self", "int")] and len(method.body) == 1


def test_class_with_multiple_methods():
    source = '''class Hero(Entity):
    def on_create(self):
        self.hp = 100
        self.mp = 50
    def on_turn(self, enemy):
        damage = self.attack - enemy.defense
        enemy.hp -= damage'''
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert len(stmt.methods) == 2 and stmt.methods[1].name == "on_turn"


def test_class_with_triple_quoted_docstring():
    source = '''class Hero(Entity):\n    """Главный герой"""\n    def on_create(self):\n        pass'''
    ast = Parser(tokenize(source)).parse()
    assert ast.statements[0].doc == "Главный герой"


def test_simple_assignment():
    source = 'x = 42'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, Assignment) and stmt.name == "x" and stmt.value.value == 42


def test_field_assignment():
    source = 'self.hp = 100'
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0], Assignment) and ast.statements[0].name == "self.hp"


def test_compound_assignment():
    source = 'self.hp += 10'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, CompoundAssignment) and stmt.op == "+="


def test_method_call():
    source = '''class Hero(Entity):\n    def on_start(self):\n        self:heal(10)'''
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0].methods[0].body[0], MethodCall)


def test_method_call_on_object():
    source = '''class Game(System):\n    def on_start(self):\n        player:heal(10)'''
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0].methods[0].body[0], MethodCall)


def test_typed_parameters():
    source = '''class Hero(Entity):\n    def heal(self, amount: int):\n        self.hp = self.hp + amount'''
    ast = Parser(tokenize(source)).parse()
    assert ast.statements[0].methods[0].params == [("self", "int"), ("amount", "int")]


def test_load_import():
    source = '@load "hero.gs"'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, LoadStmt) and stmt.filename == "hero.gs" and not stmt.optional


def test_load_optional_import():
    source = '@load? "optional.gs"'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, LoadStmt) and stmt.optional


def test_if_statement():
    source = '''class Enemy(Entity):\n    def on_turn(self):\n        if self.hp == 0:\n            self.is_alive = false'''
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0].methods[0].body[0], IfStmt)


def test_if_else_statement():
    source = '''class Enemy(Entity):\n    def on_turn(self):\n        if self.hp == 0:\n            self.is_alive = false\n        else:\n            self.is_alive = true'''
    ast = Parser(tokenize(source)).parse()
    assert ast.statements[0].methods[0].body[0].else_body is not None


def test_if_with_greater_equal():
    source = '''class Enemy(Entity):\n    def on_turn(self):\n        if self.hp >= 100:\n            self.is_alive = true'''
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0].methods[0].body[0], IfStmt)


def test_while_statement():
    source = '''class Hero(Entity):\n    def rest(self):\n        while self.hp < self.max_hp:\n            self.hp = self.hp + 1'''
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0].methods[0].body[0], WhileStmt)


def test_for_statement():
    source = '''class Hero(Entity):\n    def use_all(self, items):\n        for i in items:\n            self:use(i)'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert isinstance(method.body[0], ForStmt) and method.body[0].var == "i"


def test_return_statement():
    source = '''class Enemy(Entity):\n    def get_hp(self):\n        return self.hp'''
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0].methods[0].body[0], ReturnStmt)


def test_continue_break():
    s1 = '''class Hero(Entity):\n    def loop(self):\n        while self.hp > 0:\n            break'''
    assert isinstance(Parser(tokenize(s1)).parse().statements[0].methods[0].body[0].body[0], BreakStmt)
    s2 = '''class Hero(Entity):\n    def loop(self):\n        while self.hp > 0:\n            continue'''
    assert isinstance(Parser(tokenize(s2)).parse().statements[0].methods[0].body[0].body[0], ContinueStmt)


def test_load_like():
    source = '@load "hero" like "Player"'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, LoadStmt)
    assert stmt.filename == "hero"
    assert stmt.alias == "Player"


def test_load_like_star():
    source = '@load "hero" like "*"'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert stmt.alias == "*"


def test_not_operator():
    source = '''class Hero(Entity):
    def check(self):
        if not self.is_alive:
            self.hp = 0'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert isinstance(method.body[0], IfStmt)
    assert isinstance(method.body[0].condition, UnaryOp)
    assert method.body[0].condition.op == '!'


def test_elif_statement():
    source = '''class Hero(Entity):
    def check(self):
        if self.hp > 50:
            self.status = "good"
        elif self.hp > 20:
            self.status = "ok"
        else:
            self.status = "bad"'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    if_stmt = method.body[0]
    assert isinstance(if_stmt, IfStmt)
    assert if_stmt.else_body is not None


def test_list_literal():
    source = 'self.items = [1, 2, 3]'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, Assignment)
    assert isinstance(stmt.value, ListLiteral)
    assert len(stmt.value.elements) == 3


def test_increment():
    source = 'self.hp++'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, CompoundAssignment)
    assert stmt.op == '++'

def test_decrement():
    source = 'self.hp--'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, CompoundAssignment)
    assert stmt.op == '--'


def test_class_without_parent():
    """Класс без родителя."""
    source = '''class Entity:
    def on_create(self):
        self.hp = 100'''
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, ClassDef)
    assert stmt.name == "Entity"
    assert stmt.parent is None
    assert len(stmt.methods) == 1


def test_nested_while():
    """Вложенные while с break."""
    source = '''class Hero(Entity):
    def loop(self):
        while self.hp > 0:
            while self.mp > 0:
                self.mp = self.mp - 1
            self.hp = self.hp - 1'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    outer = method.body[0]
    assert isinstance(outer, WhileStmt)
    assert len(outer.body) == 2  # inner while + self.hp
    inner = outer.body[0]
    assert isinstance(inner, WhileStmt)


def test_nested_if_else():
    """Вложенные if/else."""
    source = '''class Hero(Entity):
    def check(self):
        if self.hp > 50:
            if self.mp > 20:
                self.status = "good"
            else:
                self.status = "ok"
        else:
            self.status = "bad"'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    outer_if = method.body[0]
    assert isinstance(outer_if, IfStmt)
    inner_if = outer_if.body[0]
    assert isinstance(inner_if, IfStmt)
    assert inner_if.else_body is not None


def test_print_statement():
    """print() парсится."""
    source = '''class Hero(Entity):
    def debug(self):
        print(self.hp)'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert isinstance(method.body[0], PrintStmt)


def test_assert_statement():
    """assert парсится."""
    source = '''class Hero(Entity):
    def check(self):
        assert self.hp >= 0'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert isinstance(method.body[0], AssertStmt)


def test_logical_and_or():
    """and/or в выражениях."""
    source = '''class Hero(Entity):
    def check(self):
        if self.hp > 0 and self.mp > 0:
            self.is_alive = true'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    condition = method.body[0].condition
    assert isinstance(condition, BinaryOp)
    assert condition.op == 'and'


def test_null_in_expression():
    """None в выражении."""
    source = '''class Hero(Entity):
    def check(self):
        if self.target != None:
            self.hp = 100'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    condition = method.body[0].condition
    assert isinstance(condition.right, NoneLiteral)


if __name__ == "__main__":
    test_dict_def(); test_multiple_dicts(); test_nested_dict(); test_list()
    test_class_def(); test_class_with_method(); test_class_with_multiple_methods()
    test_class_with_triple_quoted_docstring()
    test_simple_assignment(); test_field_assignment(); test_compound_assignment()
    test_method_call(); test_method_call_on_object(); test_typed_parameters()
    test_load_import(); test_load_optional_import()
    test_if_statement(); test_if_else_statement(); test_if_with_greater_equal()
    test_while_statement(); test_for_statement(); test_return_statement()
    test_continue_break()
    test_load_like(); test_load_like_star()
    test_not_operator(); test_elif_statement(); test_list_literal()
    test_increment(); test_decrement()
    test_class_without_parent(); test_nested_while(); test_nested_if_else()
    test_print_statement(); test_assert_statement()
    test_logical_and_or(); test_null_in_expression()
    print("✓ Все тесты парсера пройдены!")