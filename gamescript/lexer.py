"""
Лексер GameScript: строка исходного кода → список токенов.

Разбивает исходный код на токены для парсера.
Поддерживает INDENT/DEDENT для отступов.
"""

from typing import List
from .tokens import TokenType, Token


class Lexer:
    """
    Превращает исходный код GameScript в последовательность токенов.
    
    Использование:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
    """
    
    # Ключевые слова языка → соответствующий TokenType
    KEYWORDS = {
        # Управление потоком
        'class':    TokenType.CLASS,
        'def':      TokenType.DEF,
        'pass':     TokenType.PASS,
        'if':       TokenType.IF,
        'else':     TokenType.ELSE,
        'elif':     TokenType.ELIF,
        'while':    TokenType.WHILE,
        'for':      TokenType.FOR,
        'in':       TokenType.IN,
        'return':   TokenType.RETURN,
        'continue': TokenType.CONTINUE,
        'break':    TokenType.BREAK,
        'fn':       TokenType.FN,
        # Типы
        'int':      TokenType.INT,
        'float':    TokenType.FLOAT,
        'str':      TokenType.STR,
        'bool':     TokenType.BOOL,
        'list':     TokenType.LIST,
        'dict':     TokenType.DICT,
        # Логические
        'and':      TokenType.AND,
        'or':       TokenType.OR,
        'not':      TokenType.NOT,
        # Константы
        'None':     TokenType.NONE,
        'true':     TokenType.TRUE,
        'false':    TokenType.FALSE,
        # Встроенные функции
        'print':    TokenType.PRINT,
        'assert':   TokenType.ASSERT,
        'like':     TokenType.LIKE,
        # Файловые операции
        'open':     TokenType.OPEN,
        'read':     TokenType.READ,
        'write':    TokenType.WRITE,
        'close':    TokenType.CLOSE,
    }

    def __init__(self, source: str):
        """
        Args:
            source: исходный код на GameScript
        """
        self.source = source
        self.pos = 0               # текущая позиция в исходнике
        self.line = 1              # текущая строка
        self.col = 1               # текущая колонка
        self.tokens: List[Token] = []
        self.indent_stack = [0]    # стек уровней отступа
        self.at_line_start = True  # флаг начала строки
        self.bracket_depth = 0     # вложенность скобок

    # ===== Утилиты =====

    def current(self) -> str:
        """Возвращает текущий символ или \\0 если конец файла."""
        return self.source[self.pos] if self.pos < len(self.source) else '\0'

    def advance(self) -> str:
        """Сдвигает позицию на один символ вперёд, возвращает его."""
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
        """Подсмотреть n символов вперёд, не сдвигая позицию."""
        return self.source[self.pos:self.pos + n]

    # ===== Отступы =====

    def handle_indent(self):
        """
        Вычисляет отступ текущей строки и генерирует токены INDENT/DEDENT.
        Отступы игнорируются внутри скобок (bracket_depth > 0).
        """
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
            # Отступ уменьшился → один или несколько DEDENT
            while indent < self.indent_stack[-1]:
                self.indent_stack.pop()
                self.tokens.append(Token(TokenType.DEDENT, 'DEDENT', self.line, 1))

        # Пропускаем пробелы начала строки
        while self.pos < len(self.source) and self.source[self.pos] == ' ':
            self.advance()

        self.at_line_start = False

    # ===== Пропуск пробелов и комментариев =====

    def skip_whitespace_and_comments(self):
        """
        Пропускает пробелы, табы, переводы строк (внутри скобок) и комментарии.
        """
        while self.pos < len(self.source):
            c = self.current()
            if c in ' \t\r':
                self.advance()
            elif c == '\n' and self.bracket_depth > 0:
                self.advance()  # внутри скобок переносы строк — просто пробелы
            elif c == '#':
                # Комментарий — до конца строки
                while self.pos < len(self.source) and self.current() != '\n':
                    self.advance()
            else:
                break

    # ===== Чтение литералов =====

    def read_string(self, quote: str) -> str:
        """
        Читает строковый литерал в одинарных или двойных кавычках.
        Поддерживает экранирование: \\n, \\t, \\\", \\'
        """
        self.advance()  # открывающая кавычка
        result = ""
        while self.pos < len(self.source):
            c = self.current()
            if c == quote:
                self.advance()  # закрывающая кавычка
                return result
            elif c == '\\':
                self.advance()
                esc = self.advance()
                result += {'n': '\n', 't': '\t', '"': '"', "'": "'"}.get(esc, esc)
            else:
                result += self.advance()
        return result

    def read_docstring(self, quote: str) -> str:
        """
        Читает док-строку в тройных кавычках: \\\"\\\"\\\"...\\\"\\\"\\\" или '''...'''
        """
        for _ in range(3):
            self.advance()  # открывающие кавычки
        result = ""
        while self.pos < len(self.source):
            if self.peek_str(3) == quote * 3:
                for _ in range(3):
                    self.advance()  # закрывающие кавычки
                return result
            result += self.advance()
        return result

    def read_number(self) -> Token:
        """
        Читает числовой литерал: целый (42) или с плавающей точкой (3.14).
        """
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
        """
        Читает идентификатор или ключевое слово.
        Идентификатор: буква или _, затем буквы, цифры, _
        """
        ident = ""
        while self.pos < len(self.source) and (self.current().isalnum() or self.current() == '_'):
            ident += self.advance()

        # Проверяем, не ключевое ли слово
        kw_type = self.KEYWORDS.get(ident)
        if kw_type:
            return Token(kw_type, ident, self.line, self.col)
        return Token(TokenType.IDENT, ident, self.line, self.col)

    # ===== Главный метод =====

    def tokenize(self) -> List[Token]:
        """
        Разбирает исходный код на токены.
        
        Returns:
            список Token, последний токен всегда EOF
        """
        # Сбрасываем состояние
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

            # Док-строки: \"\"\"...\"\"\" или '''...'''
            if c in '"\'' and self.peek_str(3) in ('"""', "'''"):
                s = self.read_docstring(c)
                self.tokens.append(Token(TokenType.STRING, s, self.line, self.col))

            # Обычные строки: "..." или '...'
            elif c in '"\'':
                s = self.read_string(c)
                self.tokens.append(Token(TokenType.STRING, s, self.line, self.col))

            # Числа
            elif c.isdigit():
                self.tokens.append(self.read_number())

            # Идентификаторы и ключевые слова
            elif c.isalpha() or c == '_':
                self.tokens.append(self.read_ident())

            # Импорты: @load, @load?
            elif c == '@':
                self.advance()
                if self.peek_str(4) == 'load':
                    for _ in range(4):
                        self.advance()
                    if self.current() == '?':
                        self.advance()
                        self.tokens.append(Token(TokenType.AT_LOAD_OPT, '@load?', self.line, self.col))
                    else:
                        self.tokens.append(Token(TokenType.AT_LOAD, '@load', self.line, self.col))

            # Скобки (с отслеживанием вложенности)
            elif c == '{':
                self.tokens.append(Token(TokenType.LBRACE, '{', self.line, self.col))
                self.advance()
                self.bracket_depth += 1
            elif c == '}':
                self.tokens.append(Token(TokenType.RBRACE, '}', self.line, self.col))
                self.advance()
                self.bracket_depth -= 1
            elif c == '(':
                self.tokens.append(Token(TokenType.LPAREN, '(', self.line, self.col))
                self.advance()
                self.bracket_depth += 1
            elif c == ')':
                self.tokens.append(Token(TokenType.RPAREN, ')', self.line, self.col))
                self.advance()
                self.bracket_depth -= 1
            elif c == '[':
                self.tokens.append(Token(TokenType.LBRACKET, '[', self.line, self.col))
                self.advance()
                self.bracket_depth += 1
            elif c == ']':
                self.tokens.append(Token(TokenType.RBRACKET, ']', self.line, self.col))
                self.advance()
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
                self.tokens.append(Token(TokenType.COLON, ':', self.line, self.col))
                self.advance()
            elif c == ',':
                self.tokens.append(Token(TokenType.COMMA, ',', self.line, self.col))
                self.advance()
            elif c == ';':
                self.tokens.append(Token(TokenType.SEMICOLON, ';', self.line, self.col))
                self.advance()
            elif c == '.':
                self.tokens.append(Token(TokenType.DOT, '.', self.line, self.col))
                self.advance()

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
            elif c == '%':
                self.advance()
                if self.current() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.PERCENT_EQUALS, '%=', self.line, self.col))
                else:
                    self.tokens.append(Token(TokenType.PERCENT, '%', self.line, self.col))
            elif c == '^':
                self.advance()
                if self.current() == '=':
                    self.advance()
                    self.tokens.append(Token(TokenType.CARET_EQUALS, '^=', self.line, self.col))
                else:
                    self.tokens.append(Token(TokenType.CARET, '^', self.line, self.col))

            # Неизвестный символ — пропускаем
            else:
                self.advance()

        # В конце файла генерируем оставшиеся DEDENT
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            self.tokens.append(Token(TokenType.DEDENT, 'DEDENT', self.line, 1))

        # Завершающий токен EOF
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.col))
        return self.tokens