"""
Узлы AST (Абстрактного Синтаксического Дерева).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any

@dataclass
class ASTNode:
    """Базовый класс для всех узлов AST."""
    pass

@dataclass
class Program(ASTNode):
    """Корень программы."""
    statements: List[ASTNode] = field(default_factory=list)

# ===== Импорты =====

@dataclass
class LoadStmt(ASTNode):
    """@load "filename" или @load? "filename" """
    filename: str
    alias: Optional[str] = None    # like "Alias"
    optional: bool = False

# ===== Значения =====

@dataclass
class StringLiteral(ASTNode):
    value: str

@dataclass
class NumberLiteral(ASTNode):
    value: float

@dataclass
class BoolLiteral(ASTNode):
    value: bool

@dataclass
class NoneLiteral(ASTNode):
    pass

# ===== Словари =====

@dataclass
class DictLiteral(ASTNode):
    pairs: List[tuple] = field(default_factory=list)

@dataclass
class DictDef(ASTNode):
    name: str
    value: ASTNode

# ===== Классы и методы =====

@dataclass
class ClassDef(ASTNode):
    name: str
    parent: Optional[str] = None
    doc: Optional[str] = None
    methods: List['MethodDef'] = field(default_factory=list)

@dataclass
class MethodDef(ASTNode):
    name: str
    params: List[tuple] = field(default_factory=list)
    vararg: Optional[str] = None
    body: List[ASTNode] = field(default_factory=list)

# ===== Выражения =====

@dataclass
class Identifier(ASTNode):
    name: str

@dataclass
class TypeCall(ASTNode):
    typename: str
    args: List[ASTNode] = field(default_factory=list)

@dataclass
class BinaryOp(ASTNode):
    op: str
    left: ASTNode
    right: ASTNode

@dataclass
class UnaryOp(ASTNode):
    op: str
    expr: ASTNode

@dataclass
class FieldAccess(ASTNode):
    obj: ASTNode
    field: str

@dataclass
class MethodCall(ASTNode):
    obj: ASTNode
    method: str
    args: List[ASTNode] = field(default_factory=list)

@dataclass
class FunCall(ASTNode):
    name: str
    args: List[ASTNode] = field(default_factory=list)

# ===== Инструкции =====

@dataclass
class Assignment(ASTNode):
    name: str
    value: ASTNode

@dataclass
class CompoundAssignment(ASTNode):
    name: str
    op: str
    value: ASTNode

@dataclass
class IfStmt(ASTNode):
    condition: ASTNode
    body: List[ASTNode] = field(default_factory=list)
    else_body: Optional[List[ASTNode]] = None

@dataclass
class WhileStmt(ASTNode):
    condition: ASTNode
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class ForStmt(ASTNode):
    var: str
    iterable: ASTNode
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class ReturnStmt(ASTNode):
    value: Optional[ASTNode] = None

@dataclass
class ContinueStmt(ASTNode):
    pass

@dataclass
class BreakStmt(ASTNode):
    pass

@dataclass
class PrintStmt(ASTNode):
    value: ASTNode

@dataclass
class AssertStmt(ASTNode):
    condition: ASTNode

@dataclass
class ListLiteral(ASTNode):
    elements: List[ASTNode] = field(default_factory=list)

@dataclass
class LambdaExpr(ASTNode):
    params: List[tuple] = field(default_factory=list)
    body: List[ASTNode] = field(default_factory=list)