"""
Тесты лексера GameScript.

Проверяют, что лексер правильно разбивает исходный код на токены.
"""

from gamescript.lexer import Lexer
from gamescript.tokens import TokenType


# ===== Базовые токены =====

def test_empty():
    """Пустой файл — только EOF."""
    lexer = Lexer("")
    tokens = lexer.tokenize()
    assert len(tokens) == 1
    assert tokens[0].type == TokenType.EOF


def test_numbers():
    """Целые и дробные числа."""
    lexer = Lexer("42 3.14")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.NUMBER and tokens[0].value == 42
    assert tokens[1].type == TokenType.NUMBER and tokens[1].value == 3.14


def test_strings():
    """Строки в одинарных и двойных кавычках."""
    lexer = Lexer('"hello" \'world\'')
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.STRING and tokens[0].value == "hello"
    assert tokens[1].type == TokenType.STRING and tokens[1].value == "world"


def test_docstring():
    """Тройные двойные кавычки."""
    lexer = Lexer('"""Главный герой"""')
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.STRING and tokens[0].value == "Главный герой"


def test_docstring_single_quotes():
    """Тройные одинарные кавычки."""
    lexer = Lexer("'''Главный герой'''")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.STRING and tokens[0].value == "Главный герой"


# ===== Ключевые слова =====

def test_keywords():
    """Все ключевые слова распознаются."""
    lexer = Lexer("class def pass if else elif while for in return continue break "
                  "true false None not and or print assert fn like "
                  "open read write close")
    tokens = lexer.tokenize()
    types = [t.type for t in tokens if t.type not in (TokenType.EOF, TokenType.INDENT, TokenType.DEDENT)]
    assert types == [
        TokenType.CLASS, TokenType.DEF, TokenType.PASS,
        TokenType.IF, TokenType.ELSE, TokenType.ELIF,
        TokenType.WHILE, TokenType.FOR, TokenType.IN, TokenType.RETURN,
        TokenType.CONTINUE, TokenType.BREAK,
        TokenType.TRUE, TokenType.FALSE, TokenType.NONE,
        TokenType.NOT, TokenType.AND, TokenType.OR,
        TokenType.PRINT, TokenType.ASSERT, TokenType.FN, TokenType.LIKE,
        TokenType.OPEN, TokenType.READ, TokenType.WRITE, TokenType.CLOSE,
    ]


def test_type_constructors():
    """Встроенные типы."""
    lexer = Lexer("int float str bool list dict")
    types = [t.type for t in lexer.tokenize() if t.type not in (TokenType.EOF, TokenType.INDENT, TokenType.DEDENT)]
    assert types == [TokenType.INT, TokenType.FLOAT, TokenType.STR, TokenType.BOOL, TokenType.LIST, TokenType.DICT]


# ===== Операторы =====

def test_operators():
    """Базовые операторы и разделители."""
    lexer = Lexer("{}()[] : , ; . = == != + - * /")
    types = [t.type for t in lexer.tokenize() if t.type not in (TokenType.EOF, TokenType.INDENT, TokenType.DEDENT)]
    assert types == [
        TokenType.LBRACE, TokenType.RBRACE,
        TokenType.LPAREN, TokenType.RPAREN,
        TokenType.LBRACKET, TokenType.RBRACKET,
        TokenType.COLON, TokenType.COMMA, TokenType.SEMICOLON, TokenType.DOT,
        TokenType.EQUALS, TokenType.EQUALS_EQUALS, TokenType.NOT_EQUALS,
        TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH,
    ]


def test_comparison_operators():
    """Операторы сравнения."""
    lexer = Lexer("< > <= >=")
    types = [t.type for t in lexer.tokenize() if t.type not in (TokenType.EOF, TokenType.INDENT, TokenType.DEDENT)]
    assert types == [TokenType.LESS, TokenType.GREATER, TokenType.LESS_EQUALS, TokenType.GREATER_EQUALS]


def test_compound_assignment():
    """Составные присваивания."""
    lexer = Lexer("+= -= *= /=")
    types = [t.type for t in lexer.tokenize() if t.type not in (TokenType.EOF, TokenType.INDENT, TokenType.DEDENT)]
    assert types == [TokenType.PLUS_EQUALS, TokenType.MINUS_EQUALS, TokenType.STAR_EQUALS, TokenType.SLASH_EQUALS]


def test_percent_caret():
    lexer = Lexer("% %= ^ ^=")
    types = [t.type for t in lexer.tokenize() if t.type not in (TokenType.EOF, TokenType.INDENT, TokenType.DEDENT)]
    assert types == [TokenType.PERCENT, TokenType.PERCENT_EQUALS, TokenType.CARET, TokenType.CARET_EQUALS]


def test_increment_decrement():
    """Инкремент и декремент."""
    lexer = Lexer("++ --")
    types = [t.type for t in lexer.tokenize() if t.type not in (TokenType.EOF, TokenType.INDENT, TokenType.DEDENT)]
    assert types == [TokenType.PLUS_PLUS, TokenType.MINUS_MINUS]


# ===== Прочее =====

def test_comment():
    """Комментарии пропускаются."""
    lexer = Lexer("# комментарий\n42")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.NUMBER and tokens[0].value == 42


def test_imports():
    """@load и @load?"""
    lexer = Lexer('@load "hero.gs"\n@load? "optional.gs"')
    tokens = lexer.tokenize()
    types = [t.type for t in tokens if t.type not in (TokenType.EOF, TokenType.INDENT, TokenType.DEDENT)]
    assert types == [TokenType.AT_LOAD, TokenType.STRING, TokenType.AT_LOAD_OPT, TokenType.STRING]


def test_like_keyword():
    """like после @load."""
    lexer = Lexer('@load "hero" like "Player"')
    types = [t.type for t in lexer.tokenize() if t.type not in (TokenType.EOF, TokenType.INDENT, TokenType.DEDENT)]
    assert types == [TokenType.AT_LOAD, TokenType.STRING, TokenType.LIKE, TokenType.STRING]


def test_not_operator():
    """Унарный not."""
    lexer = Lexer("not self.is_alive")
    types = [t.type for t in lexer.tokenize() if t.type not in (TokenType.EOF, TokenType.INDENT, TokenType.DEDENT)]
    assert types == [TokenType.NOT, TokenType.IDENT, TokenType.DOT, TokenType.IDENT]


# ===== Отступы =====

def test_indent_dedent():
    """Блоки с отступами генерируют INDENT/DEDENT."""
    source = '''class Hero:
    def on_create(self):
        self.hp = 100'''
    lexer = Lexer(source)
    types = [t.type for t in lexer.tokenize() if t.type not in (TokenType.EOF,)]
    assert types == [
        TokenType.CLASS, TokenType.IDENT, TokenType.COLON,
        TokenType.INDENT,
        TokenType.DEF, TokenType.IDENT, TokenType.LPAREN, TokenType.IDENT, TokenType.RPAREN, TokenType.COLON,
        TokenType.INDENT,
        TokenType.IDENT, TokenType.DOT, TokenType.IDENT, TokenType.EQUALS, TokenType.NUMBER,
        TokenType.DEDENT,
        TokenType.DEDENT,
    ]


def test_bracket_depth_suppresses_indent():
    """Внутри скобок отступы игнорируются."""
    source = '''HERO = {
    "hp": 100,
    "mp": 50
}'''
    lexer = Lexer(source)
    types = [t.type for t in lexer.tokenize() if t.type not in (TokenType.EOF, TokenType.INDENT, TokenType.DEDENT)]
    assert types == [
        TokenType.IDENT, TokenType.EQUALS, TokenType.LBRACE,
        TokenType.STRING, TokenType.COLON, TokenType.NUMBER, TokenType.COMMA,
        TokenType.STRING, TokenType.COLON, TokenType.NUMBER,
        TokenType.RBRACE,
    ]


def test_dict_syntax():
    """Словарь с отступами внутри."""
    source = '''HERO = { "name": "Артур", "hp": 100 }'''
    lexer = Lexer(source)
    types = [t.type for t in lexer.tokenize() if t.type not in (TokenType.EOF, TokenType.INDENT, TokenType.DEDENT)]
    assert TokenType.IDENT in types and TokenType.LBRACE in types and TokenType.RBRACE in types


def test_brackets():
    """Квадратные скобки."""
    lexer = Lexer("[ ]")
    types = [t.type for t in lexer.tokenize() if t.type not in (TokenType.EOF, TokenType.INDENT, TokenType.DEDENT)]
    assert types == [TokenType.LBRACKET, TokenType.RBRACKET]


if __name__ == "__main__":
    test_empty()
    test_numbers()
    test_strings()
    test_docstring()
    test_docstring_single_quotes()
    test_keywords()
    test_type_constructors()
    test_operators()
    test_comparison_operators()
    test_compound_assignment()
    test_percent_caret()
    test_increment_decrement()
    test_comment()
    test_imports()
    test_like_keyword()
    test_not_operator()
    test_indent_dedent()
    test_bracket_depth_suppresses_indent()
    test_dict_syntax()
    test_brackets()
    print("✓ Все тесты лексера пройдены!")