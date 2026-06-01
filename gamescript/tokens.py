"""
Типы токенов и класс Token для GameScript.

Все возможные токены, которые лексер может выделить из исходного кода.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TokenType(Enum):
    """Все возможные типы токенов в GameScript."""
    
    # ===== Идентификаторы и литералы =====
    IDENT = "IDENT"            # имя переменной, класса, метода
    STRING = "STRING"          # "строка", 'строка', """док-строка"""
    NUMBER = "NUMBER"          # 42 или 3.14
    
    # ===== Скобки =====
    LBRACE = "{"               # {
    RBRACE = "}"               # }
    LPAREN = "("               # (
    RPAREN = ")"               # )
    LBRACKET = "["             # [
    RBRACKET = "]"             # ]
    
    # ===== Разделители =====
    COLON = ":"                # :
    COMMA = ","                # ,
    SEMICOLON = ";"            # ;
    DOT = "."                  # .
    
    # ===== Присваивание =====
    EQUALS = "="               # =
    PLUS_EQUALS = "+="         # +=
    MINUS_EQUALS = "-="        # -=
    STAR_EQUALS = "*="         # *=
    SLASH_EQUALS = "/="        # /=
    
    # ===== Сравнение =====
    EQUALS_EQUALS = "=="       # ==
    NOT_EQUALS = "!="          # !=
    LESS = "<"                 # <
    GREATER = ">"              # >
    LESS_EQUALS = "<="         # <=
    GREATER_EQUALS = ">="      # >=
    PERCENT_EQUALS = "%="      # %=
    CARET = "^"                # ^
    CARET_EQUALS = "^="        # ^=
    
    # ===== Арифметика =====
    PLUS = "+"                 # +
    MINUS = "-"                # -
    STAR = "*"                 # *
    SLASH = "/"                # /
    PERCENT = "%"              # %
    PLUS_PLUS = "++"           # ++ (инкремент)
    MINUS_MINUS = "--"         # -- (декремент)
    
    # ===== Ключевые слова =====
    CLASS = "CLASS"            # class
    DEF = "DEF"                # def
    PASS = "PASS"              # pass
    IF = "IF"                  # if
    ELSE = "ELSE"              # else
    ELIF = "ELIF"              # elif
    WHILE = "WHILE"            # while
    FOR = "FOR"                # for
    IN = "IN"                  # in
    RETURN = "RETURN"          # return
    CONTINUE = "CONTINUE"      # continue
    BREAK = "BREAK"            # break
    FN = "FN"                  # fn (лямбда)
    LIKE = "LIKE"              # like (псевдоним)
    PRINT = "PRINT"            # print (отладка)
    ASSERT = "ASSERT"          # assert (проверка)
    
    # ===== Логические операторы =====
    AND = "AND"                # and
    OR = "OR"                  # or
    NOT = "NOT"                # not
    
    # ===== Импорты =====
    AT_LOAD = "@load"          # @load "file"
    AT_LOAD_OPT = "@load?"     # @load? "file" (опциональный)
    
    # ===== Встроенные типы =====
    INT = "INT"                # int
    FLOAT = "FLOAT"            # float
    STR = "STR"                # str
    BOOL = "BOOL"              # bool
    LIST = "LIST"              # list
    DICT = "DICT"              # dict
    
    # ===== Файловые операции =====
    OPEN = "OPEN"              # open()
    READ = "READ"              # read()
    WRITE = "WRITE"            # write()
    CLOSE = "CLOSE"            # close()
    
    # ===== Константы =====
    NONE = "NONE"              # None
    TRUE = "TRUE"              # true
    FALSE = "FALSE"            # false
    
    # ===== Отступы =====
    INDENT = "INDENT"          # увеличение отступа
    DEDENT = "DEDENT"          # уменьшение отступа
    NEWLINE = "NEWLINE"        # новая строка
    
    # ===== Служебные =====
    COMMENT = "COMMENT"        # комментарий (пропускается)
    EOF = "EOF"                # конец файла


@dataclass
class Token:
    """
    Один токен после лексинга.
    
    Атрибуты:
        type:  тип токена (TokenType)
        value: значение токена (строка, число, оператор)
        line:  номер строки в исходном коде
        col:   номер колонки в исходном коде
    """
    type: TokenType
    value: Any
    line: int
    col: int
    
    def __repr__(self) -> str:
        return f"Token({self.type}, {repr(self.value)}, line={self.line}, col={self.col})"