"""
Лексер: строка исходного кода → список токенов.
"""

from typing import List
from .tokens import TokenType, Token


class Lexer:
    """Превращает исходный код GameScript в последовательность токенов."""
    
    KEYWORDS = {
        'class': TokenType.CLASS,
        'def': TokenType.DEF,
        'pass': TokenType.PASS,
        'if': TokenType.IF,
        'else': TokenType.ELSE,
        'while': TokenType.WHILE,
        'for': TokenType.FOR,
        'in': TokenType.IN,
        'return': TokenType.RETURN,
        'continue': TokenType.CONTINUE,
        'break': TokenType.BREAK,
        'like': TokenType.LIKE,
        'int': TokenType.INT,
        'float': TokenType.FLOAT,
        'str': TokenType.STR,
        'bool': TokenType.BOOL,
        'list': TokenType.LIST,
        'print': TokenType.PRINT,
        'assert': TokenType.ASSERT,
        'dict': TokenType.DICT,
        'None': TokenType.NONE,
        'true': TokenType.TRUE,
        'false': TokenType.FALSE,
        'and': TokenType.AND,
        'or': TokenType.OR,
        'not': TokenType.NOT,
        'elif': TokenType.ELIF,
    }

    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.col = 1
        self.tokens: List[Token] = []
        self.indent_stack = [0]  # стек уровней отступа
        self.at_line_start = True  # начало строки
        self.bracket_depth = 0
    
    def compute_indent(self) -> int:
        """Считает количество пробелов в начале строки."""
        indent = 0
        pos = self.pos
        while pos < len(self.source) and self.source[pos] == ' ':
            indent += 1
            pos += 1
        return indent
    
    def handle_indent(self):
        """Вычисляет отступ текущей строки и генерирует INDENT/DEDENT."""
        if not self.at_line_start or self.bracket_depth > 0:
            return
        # Считаем пробелы в начале строки
        indent = 0
        pos = self.pos
        while pos < len(self.source) and self.source[pos] == ' ':
            indent += 1
            pos += 1
        
        current_indent = self.indent_stack[-1]
        
        if indent > current_indent:
            # Отступ увеличился → INDENT
            self.indent_stack.append(indent)
            self.tokens.append(Token(TokenType.INDENT, 'INDENT', self.line, 1))
        elif indent < current_indent:
            # Отступ уменьшился → DEDENT(ы)
            while indent < self.indent_stack[-1]:
                self.indent_stack.pop()
                self.tokens.append(Token(TokenType.DEDENT, 'DEDENT', self.line, 1))
        
        # Пропускаем пробелы
        while self.pos < len(self.source) and self.source[self.pos] == ' ':
            self.advance()
        
        self.at_line_start = False

    def current(self) -> str:
        return self.source[self.pos] if self.pos < len(self.source) else '\0'

    def advance(self) -> str:
        c = self.current()
        self.pos += 1
        if c == '\n':
            self.line += 1
            self.col = 1
            self.at_line_start = True
        else:
            self.col += 1
        return c

    def peek_str(self, n: int) -> str:
        return self.source[self.pos:self.pos + n]

    def skip_whitespace_and_comments(self):
        while self.pos < len(self.source):
            c = self.current()
            if c in ' \t\r':
                self.advance()
            elif c == '#':
                while self.pos < len(self.source) and self.current() != '\n':
                    self.advance()
            else:
                break

    def read_string(self, quote: str) -> str:
        self.advance()
        result = ""
        while self.pos < len(self.source):
            c = self.current()
            if c == quote:
                self.advance()
                return result
            elif c == '\\':
                self.advance()
                esc = self.advance()
                result += {'n': '\n', 't': '\t', '"': '"', "'": "'"}.get(esc, esc)
            else:
                result += self.advance()
        return result

    def read_docstring(self, quote: str) -> str:
        for _ in range(3):
            self.advance()
        result = ""
        while self.pos < len(self.source):
            if self.peek_str(3) == quote * 3:
                for _ in range(3):
                    self.advance()
                return result
            result += self.advance()
        return result

    def read_number(self) -> Token:
        num = ""
        while self.pos < len(self.source) and self.current().isdigit():
            num += self.advance()
        if self.current() == '.':
            num += self.advance()
            while self.pos < len(self.source) and self.current().isdigit():
                num += self.advance()
            return Token(TokenType.NUMBER, float(num), self.line, self.col)
        return Token(TokenType.NUMBER, int(num), self.line, self.col)

    def read_ident(self) -> Token:
        ident = ""
        while self.pos < len(self.source) and (self.current().isalnum() or self.current() == '_'):
            ident += self.advance()
        kw_type = self.KEYWORDS.get(ident)
        if kw_type:
            return Token(kw_type, ident, self.line, self.col)
        return Token(TokenType.IDENT, ident, self.line, self.col)

    def tokenize(self) -> List[Token]:
        # Начальный отступ
        self.indent_stack = [0]
        self.at_line_start = True
        
        while self.pos < len(self.source):
            # В начале строки — обрабатываем отступ
            if self.at_line_start:
                self.handle_indent()
            
            self.skip_whitespace_and_comments()
            if self.pos >= len(self.source):
                break
    
            c = self.current()
            
            # Док-строки
            if c in '"\'' and self.peek_str(3) in ('"""', "'''"):
                s = self.read_docstring(c)
                self.tokens.append(Token(TokenType.STRING, s, self.line, self.col))
            # Обычные строки
            elif c in '"\'':
                s = self.read_string(c)
                self.tokens.append(Token(TokenType.STRING, s, self.line, self.col))
            
            # Числа
            elif c.isdigit():
                self.tokens.append(self.read_number())
            # Идентификаторы
            elif c.isalpha() or c == '_':
                self.tokens.append(self.read_ident())
            # Импорты
            elif c == '@':
                self.advance()
                if self.peek_str(4) == 'load':
                    for _ in range(4): self.advance()
                    if self.current() == '?':
                        self.advance()
                        self.tokens.append(Token(TokenType.AT_LOAD_OPT, '@load?', self.line, self.col))
                    else:
                        self.tokens.append(Token(TokenType.AT_LOAD, '@load', self.line, self.col))
            # Скобки
            elif c == '{':
                self.tokens.append(Token(TokenType.LBRACE, '{', self.line, self.col)); self.advance()
                self.bracket_depth += 1
            elif c == '}':
                self.tokens.append(Token(TokenType.RBRACE, '}', self.line, self.col)); self.advance()
                self.bracket_depth -= 1
            elif c == '(':
                self.tokens.append(Token(TokenType.LPAREN, '(', self.line, self.col)); self.advance()
                self.bracket_depth += 1
            elif c == ')':
                self.tokens.append(Token(TokenType.RPAREN, ')', self.line, self.col)); self.advance()
                self.bracket_depth -= 1
            elif c == '[':
                self.tokens.append(Token(TokenType.LBRACKET, '[', self.line, self.col)); self.advance()
                self.bracket_depth += 1
            elif c == ']':
                self.tokens.append(Token(TokenType.RBRACKET, ']', self.line, self.col)); self.advance()
                self.bracket_depth -= 1
            # Операторы сравнения
            elif c == '<':
                self.advance()
                if self.current() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.LESS_EQUALS, '<=', self.line, self.col))
                else:
                    self.tokens.append(Token(TokenType.LESS, '<', self.line, self.col))
            elif c == '>':
                self.advance()
                if self.current() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.GREATER_EQUALS, '>=', self.line, self.col))
                else:
                    self.tokens.append(Token(TokenType.GREATER, '>', self.line, self.col))
            # Разделители
            elif c == ':':
                self.tokens.append(Token(TokenType.COLON, ':', self.line, self.col)); self.advance()
            elif c == ',':
                self.tokens.append(Token(TokenType.COMMA, ',', self.line, self.col)); self.advance()
            elif c == ';':
                self.tokens.append(Token(TokenType.SEMICOLON, ';', self.line, self.col)); self.advance()
            elif c == '.':
                self.tokens.append(Token(TokenType.DOT, '.', self.line, self.col)); self.advance()
            # Операторы
            elif c == '=':
                self.advance()
                if self.current() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.EQUALS_EQUALS, '==', self.line, self.col))
                else:
                    self.tokens.append(Token(TokenType.EQUALS, '=', self.line, self.col))
            elif c == '!':
                self.advance()
                if self.current() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.NOT_EQUALS, '!=', self.line, self.col))
            elif c == '+':
                self.advance()
                if self.current() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.PLUS_EQUALS, '+=', self.line, self.col))
                elif self.current() == '+':
                    self.advance()
                    self.tokens.append(Token(TokenType.PLUS_PLUS, '++', self.line, self.col))
                else:
                    self.tokens.append(Token(TokenType.PLUS, '+', self.line, self.col))
            elif c == '-':
                self.advance()
                if self.current() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.MINUS_EQUALS, '-=', self.line, self.col))
                elif self.current() == '-':
                    self.advance()
                    self.tokens.append(Token(TokenType.MINUS_MINUS, '--', self.line, self.col))
                else:
                    self.tokens.append(Token(TokenType.MINUS, '-', self.line, self.col))
            elif c == '*':
                self.advance()
                if self.current() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.STAR_EQUALS, '*=', self.line, self.col))
                else:
                    self.tokens.append(Token(TokenType.STAR, '*', self.line, self.col))
            elif c == '/':
                self.advance()
                if self.current() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.SLASH_EQUALS, '/=', self.line, self.col))
                else:
                    self.tokens.append(Token(TokenType.SLASH, '/', self.line, self.col))
            else:
                self.advance()
    
        # В конце генерируем оставшиеся DEDENT
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, 'DEDENT', self.line, 1))
        
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return self.tokens