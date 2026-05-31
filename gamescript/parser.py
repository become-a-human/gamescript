"""
Парсер: список токенов → AST с поддержкой INDENT/DEDENT.
"""

from typing import List, Optional
from .tokens import TokenType, Token
from .ast_nodes import *


class ParseError(SyntaxError):
    def __init__(self, msg: str, line: int, col: int, context: str = ""):
        self.line = line
        self.col = col
        self.context = context
        pointer = " " * (col - 1) + "^"
        super().__init__(f"{msg}\n  строка {line}, колонка {col}\n  {context}\n  {pointer}")


class Parser:
    
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Token:
        return self.tokens[self.pos]

    def advance(self) -> Token:
        t = self.tokens[self.pos]
        self.pos += 1
        return t

    def expect(self, ttype: TokenType) -> Token:
        t = self.advance()
        if t.type != ttype:
            raise ParseError(f"Ожидался {ttype.value}, получен {t.type.value} ({t.value})", t.line, t.col)
        return t

    def parse(self) -> Program:
        stmts = []
        while self.peek().type != TokenType.EOF:
            stmts.append(self._parse_statement())
        return Program(stmts)

    def _parse_statement(self) -> ASTNode:
        t = self.peek()
        
        if t.type == TokenType.AT_LOAD: return self._parse_load()
        elif t.type == TokenType.AT_LOAD_OPT: return self._parse_load()
        elif t.type == TokenType.CLASS: return self._parse_class()
        elif t.type == TokenType.DEF: return self._parse_method()
        elif t.type == TokenType.IF: return self._parse_if()
        elif t.type == TokenType.WHILE: return self._parse_while()
        elif t.type == TokenType.FOR: return self._parse_for()
        elif t.type == TokenType.RETURN: return self._parse_return()
        elif t.type == TokenType.CONTINUE: self.advance(); return ContinueStmt()
        elif t.type == TokenType.BREAK: self.advance(); return BreakStmt()
        elif t.type == TokenType.INDENT: self.advance(); return None
        elif t.type == TokenType.DEDENT: self.advance(); return None
        elif t.type == TokenType.IDENT: return self._parse_ident_stmt()
        elif t.type == TokenType.PASS: self.advance(); return None
        elif t.type == TokenType.PRINT: return self._parse_print()
        elif t.type == TokenType.ASSERT: return self._parse_assert()
        else: return self._parse_expression()

    def _parse_block(self) -> List[ASTNode]:
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

    def _parse_ident_stmt(self) -> ASTNode:
        parts = [self.expect(TokenType.IDENT).value]
        while self.peek().type == TokenType.DOT:
            self.advance()
            parts.append(self.expect(TokenType.IDENT).value)
        full_name = '.'.join(parts)
        t = self.peek()
        if t.type in (TokenType.PLUS_PLUS, TokenType.MINUS_MINUS):
            return CompoundAssignment(full_name, self.advance().value, NumberLiteral(1))
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
        if t.type in (TokenType.EQUALS, TokenType.PLUS_EQUALS, TokenType.MINUS_EQUALS,
                      TokenType.STAR_EQUALS, TokenType.SLASH_EQUALS):
            op = self.advance()
            if op.type != TokenType.EQUALS:
                return CompoundAssignment(full_name, op.value, self._parse_expression())
            if self.peek().type == TokenType.LBRACE:
                return DictDef(full_name, self._parse_dict())
            return Assignment(full_name, self._parse_expression())
        expr = Identifier(parts[0])
        for f in parts[1:]:
            expr = FieldAccess(expr, f)
        return expr

    def _parse_load(self) -> LoadStmt:
        optional = self.advance().type == TokenType.AT_LOAD_OPT
        if not optional: self.pos -= 1; self.advance()
        filename = self.expect(TokenType.STRING).value
        alias = None
        if self.peek().type == TokenType.LIKE:
            self.advance()
            alias = self.expect(TokenType.STRING).value
        return LoadStmt(filename, alias, optional)

    def _parse_value(self) -> ASTNode:
        t = self.peek()
        if t.type == TokenType.LBRACE: return self._parse_dict()
        elif t.type == TokenType.STRING: self.advance(); return StringLiteral(t.value)
        elif t.type == TokenType.NUMBER: self.advance(); return NumberLiteral(t.value)
        elif t.type == TokenType.TRUE: self.advance(); return BoolLiteral(True)
        elif t.type == TokenType.FALSE: self.advance(); return BoolLiteral(False)
        elif t.type == TokenType.NONE: self.advance(); return NoneLiteral()
        elif t.type in (TokenType.INT, TokenType.FLOAT, TokenType.STR,
                        TokenType.BOOL, TokenType.LIST, TokenType.DICT):
            return self._parse_type_call()
        else:
            raise ParseError(f"Неожиданный токен в значении: {t.type.value}", t.line, t.col)

    def _parse_dict(self) -> DictLiteral:
        self.expect(TokenType.LBRACE)
        pairs = []
        while self.peek().type != TokenType.RBRACE:
            key = self.expect(TokenType.STRING).value
            self.expect(TokenType.COLON)
            value = self._parse_value()
            pairs.append((key, value))
            if self.peek().type == TokenType.COMMA: self.advance()
            else: break
        self.expect(TokenType.RBRACE)
        return DictLiteral(pairs)

    def _parse_type_call(self) -> TypeCall:
        typename = self.advance().value
        self.expect(TokenType.LPAREN)
        args = []
        if self.peek().type != TokenType.RPAREN:
            args.append(self._parse_value())
            while self.peek().type == TokenType.COMMA:
                self.advance()
                if self.peek().type == TokenType.RPAREN: break
                args.append(self._parse_value())
        self.expect(TokenType.RPAREN)
        return TypeCall(typename, args)

    def _parse_class(self) -> ClassDef:
        self.expect(TokenType.CLASS)
        name = self.expect(TokenType.IDENT).value
        parent = None
        if self.peek().type == TokenType.LPAREN:
            self.advance()
            parent = self.expect(TokenType.IDENT).value
            self.expect(TokenType.RPAREN)
        self.expect(TokenType.COLON)
        
        # docstring может быть на следующей строке
        # но _parse_block сам разберётся с INDENT
        body = self._parse_block()
        methods = [s for s in body if isinstance(s, MethodDef)]
        
        # docstring извлекаем из тела если есть
        doc = None
        for s in body:
            if isinstance(s, StringLiteral):
                doc = s.value
                break
        
        return ClassDef(name, parent, doc, methods)
    
    def _parse_print(self) -> PrintStmt:
        self.expect(TokenType.PRINT)
        self.expect(TokenType.LPAREN)
        value = self._parse_expression()
        self.expect(TokenType.RPAREN)
        return PrintStmt(value)
    
    def _parse_assert(self) -> AssertStmt:
        self.expect(TokenType.ASSERT)
        condition = self._parse_expression()
        return AssertStmt(condition)
    
    def _parse_method(self) -> MethodDef:
        self.expect(TokenType.DEF)
        name = self.expect(TokenType.IDENT).value
        self.expect(TokenType.LPAREN)
        params = []
        if self.peek().type != TokenType.RPAREN:
            pname = self.expect(TokenType.IDENT).value
            ptype = 'int'
            if self.peek().type == TokenType.COLON:
                self.advance()
                t = self.peek()
                if t.type in (TokenType.IDENT, TokenType.INT, TokenType.FLOAT, TokenType.STR, TokenType.BOOL):
                    ptype = self.advance().value
            params.append((pname, ptype))
            while self.peek().type == TokenType.COMMA:
                self.advance()
                pname = self.expect(TokenType.IDENT).value
                ptype = 'int'
                if self.peek().type == TokenType.COLON:
                    self.advance()
                    t = self.peek()
                    if t.type in (TokenType.IDENT, TokenType.INT, TokenType.FLOAT, TokenType.STR, TokenType.BOOL):
                        ptype = self.advance().value
                params.append((pname, ptype))
        self.expect(TokenType.RPAREN)
        self.expect(TokenType.COLON)
        body = self._parse_block()
        return MethodDef(name, params, body)
    
    def _parse_if(self, skip_if: bool = False) -> IfStmt:
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
        self.expect(TokenType.WHILE)
        condition = self._parse_expression()
        self.expect(TokenType.COLON)
        return WhileStmt(condition, self._parse_block())
    
    def _parse_for(self) -> ForStmt:
        self.expect(TokenType.FOR)
        var = self.expect(TokenType.IDENT).value
        self.expect(TokenType.IN)
        iterable = self._parse_expression()
        self.expect(TokenType.COLON)
        return ForStmt(var, iterable, self._parse_block())

    def _parse_return(self) -> ReturnStmt:
        self.expect(TokenType.RETURN)
        stop_tokens = {TokenType.EOF, TokenType.DEDENT, TokenType.ELSE, TokenType.ELIF}
        if self.peek().type not in stop_tokens:
            return ReturnStmt(self._parse_expression())
        return ReturnStmt(None)

    def _parse_expression(self) -> ASTNode: return self._parse_logic()

    def _parse_logic(self) -> ASTNode:
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
                                    TokenType.LESS_EQUALS, TokenType.GREATER_EQUALS):
            op = self.advance().value
            right = self._parse_addition()
            left = BinaryOp(op, left, right)
        return left

    def _parse_addition(self) -> ASTNode:
        left = self._parse_multiplication()
        while self.peek().type in (TokenType.PLUS, TokenType.MINUS):
            op = self.advance().value
            right = self._parse_multiplication()
            left = BinaryOp(op, left, right)
        return left

    def _parse_multiplication(self) -> ASTNode:
        left = self._parse_primary()
        while self.peek().type in (TokenType.STAR, TokenType.SLASH):
            op = self.advance().value
            right = self._parse_primary()
            left = BinaryOp(op, left, right)
        return left

    def _parse_list(self) -> ListLiteral:
        self.expect(TokenType.LBRACKET)
        elements = []
        if self.peek().type != TokenType.RBRACKET:
            elements.append(self._parse_expression())
            while self.peek().type == TokenType.COMMA:
                self.advance()
                elements.append(self._parse_expression())
        self.expect(TokenType.RBRACKET)
        return ListLiteral(elements)

    def _parse_primary(self) -> ASTNode:
        t = self.peek()
        
        # Префиксные ++ и --
        if t.type in (TokenType.PLUS_PLUS, TokenType.MINUS_MINUS):
            op = self.advance().value
            expr = self._parse_primary()
            return UnaryOp(op, expr)
        
        if t.type == TokenType.NOT: self.advance(); return UnaryOp('!', self._parse_primary())
        if t.type == TokenType.IDENT:
            self.advance()
            expr = Identifier(t.value)
            while self.peek().type == TokenType.DOT:
                self.advance()
                expr = FieldAccess(expr, self.expect(TokenType.IDENT).value)
            return expr
        elif t.type == TokenType.NUMBER: self.advance(); return NumberLiteral(t.value)
        elif t.type == TokenType.STRING: self.advance(); return StringLiteral(t.value)
        elif t.type == TokenType.TRUE: self.advance(); return BoolLiteral(True)
        elif t.type == TokenType.FALSE: self.advance(); return BoolLiteral(False)
        elif t.type == TokenType.NONE: self.advance(); return NoneLiteral()
        elif t.type == TokenType.LBRACE: return self._parse_dict()
        elif t.type == TokenType.LBRACKET: return self._parse_list()
        elif t.type == TokenType.LPAREN:
            self.advance()
            expr = self._parse_expression()
            self.expect(TokenType.RPAREN)
            return expr
        elif t.type in (TokenType.INT, TokenType.FLOAT, TokenType.STR,
                        TokenType.BOOL, TokenType.LIST, TokenType.DICT):
            return self._parse_type_call()
        else:
            raise ParseError(f"Неожиданный токен в выражении: {t.type.value}", t.line, t.col)