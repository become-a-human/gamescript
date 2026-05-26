"""
Тесты лексера.

Проверяют, что лексер правильно разбивает исходный код на токены.
"""

from gamescript.lexer import Lexer
from gamescript.tokens import TokenType


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
    assert tokens[0].type == TokenType.NUMBER
    assert tokens[0].value == 42
    assert tokens[1].type == TokenType.NUMBER
    assert tokens[1].value == 3.14


def test_strings():
    """Строки в кавычках."""
    lexer = Lexer('"hello" \'world\'')
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "hello"
    assert tokens[1].type == TokenType.STRING
    assert tokens[1].value == "world"


def test_docstring():
    """Тройные кавычки — один токен."""
    lexer = Lexer('"""Главный герой"""')
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "Главный герой"


def test_docstring_single_quotes():
    """Тройные одинарные кавычки."""
    lexer = Lexer("'''Главный герой'''")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.STRING
    assert tokens[0].value == "Главный герой"


def test_keywords():
    """Ключевые слова."""
    lexer = Lexer("class def pass if else while for in return continue break true false None")
    tokens = lexer.tokenize()
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert types == [
        TokenType.CLASS, TokenType.DEF, TokenType.PASS,
        TokenType.IF, TokenType.ELSE, TokenType.WHILE, TokenType.FOR,
        TokenType.IN, TokenType.RETURN, TokenType.CONTINUE, TokenType.BREAK,
        TokenType.TRUE, TokenType.FALSE, TokenType.NONE,
    ]


def test_type_constructors():
    """Конструкторы типов."""
    lexer = Lexer("int float str bool list dict")
    tokens = lexer.tokenize()
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert types == [
        TokenType.INT, TokenType.FLOAT, TokenType.STR,
        TokenType.BOOL, TokenType.LIST, TokenType.DICT,
    ]


def test_operators():
    """Операторы и скобки."""
    lexer = Lexer("{}() : , ; . = == != + - * /")
    tokens = lexer.tokenize()
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    expected = [
        TokenType.LBRACE, TokenType.RBRACE,
        TokenType.LPAREN, TokenType.RPAREN,
        TokenType.COLON, TokenType.COMMA, TokenType.SEMICOLON,
        TokenType.DOT, TokenType.EQUALS, TokenType.EQUALS_EQUALS,
        TokenType.NOT_EQUALS,
        TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH,
    ]
    assert types == expected


def test_comparison_operators():
    """<, >, <=, >="""
    lexer = Lexer("< > <= >=")
    tokens = lexer.tokenize()
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert types == [
        TokenType.LESS, TokenType.GREATER,
        TokenType.LESS_EQUALS, TokenType.GREATER_EQUALS,
    ]


def test_compound_assignment_tokens():
    """+=, -=, *=, /="""
    lexer = Lexer("+= -= *= /=")
    tokens = lexer.tokenize()
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert types == [
        TokenType.PLUS_EQUALS, TokenType.MINUS_EQUALS,
        TokenType.STAR_EQUALS, TokenType.SLASH_EQUALS,
    ]


def test_comment():
    """Комментарии пропускаются."""
    lexer = Lexer("# это комментарий\n42")
    tokens = lexer.tokenize()
    assert tokens[0].type == TokenType.NUMBER
    assert tokens[0].value == 42


def test_imports_load():
    """@load и @load?"""
    lexer = Lexer('@load "hero.gs"\n@load? "optional.gs"')
    tokens = lexer.tokenize()
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert types == [
        TokenType.AT_LOAD, TokenType.STRING,
        TokenType.AT_LOAD_OPT, TokenType.STRING,
    ]


def test_imports_grab():
    """~grab и ~grab? с like и угловыми скобками"""
    lexer = Lexer('~grab <Hero> like <Player>, <Sword>')
    tokens = lexer.tokenize()
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert types == [
        TokenType.TILDE_GRAB,
        TokenType.LANGLE, TokenType.IDENT, TokenType.RANGLE,
        TokenType.LIKE,
        TokenType.LANGLE, TokenType.IDENT, TokenType.RANGLE,
        TokenType.COMMA,
        TokenType.LANGLE, TokenType.IDENT, TokenType.RANGLE,
    ]


def test_imports_link():
    """&link и &link?"""
    lexer = Lexer('&link <on_create> like <init>\n&link? <rumble>')
    tokens = lexer.tokenize()
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert types == [
        TokenType.AMP_LINK,
        TokenType.LANGLE, TokenType.IDENT, TokenType.RANGLE,
        TokenType.LIKE,
        TokenType.LANGLE, TokenType.IDENT, TokenType.RANGLE,
        TokenType.AMP_LINK_OPT,
        TokenType.LANGLE, TokenType.IDENT, TokenType.RANGLE,
    ]


def test_dict_syntax():
    """Полный словарь."""
    source = '''
HERO = {
    "name": str("Артур"),
    "hp": int(100),
}
'''
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert TokenType.IDENT in types
    assert TokenType.LBRACE in types
    assert TokenType.RBRACE in types


def test_full_import_example():
    """Реальный пример импортов."""
    source = '''
@load "hero.gs"
@load? "gamepad.gs"
~grab <Hero> like <Player>, <Dragon> like <Boss>
&link <on_create> like <init>, <on_turn>
'''
    lexer = Lexer(source)
    tokens = lexer.tokenize()
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert TokenType.AT_LOAD in types
    assert TokenType.AT_LOAD_OPT in types
    assert TokenType.TILDE_GRAB in types
    assert TokenType.AMP_LINK in types
    assert TokenType.LIKE in types
    assert TokenType.LANGLE in types
    assert TokenType.RANGLE in types


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
    test_compound_assignment_tokens()
    test_comment()
    test_imports_load()
    test_imports_grab()
    test_imports_link()
    test_dict_syntax()
    test_full_import_example()
    print("✓ Все тесты лексера пройдены!")