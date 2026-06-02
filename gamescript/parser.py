"""
Парсер GameScript: список токенов → AST.

Реализует рекурсивный спуск по грамматике GameScript.
Поддерживает INDENT/DEDENT для блоков кода.

Грамматика:
    program        = statement*
    statement      = import | class_def | method_def | if_stmt | while_stmt
                   | for_stmt | return_stmt | assign_or_expr | pass
                   | print_stmt | assert_stmt | file_op | CONTINUE | BREAK
    import         = "@load" | "@load?" STRING ["like" STRING]
    class_def      = "class" IDENT ["(" IDENT ")"] ":" [STRING] INDENT (method_def)* DEDENT
    method_def     = "def" IDENT "(" [param ("," param)*] ")" ":" INDENT statement* DEDENT
    param          = IDENT [":" type] | "*" IDENT
    type           = IDENT | "int" | "float" | "str" | "bool"
    block          = INDENT statement* DEDENT
    if_stmt        = "if" expression ":" block ["elif" expression ":" block]* ["else" ":" block]
    while_stmt     = "while" expression ":" block
    for_stmt       = "for" IDENT "in" expression ":" block
    return_stmt    = "return" [expression]
    assign_or_expr = IDENT ("." IDENT)* (("=" | "+=" | "-=" | "*=" | "/=") expression)?
    expression     = logic
    logic          = comparison (("and" | "or") comparison)*
    comparison     = addition (("==" | "!=" | "<" | ">" | "<=" | ">=") addition)*
    addition       = multiplication (("+" | "-") multiplication)*
    multiplication = unary (("*" | "/") unary)*
    unary          = ("not" | "++" | "--") primary | primary
    primary        = IDENT ("." IDENT)* [":" IDENT "(" [expression ("," expression)*] ")"]
                   | NUMBER | STRING | "true" | "false" | "None"
                   | "{" pair* "}" | "[" expression* "]" | "(" expression ")"
                   | type_call | "fn" lambda_def | file_op
    type_call      = ("int" | "float" | "str" | "bool" | "list" | "dict") "(" [value ("," value)*] ")"
    pair           = STRING ":" value (",")?
    value          = "{" pair* "}" | "[" value* "]" | type_call | STRING | NUMBER | "None" | "true" | "false" | IDENT
    lambda_def     = "(" [param ("," param)*] ")" ":" (expression | block)
"""

from typing import List, Optional
from .tokens import TokenType, Token
from .ast_nodes import *


class ParseError(SyntaxError):
    """Ошибка парсинга с указанием строки и колонки."""
    def __init__(self, msg: str, line: int, col: int, context: str = ""):
        self.line = line
        self.col = col
        self.context = context
        pointer = " " * (col - 1) + "^"
        super().__init__(f"{msg}\n  строка {line}, колонка {col}\n  {context}\n  {pointer}")


class Parser:
    """
    Парсер GameScript.
    Принимает список токенов от Lexer, возвращает AST (Program).
    Использует рекурсивный спуск: один метод на каждое правило грамматики.
    """

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    # ===== Утилиты =====

    def peek(self) -> Token:
        """Подсмотреть текущий токен, не сдвигая позицию."""
        return self.tokens[self.pos]

    def advance(self) -> Token:
        """Скушать текущий токен и сдвинуться вперёд."""
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def expect(self, ttype: TokenType) -> Token:
        """
        Скушать токен конкретного типа.
        Если токен другого типа — бросить ParseError.
        """
        t = self.advance()
        if t.type != ttype:
            raise ParseError(
                f"Ожидался {ttype.value}, получен {t.type.value} ({t.value})",
                t.line, t.col
            )
        return t

    def _is_assignment(self) -> bool:
        """
        Проверяет, является ли следующий за текущим токеном
        оператор присваиванием. Используется чтобы отличить
        `open = 1` от `open("file.txt")`.
        """
        pos = self.pos
        self.advance()
        result = self.peek().type in (
            TokenType.EQUALS, TokenType.PLUS_EQUALS,
            TokenType.MINUS_EQUALS, TokenType.DOT
        )
        self.pos = pos
        return result

    # ===== Главный метод =====

    def parse(self) -> Program:
        """Разбирает всю программу. Точка входа парсера."""
        stmts = []
        while self.peek().type != TokenType.EOF:
            stmts.append(self._parse_statement())
        return Program(stmts)

    # ===== Инструкции =====

    def _parse_statement(self) -> ASTNode:
        """
        Одна инструкция верхнего уровня или внутри блока.
        Диспетчер: смотрит на первый токен и вызывает нужный метод.
        """
        t = self.peek()

        # Импорты
        if t.type == TokenType.AT_LOAD:
            return self._parse_load()
        elif t.type == TokenType.AT_LOAD_OPT:
            return self._parse_load()

        # Определения
        elif t.type == TokenType.CLASS:
            return self._parse_class()
        elif t.type == TokenType.DEF:
            return self._parse_method()

        # Управляющие конструкции
        elif t.type == TokenType.IF:
            return self._parse_if()
        elif t.type == TokenType.WHILE:
            return self._parse_while()
        elif t.type == TokenType.FOR:
            return self._parse_for()
        elif t.type == TokenType.RETURN:
            return self._parse_return()

        # Короткие инструкции
        elif t.type == TokenType.CONTINUE:
            self.advance()
            return ContinueStmt()
        elif t.type == TokenType.BREAK:
            self.advance()
            return BreakStmt()
        elif t.type == TokenType.PASS:
            self.advance()
            return None

        # Отступы (обрабатываются в _parse_block, здесь просто пропускаем)
        elif t.type == TokenType.INDENT:
            self.advance()
            return None
        elif t.type == TokenType.DEDENT:
            self.advance()
            return None

        # Встроенные функции (могут быть присваиванием)
        elif t.type == TokenType.PRINT:
            if self._is_assignment():
                return self._parse_ident_stmt()
            return self._parse_print()
        elif t.type == TokenType.ASSERT:
            if self._is_assignment():
                return self._parse_ident_stmt()
            return self._parse_assert()
        elif t.type == TokenType.OPEN:
            if self._is_assignment():
                return self._parse_ident_stmt()
            return self._parse_file_open()
        elif t.type == TokenType.READ:
            if self._is_assignment():
                return self._parse_ident_stmt()
            return self._parse_file_read()
        elif t.type == TokenType.WRITE:
            if self._is_assignment():
                return self._parse_ident_stmt()
            return self._parse_file_write()
        elif t.type == TokenType.CLOSE:
            if self._is_assignment():
                return self._parse_ident_stmt()
            return self._parse_file_close()
        elif t.type == TokenType.FN:
            if self._is_assignment():
                return self._parse_ident_stmt()
            return self._parse_lambda()

        # Идентификатор — присваивание, вызов или выражение
        elif t.type == TokenType.IDENT:
            return self._parse_ident_stmt()
    
        # Всё остальное — выражение
        else:
            return self._parse_expression()

    # ===== Блоки (INDENT/DEDENT) =====

    def _parse_block(self) -> List[ASTNode]:
        """
        Блок инструкций: INDENT statement* DEDENT
        Используется для тел классов, методов, if, while, for.
        """
        body = []
        if self.peek().type == TokenType.INDENT:
            self.advance()
            while self.peek().type not in (TokenType.DEDENT, TokenType.EOF):
                stmt = self._parse_statement()
                if stmt is not None:
                    body.append(stmt)
            if self.peek().type == TokenType.DEDENT:
                self.advance()
        return body

    # ===== Присваивание / идентификатор =====

    def _parse_ident_stmt(self) -> ASTNode:
        """
        Парсит всё, что начинается с идентификатора:
        - Присваивание:      name = value
        - Составное приев.:  name += value
        - Определение словаря: name = { ... }
        - Вызов метода:      obj:method(args)
        - Вызов функции:     name(args)
        - Инкремент:         name++
        - Просто выражение:  name
        """
        # Разрешаем ключевые слова как имена переменных при присваивании
        t = self.advance()
        parts = [t.value]

        while self.peek().type == TokenType.DOT:
            self.advance()
            t = self.advance()
            parts.append(t.value)

        full_name = '.'.join(parts)
        t = self.peek()

        # Инкремент/декремент: name++ или name--
        if t.type in (TokenType.PLUS_PLUS, TokenType.MINUS_MINUS):
            return CompoundAssignment(full_name, self.advance().value, NumberLiteral(1))

        # Вызов функции без присваивания: name(args)
        if t.type == TokenType.LPAREN:
            self.advance()
            args = []
            if self.peek().type != TokenType.RPAREN:
                args.append(self._parse_expression())
                while self.peek().type == TokenType.COMMA:
                    self.advance()
                    args.append(self._parse_expression())
            self.expect(TokenType.RPAREN)
            return FunCall(full_name, args)

        # Вызов метода через ':' : obj:method(args)
        if t.type == TokenType.COLON:
            self.advance()
            method = self.expect(TokenType.IDENT).value
            self.expect(TokenType.LPAREN)
            args = []
            if self.peek().type != TokenType.RPAREN:
                args.append(self._parse_expression())
                while self.peek().type == TokenType.COMMA:
                    self.advance()
                    args.append(self._parse_expression())
            self.expect(TokenType.RPAREN)
            expr = Identifier(parts[0])
            for f in parts[1:]:
                expr = FieldAccess(expr, f)
            return MethodCall(expr, method, args)

        # Присваивание: =, +=, -=, *=, /=
        if t.type in (TokenType.EQUALS, TokenType.PLUS_EQUALS, TokenType.MINUS_EQUALS,
              TokenType.STAR_EQUALS, TokenType.SLASH_EQUALS,
              TokenType.PERCENT_EQUALS, TokenType.CARET_EQUALS):
            op = self.advance()
            if op.type != TokenType.EQUALS:
                return CompoundAssignment(full_name, op.value, self._parse_expression())
            if self.peek().type == TokenType.LBRACE:
                return DictDef(full_name, self._parse_dict())
            return Assignment(full_name, self._parse_expression())

        # Просто выражение
        expr = Identifier(parts[0])
        for f in parts[1:]:
            expr = FieldAccess(expr, f)
        return expr

    # ===== Импорты =====

    def _parse_load(self) -> LoadStmt:
        """
        @load "filename" [like "Alias"]
        @load? "filename" [like "Alias"]
        """
        optional = self.advance().type == TokenType.AT_LOAD_OPT
        if not optional:
            self.pos -= 1
            self.advance()

        filename = self.expect(TokenType.STRING).value

        alias = None
        if self.peek().type == TokenType.LIKE:
            self.advance()
            alias = self.expect(TokenType.STRING).value

        return LoadStmt(filename, alias, optional)

    # ===== Значения =====

    def _parse_value(self) -> ASTNode:
        """
        Значение — то, что может быть справа от ':' в словаре
        или аргументом type_call.
        """
        t = self.peek()

        if t.type == TokenType.LBRACE:
            return self._parse_dict()
        elif t.type == TokenType.LBRACKET:
            return self._parse_list()
        elif t.type == TokenType.STRING:
            self.advance()
            return StringLiteral(t.value)
        elif t.type == TokenType.NUMBER:
            self.advance()
            return NumberLiteral(t.value)
        elif t.type == TokenType.TRUE:
            self.advance()
            return BoolLiteral(True)
        elif t.type == TokenType.FALSE:
            self.advance()
            return BoolLiteral(False)
        elif t.type == TokenType.NONE:
            self.advance()
            return NoneLiteral()
        elif t.type == TokenType.IDENT:
            self.advance()
            return Identifier(t.value)
        elif t.type in (TokenType.INT, TokenType.FLOAT, TokenType.STR,
                        TokenType.BOOL, TokenType.LIST, TokenType.DICT):
            return self._parse_type_call()
        else:
            raise ParseError(
                f"Неожиданный токен в значении: {t.type.value}",
                t.line, t.col
            )

    def _parse_dict(self) -> DictLiteral:
        """Словарь: { "key": value, ... } с опциональной trailing comma."""
        self.expect(TokenType.LBRACE)
        pairs = []

        while self.peek().type != TokenType.RBRACE:
            key = self.expect(TokenType.STRING).value
            self.expect(TokenType.COLON)
            value = self._parse_value()
            pairs.append((key, value))

            if self.peek().type == TokenType.COMMA:
                self.advance()
            else:
                break

        self.expect(TokenType.RBRACE)
        return DictLiteral(pairs)

    def _parse_list(self) -> ListLiteral:
        """Список: [value, ...] с опциональной trailing comma."""
        self.expect(TokenType.LBRACKET)
        elements = []

        if self.peek().type != TokenType.RBRACKET:
            elements.append(self._parse_value())
            while self.peek().type == TokenType.COMMA:
                self.advance()
                if self.peek().type == TokenType.RBRACKET:
                    break  # trailing comma
                elements.append(self._parse_value())

        self.expect(TokenType.RBRACKET)
        return ListLiteral(elements)

    def _parse_type_call(self) -> TypeCall:
        typename = self.advance().value
        self.expect(TokenType.LPAREN)
        
        # Для str/int/float/bool разрешаем выражения
        if typename in ('str', 'int', 'float', 'bool'):
            args = [self._parse_expression()]
            self.expect(TokenType.RPAREN)
            return FunCall(typename, args)
        
        args = []
        if self.peek().type != TokenType.RPAREN:
            args.append(self._parse_value())
            while self.peek().type == TokenType.COMMA:
                self.advance()
                if self.peek().type == TokenType.RPAREN:
                    break
                args.append(self._parse_value())
        self.expect(TokenType.RPAREN)
        return TypeCall(typename, args)

    # ===== Классы и методы =====

    def _parse_class(self) -> ClassDef:
        """
        Определение класса:
        class Name(Parent):
            [docstring]
            method...
        или без родителя:
        class Name:
            ...
        """
        self.expect(TokenType.CLASS)
        name = self.expect(TokenType.IDENT).value
    
        parent = None
        if self.peek().type == TokenType.LPAREN:
            self.advance()
            parent = self.expect(TokenType.IDENT).value
            self.expect(TokenType.RPAREN)

        self.expect(TokenType.COLON)

        # Тело класса — блок с INDENT/DEDENT
        body = self._parse_block()

        # Извлекаем docstring и методы
        doc = None
        methods = []
        for stmt in body:
            if isinstance(stmt, StringLiteral) and doc is None:
                doc = stmt.value
            elif isinstance(stmt, MethodDef):
                methods.append(stmt)
    
        return ClassDef(name, parent, doc, methods)

    def _parse_method(self) -> MethodDef:
        """
        Определение метода:
        def name(self, param1, param2: type, *args):
            body
        """
        self.expect(TokenType.DEF)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LPAREN)

        params = []
        vararg = None

        if self.peek().type != TokenType.RPAREN and self.peek().type != TokenType.STAR:
            # Первый параметр
            pname = self.expect(TokenType.IDENT).value
            ptype = 'int'
            if self.peek().type == TokenType.COLON:
                self.advance()
                t = self.peek()
                if t.type in (TokenType.IDENT, TokenType.INT, TokenType.FLOAT,
                              TokenType.STR, TokenType.BOOL):
                    ptype = self.advance().value
            params.append((pname, ptype))

            # Остальные параметры
            while self.peek().type == TokenType.COMMA:
                self.advance()
                if self.peek().type == TokenType.STAR:
                    break
                pname = self.expect(TokenType.IDENT).value
                ptype = 'int'
                if self.peek().type == TokenType.COLON:
                    self.advance()
                    t = self.peek()
                    if t.type in (TokenType.IDENT, TokenType.INT, TokenType.FLOAT,
                                  TokenType.STR, TokenType.BOOL):
                        ptype = self.advance().value
                params.append((pname, ptype))

        # *args
        if self.peek().type == TokenType.STAR:
            self.advance()
            vararg = self.expect(TokenType.IDENT).value

        self.expect(TokenType.RPAREN)
        self.expect(TokenType.COLON)
        body = self._parse_block()

        return MethodDef(name, params, vararg, body)

    # ===== Управляющие конструкции =====

    def _parse_if(self, skip_if: bool = False) -> IfStmt:
        """
        Условный оператор:
        if condition:
            body
        elif condition:
            body
        else:
            body
        
        skip_if=True используется при рекурсии для elif
        (ключевое слово elif уже съедено).
        """
        if not skip_if:
            if self.peek().type == TokenType.ELIF:
                self.advance()
            else:
                self.expect(TokenType.IF)

        condition = self._parse_expression()
        self.expect(TokenType.COLON)
        body = self._parse_block()

        else_body = None
        if self.peek().type == TokenType.ELIF:
            self.advance()
            else_body = [self._parse_if(skip_if=True)]
        elif self.peek().type == TokenType.ELSE:
            self.advance()
            self.expect(TokenType.COLON)
            else_body = self._parse_block()

        return IfStmt(condition, body, else_body)

    def _parse_while(self) -> WhileStmt:
        """Цикл while: while condition: body"""
        self.expect(TokenType.WHILE)
        condition = self._parse_expression()
        self.expect(TokenType.COLON)
        return WhileStmt(condition, self._parse_block())

    def _parse_for(self) -> ForStmt:
        """Цикл for: for var in iterable: body"""
        self.expect(TokenType.FOR)
        var = self.expect(TokenType.IDENT).value
        self.expect(TokenType.IN)
        iterable = self._parse_expression()
        self.expect(TokenType.COLON)
        return ForStmt(var, iterable, self._parse_block())

    def _parse_return(self) -> ReturnStmt:
        """Возврат из метода: return [expression]"""
        self.expect(TokenType.RETURN)
        stop_tokens = {TokenType.EOF, TokenType.DEDENT, TokenType.ELSE, TokenType.ELIF}
        if self.peek().type not in stop_tokens:
            return ReturnStmt(self._parse_expression())
        return ReturnStmt(None)

    def _parse_print(self) -> PrintStmt:
        """Вывод в консоль: print(value)"""
        self.expect(TokenType.PRINT)
        self.expect(TokenType.LPAREN)
        value = self._parse_expression()
        self.expect(TokenType.RPAREN)
        return PrintStmt(value)

    def _parse_assert(self) -> AssertStmt:
        """Проверка условия: assert condition"""
        self.expect(TokenType.ASSERT)
        condition = self._parse_expression()
        return AssertStmt(condition)

    # ===== Файловые операции =====

    def _parse_file_open(self) -> FileOpen:
        """open("filename", "mode")"""
        self.expect(TokenType.OPEN)
        self.expect(TokenType.LPAREN)
        filename = self._parse_expression()
        self.expect(TokenType.COMMA)
        mode = self.expect(TokenType.STRING).value
        self.expect(TokenType.RPAREN)
        return FileOpen(filename, mode)

    def _parse_file_read(self) -> FileRead:
        """read(file)"""
        self.expect(TokenType.READ)
        self.expect(TokenType.LPAREN)
        file = self._parse_expression()
        self.expect(TokenType.RPAREN)
        return FileRead(file)

    def _parse_file_write(self) -> FileWrite:
        """write(file, content)"""
        self.expect(TokenType.WRITE)
        self.expect(TokenType.LPAREN)
        file = self._parse_expression()
        self.expect(TokenType.COMMA)
        content = self._parse_expression()
        self.expect(TokenType.RPAREN)
        return FileWrite(file, content)

    def _parse_file_close(self) -> FileClose:
        """close(file)"""
        self.expect(TokenType.CLOSE)
        self.expect(TokenType.LPAREN)
        file = self._parse_expression()
        self.expect(TokenType.RPAREN)
        return FileClose(file)

    # ===== Лямбды =====

    def _parse_lambda(self) -> LambdaExpr:
        """
        Лямбда-выражение:
        fn(): expression
        fn(x, y): expression
        fn():
            block
        """
        self.expect(TokenType.FN)
        params = []

        if self.peek().type == TokenType.LPAREN:
            self.advance()
            if self.peek().type != TokenType.RPAREN:
                pname = self.expect(TokenType.IDENT).value
                ptype = 'int'
                if self.peek().type == TokenType.COLON:
                    self.advance()
                    t = self.peek()
                    if t.type in (TokenType.IDENT, TokenType.INT, TokenType.FLOAT,
                                  TokenType.STR, TokenType.BOOL):
                        ptype = self.advance().value
                params.append((pname, ptype))
                while self.peek().type == TokenType.COMMA:
                    self.advance()
                    pname = self.expect(TokenType.IDENT).value
                    ptype = 'int'
                    if self.peek().type == TokenType.COLON:
                        self.advance()
                        t = self.peek()
                        if t.type in (TokenType.IDENT, TokenType.INT, TokenType.FLOAT,
                                      TokenType.STR, TokenType.BOOL):
                            ptype = self.advance().value
                    params.append((pname, ptype))
            self.expect(TokenType.RPAREN)

        self.expect(TokenType.COLON)

        # Однострочная или блок
        if self.peek().type == TokenType.INDENT:
            body = self._parse_block()
        else:
            body = [self._parse_expression()]

        return LambdaExpr(params, body)

    # ===== Выражения =====

    def _parse_expression(self) -> ASTNode:
        """Выражение: логическое И/ИЛИ."""
        return self._parse_logic()

    def _parse_logic(self) -> ASTNode:
        """Логические операторы: and, or."""
        left = self._parse_comparison()
        while self.peek().type in (TokenType.AND, TokenType.OR):
            op = self.advance().value
            right = self._parse_comparison()
            left = BinaryOp(op, left, right)
        return left

    def _parse_comparison(self) -> ASTNode:
        left = self._parse_addition()
        while self.peek().type in (TokenType.EQUALS_EQUALS, TokenType.NOT_EQUALS,
                                    TokenType.LESS, TokenType.GREATER,
                                    TokenType.LESS_EQUALS, TokenType.GREATER_EQUALS,
                                    TokenType.CARET):
            op = self.advance().value
            right = self._parse_addition()
            left = BinaryOp(op, left, right)
        return left

    def _parse_addition(self) -> ASTNode:
        """Сложение и вычитание: +, -"""
        left = self._parse_multiplication()
        while self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            right = self._parse_multiplication()
            left = BinaryOp(op, left, right)
        return left
    
    def _parse_multiplication(self) -> ASTNode:
        """Умножение, деление и остаток: *, /, %"""
        left = self._parse_unary()
        while self.peek().type in (TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self.advance().value
            right = self._parse_unary()
            left = BinaryOp(op, left, right)
        return left

    def _parse_unary(self) -> ASTNode:
        t = self.peek()
        if t.type == TokenType.NOT:
            self.advance()
            return UnaryOp('!', self._parse_unary())
        elif t.type in (TokenType.PLUS_PLUS, TokenType.MINUS_MINUS):
            op = self.advance().value
            return UnaryOp(op, self._parse_primary())
        elif t.type == TokenType.MINUS:
            self.advance()
            return UnaryOp('-', self._parse_primary())
        return self._parse_primary()

    def _parse_primary(self) -> ASTNode:
        """
        Базовый элемент выражения:
        - идентификатор (с точками)
        - число, строка, булево, None
        - словарь, список, скобки
        - вызов типа
        - лямбда
        - файловые операции (в выражении)
        """
        t = self.peek()

        # Лямбда
        if t.type == TokenType.FN:
            return self._parse_lambda()

        # Унарные операторы
        if t.type == TokenType.NOT:
            self.advance()
            return UnaryOp('!', self._parse_primary())
        if t.type in (TokenType.PLUS_PLUS, TokenType.MINUS_MINUS):
            op = self.advance().value
            return UnaryOp(op, self._parse_primary())

        # Идентификатор (с точками и возможным вызовом)
        if t.type == TokenType.IDENT:
            self.advance()
            expr = Identifier(t.value)
            while self.peek().type == TokenType.DOT:
                self.advance()
                expr = FieldAccess(expr, self.expect(TokenType.IDENT).value)
            # Вызов функции: name(args)
            if self.peek().type == TokenType.LPAREN:
                self.advance()
                args = []
                if self.peek().type != TokenType.RPAREN:
                    args.append(self._parse_expression())
                    while self.peek().type == TokenType.COMMA:
                        self.advance()
                        args.append(self._parse_expression())
                self.expect(TokenType.RPAREN)
                return FunCall(t.value, args)
            '''
            # Вызов метода через ':' в выражении
            if self.peek().type == TokenType.COLON:
                self.advance()
                method = self.expect(TokenType.IDENT).value
                self.expect(TokenType.LPAREN)
                args = []
                if self.peek().type != TokenType.RPAREN:
                    args.append(self._parse_expression())
                    while self.peek().type == TokenType.COMMA:
                        self.advance()
                        args.append(self._parse_expression())
                self.expect(TokenType.RPAREN)
                return MethodCall(expr, method, args)
            '''
            
            return expr

        # Литералы
        elif t.type == TokenType.NUMBER:
            self.advance()
            return NumberLiteral(t.value)
        elif t.type == TokenType.STRING:
            self.advance()
            return StringLiteral(t.value)
        elif t.type == TokenType.TRUE:
            self.advance()
            return BoolLiteral(True)
        elif t.type == TokenType.FALSE:
            self.advance()
            return BoolLiteral(False)
        elif t.type == TokenType.NONE:
            self.advance()
            return NoneLiteral()

        # Словарь, список, скобки
        elif t.type == TokenType.LBRACE:
            return self._parse_dict()
        elif t.type == TokenType.LBRACKET:
            return self._parse_list()
        elif t.type == TokenType.LPAREN:
            self.advance()
            expr = self._parse_expression()
            self.expect(TokenType.RPAREN)
            return expr

        # Вызов типа
        elif t.type in (TokenType.INT, TokenType.FLOAT, TokenType.STR,
                        TokenType.BOOL, TokenType.LIST, TokenType.DICT):
            return self._parse_type_call()

        # Файловые операции в выражениях
        elif t.type == TokenType.OPEN:
            return self._parse_file_open()
        elif t.type == TokenType.READ:
            return self._parse_file_read()

        else:
            raise ParseError(
                f"Неожиданный токен в выражении: {t.type.value}",
                t.line, t.col
            )