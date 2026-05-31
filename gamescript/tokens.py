"""
Типы токенов и класс Token.

Все возможные токены, которые лексер может выделить из исходного кода GameScript.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class TokenType(Enum):
    """Все возможные типы токенов в GameScript."""
    
    # Идентификаторы и литералы
    IDENT = "IDENT"            # имя переменной, класса, метода
    STRING = "STRING"          # "строка" или 'строка' или """док-строка"""
    NUMBER = "NUMBER"          # 42 или 3.14
    
    # Скобки
    LBRACE = "{"               # {
    RBRACE = "}"               # }
    LPAREN = "("               # (
    RPAREN = ")"               # )
    LBRACKET = "["             # [
    RBRACKET = "]"             # ]
    
    # Разделители
    COLON = ":"                # :
    COMMA = ","                # ,
    SEMICOLON = ";"            # ;
    DOT = "."                  # .
    
    # Операторы присваивания
    EQUALS = "="               # =
    PLUS_EQUALS = "+="         # +=
    MINUS_EQUALS = "-="        # -=
    STAR_EQUALS = "*="         # *=
    SLASH_EQUALS = "/="        # /=
    
    # Операторы сравнения
    EQUALS_EQUALS = "=="       # ==
    NOT_EQUALS = "!="          # !=
    LESS = "<"                 # <
    GREATER = ">"              # >
    LESS_EQUALS = "<="         # <=
    GREATER_EQUALS = ">="      # >=
    
    # Арифметические операторы
    PLUS = "+"                 # +
    MINUS = "-"                # -
    STAR = "*"                 # *
    SLASH = "/"                # /
    PLUS_PLUS = "++"           # ++
    MINUS_MINUS = "--"         # --
    
    # Ключевые слова
    CLASS = "CLASS"            # class
    DEF = "DEF"                # def
    PASS = "PASS"              # pass
    IF = "IF"                  # if
    ELSE = "ELSE"              # else
    WHILE = "WHILE"            # while
    FOR = "FOR"                # for
    IN = "IN"                  # in
    RETURN = "RETURN"          # return
    CONTINUE = "CONTINUE"      # continue
    BREAK = "BREAK"            # break
    LIKE = "LIKE"              # like
    PRINT = "PRINT"            # print
    ASSERT = "ASSERT"          # assert
    
    # Импорты
    AT_LOAD = "@load"          # @load "file"
    AT_LOAD_OPT = "@load?"     # @load? "file" (опциональный)
    
    # Встроенные типы
    INT = "INT"                # int()
    FLOAT = "FLOAT"            # float()
    STR = "STR"                # str()
    BOOL = "BOOL"              # bool()
    LIST = "LIST"              # list()
    DICT = "DICT"              # dict()
    AND = "AND"                # and
    OR = "OR"                  # or
    NOT = "NOT"                # not
    ELIF = "ELIF"              # elif
    FN = "FN"                  # fn
    
    
    # Константы
    NONE = "NONE"              # None
    TRUE = "TRUE"              # true
    FALSE = "FALSE"            # false
    
    # Служебные
    COMMENT = "COMMENT"        # комментарий (пропускается)
    EOF = "EOF"                # конец файла

    INDENT = "INDENT"          # indent
    DEDENT = "DEDENT"          # dedent
    NEWLINE = "NEWLINE"        # newline

@dataclass
class Token:
    """Один токен после лексинга."""
    type: TokenType
    value: Any
    line: int
    col: int
    
    def __repr__(self):
        return f"Token({self.type}, {repr(self.value)}, line={self.line}, col={self.col})"