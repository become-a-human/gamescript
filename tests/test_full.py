"""Полные тесты всех фич GameScript."""

from gamescript.compiler import compile_text, compile_header
from gamescript.lexer import Lexer
from gamescript.parser import Parser, ParseError
from gamescript.tokens import TokenType
import sys

def tokenize(s): return Lexer(s).tokenize()

def test_all_tokens():
    """Все токены распознаются."""
    lexer = Lexer("class def if else elif while for in return continue break fn like "
                  "int float str bool list dict "
                  "true false None and or not "
                  "print assert open read write close "
                  "+ - * / % ^ ++ -- "
                  "+= -= *= /= %= ^= "
                  "== != < > <= >= "
                  "= : , ; . ( ) [ ] { } "
                  "@load @load? "
                  '"""doc""" "str" 42 3.14')
    tokens = lexer.tokenize()
    types = {t.type for t in tokens}
    assert TokenType.CLASS in types
    assert TokenType.FN in types
    assert TokenType.PERCENT in types
    assert TokenType.CARET in types
    assert TokenType.PLUS_PLUS in types
    assert TokenType.AT_LOAD_OPT in types
    print('✓ Токены')

def test_all_expressions():
    """Все выражения парсятся."""
    tests = [
        'x = 42',
        'x = 3.14',
        'x = "hello"',
        'x = true',
        'x = false',
        'x = None',
        'x = y',
        'x = y.field',
        'x = y + z',
        'x = y - z',
        'x = y * z',
        'x = y / z',
        'x = y % z',
        'x = y ^ z',
        'x = -y',
        'x = not y',
        'x = y and z',
        'x = y or z',
        'x = y == z',
        'x = y != z',
        'x = y < z',
        'x = y > z',
        'x = y <= z',
        'x = y >= z',
        'x = (y + z) * w',
        'x = [1, 2, 3]',
        'x = {"a": 1}',
        'x = fn(): 42',
        'x = fn(y): y * 2',
        'x = Hero()',
        'x = Hero("A", 10)',
    ]
    for src in tests:
        ast = Parser(tokenize(src)).parse()
        assert len(ast.statements) == 1, f'Failed: {src}'
    print('✓ Выражения')

def test_all_statements():
    """Все инструкции парсятся."""
    src = '''
class Entity:
    def f(self):
        if self.hp > 0:
            self.hp = self.hp - 1
        elif self.hp == 0:
            self.alive = false
        else:
            self.hp = 100
        while self.hp < 100:
            self.hp = self.hp + 1
        for i in items:
            self:use(i)
        return self.hp
        break
        continue
        pass
        print(self.hp)
        assert self.hp >= 0
        f = open("t.txt", "out")
        write(f, "data")
        close(f)
        self.hp += 10
        self.hp -= 5
        self.hp *= 2
        self.hp /= 3
        self.hp %= 10
        self.hp ^= 1
        self.hp++
        self.hp--
        ++self.hp
        --self.hp
'''
    ast = Parser(tokenize(src)).parse()
    cls = ast.statements[0]
    assert len(cls.methods) == 1
    assert len(cls.methods[0].body) >= 15
    print('✓ Инструкции')

def test_compile_all():
    """Все фичи компилируются."""
    tests = {
        'lambda': ('class H(Entity):\n    def f(self):\n        self.fn = fn(): 42', '[&]'),
        'vararg': ('class H(Entity):\n    def f(self, *nums):\n        self.t = 0', 'std::vector<int> nums'),
        'constructor': ('class H(Entity):\n    def f(self):\n        self.h = H("A", 10)', 'H("A", 10)'),
        'sqrt': ('class C(System):\n    def f(self, x: int):\n        self.r = sqrt(x)', 'sqrt(x)'),
        'not': ('class H(Entity):\n    def f(self):\n        if not self.a:\n            self.hp = 0', '!this->a'),
        'elif': ('class H(Entity):\n    def f(self):\n        if self.hp > 50:\n            self.s = "g"\n        elif self.hp > 20:\n            self.s = "o"\n        else:\n            self.s = "b"', 'else if'),
        'list': ('class H(Entity):\n    def f(self):\n        self.items = [1, 2, 3]', '{1, 2, 3}'),
        'percent': ('class H(Entity):\n    def f(self):\n        self.x = self.y % 10', '%'),
        'caret': ('class H(Entity):\n    def f(self):\n        self.x = self.y ^ 1', '^'),
        'unary_minus': ('class H(Entity):\n    def f(self):\n        self.x = -1', '-1'),
        'print': ('class H(Entity):\n    def f(self):\n        print(self.hp)', 'std::cout'),
        'assert': ('class H(Entity):\n    def f(self):\n        assert self.hp >= 0', 'assert('),
        'file': ('class H(Entity):\n    def f(self):\n        f = open("t.txt", "out")', 'std::fstream'),
        'plus_plus': ('class H(Entity):\n    def f(self):\n        self.hp++', 'this->hp++;'),
        'minus_minus': ('class H(Entity):\n    def f(self):\n        self.hp--', 'this->hp--;'),
        'plus_equals': ('class H(Entity):\n    def f(self):\n        self.hp += 10', 'this->hp += 10;'),
        'null': ('class H(Entity):\n    def f(self):\n        if self.t != None:\n            self.hp = 100', 'nullptr'),
        'bool_true': ('class H(Entity):\n    def f(self):\n        self.a = true', 'true'),
        'bool_false': ('class H(Entity):\n    def f(self):\n        self.a = false', 'false'),
        'while_break': ('class H(Entity):\n    def f(self):\n        while self.hp > 0:\n            break', 'break;'),
        'while_continue': ('class H(Entity):\n    def f(self):\n        while self.hp > 0:\n            continue', 'continue;'),
        'for_loop': ('class H(Entity):\n    def f(self, items):\n        for i in items:\n            self:use(i)', 'for (auto& i : items)'),
        'method_call': ('class H(Entity):\n    def f(self):\n        self:heal(10)', 'this.heal(10);'),
        'typed_param': ('class H(Entity):\n    def f(self, x: int, y: str):\n        self.x = x', 'std::string y'),
        'class_no_parent': ('class E:\n    def f(self):\n        self.x = 0', 'class E {'),
        'dict_def': ('SWORD = { "name": "M", "atk": 10 }', 'struct SWORD_t'),
    }
    for name, (code, expected) in tests.items():
        cpp = code if isinstance(code, str) else code
        if isinstance(code, str):
            cpp = compile_text(code)
        assert expected in cpp, f'{name}: {expected} not found'
    print('✓ Компиляция')

def test_indent():
    """Правильные отступы."""
    cpp = compile_text('''class H(Entity):
    def f(self):
        if self.hp > 0:
            self.hp = self.hp - 1
            if self.hp == 0:
                self.alive = false
        else:
            self.hp = 100''')
    assert 'if (this->hp > 0)' in cpp
    assert 'if (this->hp == 0)' in cpp
    assert 'else {' in cpp
    print('✓ Отступы')

def test_error_messages():
    try:
        compile_text('class H(Entity)\n    def f(self):\n        self.x = 0')
        assert False
    except ParseError:
        pass  # любая ошибка парсинга — ок
    
    try:
        compile_text('@load "nonexistent_12345"')
        assert False
    except ParseError as e:
        assert 'не найден' in str(e)
    print('✓ Ошибки')

def test_header():
    cpp = compile_header('HERO = { "hp": 100 }\nclass H(Entity):\n    def f(self):\n        self.x = 0', '/dev/null')
    assert 'void f()' in cpp
    assert '#pragma once' in cpp
    print('✓ Header')

if __name__ == '__main__':
    test_all_tokens()
    test_all_expressions()
    test_all_statements()
    test_compile_all()
    test_indent()
    test_error_messages()
    test_header()
    print(f'\n✓ Все тесты пройдены!')
