"""
Тесты парсера GameScript.

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
    source = 'SWORD = { "name": "Меч", "attack": 10 }'
    ast = Parser(tokenize(source)).parse()
    assert len(ast.statements) == 1
    stmt = ast.statements[0]
    assert isinstance(stmt, DictDef) and stmt.name == "SWORD"
    assert isinstance(stmt.value, DictLiteral) and len(stmt.value.pairs) == 2


def test_multiple_dicts():
    """Несколько словарей."""
    source = '''HERO = { "hp": 100 }\nSWORD = { "attack": 8 }\nMAP = { "name": "Village" }'''
    ast = Parser(tokenize(source)).parse()
    assert len(ast.statements) == 3


def test_nested_dict():
    """Вложенный словарь через dict()."""
    source = '''QUEST = { "rewards": dict(str("gold"), int(50), str("exp"), int(100)) }'''
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0], DictDef)


def test_list_in_dict():
    """Список через list() в словаре."""
    source = 'INVENTORY = { "items": list("sword", "shield") }'
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0], DictDef)


# ===== Классы =====

def test_class_def():
    """Класс с родителем."""
    source = 'class Hero(Entity): pass'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, ClassDef) and stmt.name == "Hero" and stmt.parent == "Entity"


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


def test_class_with_method():
    """Класс с одним методом."""
    source = '''class Hero(Entity):\n    def on_create(self):\n        self.hp = 100'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert method.name == "on_create"
    assert method.params == [("self", "int")]
    assert len(method.body) == 1


def test_class_with_multiple_methods():
    """Класс с несколькими методами."""
    source = '''class Hero(Entity):
    def on_create(self):
        self.hp = 100
        self.mp = 50
    def on_turn(self, enemy):
        damage = self.attack - enemy.defense
        enemy.hp -= damage'''
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert len(stmt.methods) == 2
    assert stmt.methods[1].name == "on_turn"


def test_class_with_docstring():
    """Класс с док-строкой."""
    source = '''class Hero(Entity):\n    """Главный герой"""\n    def on_create(self):\n        pass'''
    ast = Parser(tokenize(source)).parse()
    assert ast.statements[0].doc == "Главный герой"


# ===== Присваивания =====

def test_simple_assignment():
    """Простое присваивание."""
    source = 'x = 42'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, Assignment) and stmt.name == "x" and stmt.value.value == 42


def test_field_assignment():
    """Присваивание полю через self."""
    source = 'self.hp = 100'
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0], Assignment) and ast.statements[0].name == "self.hp"


def test_compound_assignment():
    """Составное присваивание."""
    source = 'self.hp += 10'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, CompoundAssignment) and stmt.op == "+="


def test_increment():
    """Постфиксный инкремент."""
    source = 'self.hp++'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, CompoundAssignment) and stmt.op == '++'


def test_decrement():
    """Постфиксный декремент."""
    source = 'self.hp--'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, CompoundAssignment) and stmt.op == '--'


def test_modulo_operator():
    source = 'self.frame = (self.frame + 1) % self.total_frames'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt.value, BinaryOp) and stmt.value.op == '%'


def test_xor_operator():
    source = 'self.flags = self.flags ^ 1'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt.value, BinaryOp) and stmt.value.op == '^'


def test_modulo_compound():
    source = 'self.hp %= 10'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, CompoundAssignment) and stmt.op == '%='


# ===== Вызовы =====

def test_method_call():
    """Вызов метода через ':'."""
    source = '''class Hero(Entity):\n    def on_start(self):\n        self:heal(10)'''
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0].methods[0].body[0], MethodCall)


def test_method_call_on_object():
    """Вызов метода на объекте."""
    source = '''class Game(System):\n    def on_start(self):\n        player:heal(10)'''
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0].methods[0].body[0], MethodCall)


def test_constructor_call():
    """Вызов конструктора с параметрами."""
    source = 'self.hero = Hero("Артур", 100)'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, Assignment)
    assert isinstance(stmt.value, FunCall)
    assert stmt.value.name == "Hero"
    assert len(stmt.value.args) == 2


def test_constructor_no_args():
    """Вызов конструктора без параметров."""
    source = 'self.hero = Hero()'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt.value, FunCall)
    assert stmt.value.name == "Hero"
    assert len(stmt.value.args) == 0


# ===== Параметры методов =====

def test_typed_parameters():
    """Типизированные параметры."""
    source = '''class Hero(Entity):\n    def heal(self, amount: int):\n        self.hp = self.hp + amount'''
    ast = Parser(tokenize(source)).parse()
    assert ast.statements[0].methods[0].params == [("self", "int"), ("amount", "int")]


def test_vararg():
    """*args в методе."""
    source = '''class Hero(Entity):
    def sum(self, *numbers):
        for n in numbers:
            self.total = self.total + n'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert method.vararg == "numbers"
    assert method.params == [("self", "int")]


def test_vararg_with_params():
    """*args с обычными параметрами."""
    source = '''class Hero(Entity):
    def sum(self, base: int, *numbers):
        self.total = base'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert method.vararg == "numbers"
    assert method.params == [("self", "int"), ("base", "int")]


# ===== Импорты =====

def test_load_import():
    """@load."""
    source = '@load "hero.gs"'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, LoadStmt) and stmt.filename == "hero.gs" and not stmt.optional


def test_load_optional_import():
    """@load?."""
    source = '@load? "optional.gs"'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, LoadStmt) and stmt.optional


def test_load_like():
    """@load с like."""
    source = '@load "hero" like "Player"'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, LoadStmt) and stmt.filename == "hero" and stmt.alias == "Player"


def test_load_like_star():
    """@load с like *."""
    source = '@load "hero" like "*"'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert stmt.alias == "*"


# ===== Управляющие конструкции =====

def test_if_statement():
    """if."""
    source = '''class Enemy(Entity):\n    def on_turn(self):\n        if self.hp == 0:\n            self.is_alive = false'''
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0].methods[0].body[0], IfStmt)


def test_if_else_statement():
    """if/else."""
    source = '''class Enemy(Entity):\n    def on_turn(self):\n        if self.hp == 0:\n            self.is_alive = false\n        else:\n            self.is_alive = true'''
    ast = Parser(tokenize(source)).parse()
    assert ast.statements[0].methods[0].body[0].else_body is not None


def test_elif_statement():
    """if/elif/else."""
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
    assert isinstance(if_stmt, IfStmt) and if_stmt.else_body is not None


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
    inner_if = method.body[0].body[0]
    assert isinstance(inner_if, IfStmt) and inner_if.else_body is not None


def test_while_statement():
    """while."""
    source = '''class Hero(Entity):\n    def rest(self):\n        while self.hp < self.max_hp:\n            self.hp = self.hp + 1'''
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0].methods[0].body[0], WhileStmt)


def test_nested_while():
    """Вложенные while."""
    source = '''class Hero(Entity):
    def loop(self):
        while self.hp > 0:
            while self.mp > 0:
                self.mp = self.mp - 1
            self.hp = self.hp - 1'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    inner = method.body[0].body[0]
    assert isinstance(inner, WhileStmt)


def test_for_statement():
    """for."""
    source = '''class Hero(Entity):\n    def use_all(self, items):\n        for i in items:\n            self:use(i)'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert isinstance(method.body[0], ForStmt) and method.body[0].var == "i"


def test_return_statement():
    """return."""
    source = '''class Enemy(Entity):\n    def get_hp(self):\n        return self.hp'''
    ast = Parser(tokenize(source)).parse()
    assert isinstance(ast.statements[0].methods[0].body[0], ReturnStmt)


def test_continue_break():
    """continue и break."""
    s1 = '''class Hero(Entity):\n    def loop(self):\n        while self.hp > 0:\n            break'''
    assert isinstance(Parser(tokenize(s1)).parse().statements[0].methods[0].body[0].body[0], BreakStmt)
    s2 = '''class Hero(Entity):\n    def loop(self):\n        while self.hp > 0:\n            continue'''
    assert isinstance(Parser(tokenize(s2)).parse().statements[0].methods[0].body[0].body[0], ContinueStmt)


# ===== Выражения =====

def test_not_operator():
    """Унарный not."""
    source = '''class Hero(Entity):
    def check(self):
        if not self.is_alive:
            self.hp = 0'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert isinstance(method.body[0].condition, UnaryOp) and method.body[0].condition.op == '!'


def test_logical_and_or():
    """and/or."""
    source = '''class Hero(Entity):
    def check(self):
        if self.hp > 0 and self.mp > 0:
            self.is_alive = true'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert isinstance(method.body[0].condition, BinaryOp) and method.body[0].condition.op == 'and'


def test_null_in_expression():
    """None в выражении."""
    source = '''class Hero(Entity):
    def check(self):
        if self.target != None:
            self.hp = 100'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert isinstance(method.body[0].condition.right, NoneLiteral)


def test_list_literal():
    """Список [1, 2, 3]."""
    source = 'self.items = [1, 2, 3]'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, Assignment)
    assert isinstance(stmt.value, ListLiteral)
    assert len(stmt.value.elements) == 3


# ===== Встроенные функции =====

def test_print_statement():
    """print()."""
    source = '''class Hero(Entity):
    def debug(self):
        print(self.hp)'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert isinstance(method.body[0], PrintStmt)


def test_assert_statement():
    """assert."""
    source = '''class Hero(Entity):
    def check(self):
        assert self.hp >= 0'''
    ast = Parser(tokenize(source)).parse()
    method = ast.statements[0].methods[0]
    assert isinstance(method.body[0], AssertStmt)


# ===== Лямбды =====

def test_lambda_no_params():
    """Лямбда без параметров."""
    source = 'f = fn(): 42'
    ast = Parser(tokenize(source)).parse()
    stmt = ast.statements[0]
    assert isinstance(stmt, Assignment)
    assert isinstance(stmt.value, LambdaExpr)
    assert len(stmt.value.body) == 1


def test_lambda_with_params():
    """Лямбда с параметрами."""
    source = 'f = fn(x: int): x * 2'
    ast = Parser(tokenize(source)).parse()
    lam = ast.statements[0].value
    assert lam.params == [('x', 'int')]
    assert len(lam.body) == 1


if __name__ == "__main__":
    # Словари
    test_dict_def(); test_multiple_dicts(); test_nested_dict(); test_list_in_dict()
    # Классы
    test_class_def(); test_class_without_parent()
    test_class_with_method(); test_class_with_multiple_methods()
    test_class_with_docstring()
    # Присваивания
    test_simple_assignment(); test_field_assignment()
    test_compound_assignment(); test_increment(); test_decrement()
    test_modulo_operator(); test_xor_operator(); test_modulo_compound()
    # Вызовы
    test_method_call(); test_method_call_on_object()
    test_constructor_call(); test_constructor_no_args()
    # Параметры
    test_typed_parameters(); test_vararg(); test_vararg_with_params()
    # Импорты
    test_load_import(); test_load_optional_import()
    test_load_like(); test_load_like_star()
    # Управляющие конструкции
    test_if_statement(); test_if_else_statement(); test_elif_statement()
    test_nested_if_else()
    test_while_statement(); test_nested_while()
    test_for_statement(); test_return_statement()
    test_continue_break()
    # Выражения
    test_not_operator(); test_logical_and_or()
    test_null_in_expression(); test_list_literal()
    # Встроенные
    test_print_statement(); test_assert_statement()
    # Лямбды
    test_lambda_no_params(); test_lambda_with_params()
    print("✓ Все тесты парсера пройдены!")