"""
GameScript — DSL для геймдева, компилируется в C++.

Использование:
    from gamescript import compile_file
    compile_file("game.gs", "output.cpp")
"""

from .compiler import compile_file, compile_text
from .tokens import TokenType, Token
from .lexer import Lexer
from .parser import Parser
from .codegen_cpp import CppCodeGen

__version__ = "0.7.1"
__all__ = ["compile_file", "compile_text", "Lexer", "Parser", "CppCodeGen"]