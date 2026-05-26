"""
Узлы AST (Абстрактного Синтаксического Дерева).

Каждый класс — один тип узла, который парсер создаёт из токенов.
Кодген обходит эти узлы и генерирует C++ код.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any


@dataclass
class ASTNode:
    """Базовый класс для всех узлов AST."""
    pass


# ===== Корень программы =====

@dataclass
class Program(ASTNode):
    """Корень программы — список всех определений верхнего уровня."""
    statements: List[ASTNode] = field(default_factory=list)


# ===== Импорты =====

@dataclass
class LoadStmt(ASTNode):
    """
    @load "filename" [like "alias"] [~grab ...]
    @load? "filename" [like "alias"] [~grab ...]
    
    Атрибуты:
        filename: путь к файлу
        alias:    псевдоним для namespace (like)
        grabs:    список захватываемых имён [(name, alias), ...]
        optional: True если @load?
    """
    filename: str
    alias: Optional[str] = None
    grabs: List[tuple] = field(default_factory=list)
    optional: bool = False


@dataclass
class GrabStmt(ASTNode):
    """
    ~grab <Name> [like <Alias>], ...
    ~grab? <Name> [like <Alias>], ...
    
    Атрибуты:
        names:    список [(name, alias_or_None), ...]
        optional: True если ~grab?
    """
    names: List[tuple] = field(default_factory=list)
    optional: bool = False


@dataclass
class LinkStmt(ASTNode):
    """
    &link <func> [like <alias>], ...
    &link? <func> [like <alias>], ...
    
    Атрибуты:
        names:    список [(name, alias_or_None), ...]
        optional: True если &link?
    """
    names: List[tuple] = field(default_factory=list)
    optional: bool = False


# ===== Значения (литералы) =====

@dataclass
class StringLiteral(ASTNode):
    """Строковый литерал: "hello" """
    value: str


@dataclass
class NumberLiteral(ASTNode):
    """Числовой литерал: 42 или 3.14"""
    value: float


@dataclass
class BoolLiteral(ASTNode):
    """Булев литерал: true или false"""
    value: bool


@dataclass
class NoneLiteral(ASTNode):
    """None"""
    pass


# ===== Словари =====

@dataclass
class DictLiteral(ASTNode):
    """
    Анонимный словарь: { "key": value, ... }
    Используется внутри других словарей или как значение.
    """
    pairs: List[tuple] = field(default_factory=list)  # [(str, ASTNode), ...]


@dataclass
class DictDef(ASTNode):
    """
    Именованный словарь: NAME = { ... }
    Определение на верхнем уровне.
    """
    name: str
    value: ASTNode


# ===== Классы и методы =====

@dataclass
class ClassDef(ASTNode):
    """
    Определение класса: class Name(Parent): ...
    
    Атрибуты:
        name:    имя класса
        parent:  имя родительского класса
        doc:     документация (опционально)
        methods: список методов
    """
    name: str
    parent: str
    doc: Optional[str] = None
    methods: List['MethodDef'] = field(default_factory=list)


@dataclass
class MethodDef(ASTNode):
    """
    Определение метода: def name(params): body
    
    Атрибуты:
        name:   имя метода
        params: список параметров [(name, type), ...]
        body:   список инструкций
    """
    name: str
    params: List[tuple] = field(default_factory=list)  # [(name, type), ...]
    body: List[ASTNode] = field(default_factory=list)


# ===== Выражения =====

@dataclass
class Identifier(ASTNode):
    """Идентификатор: имя переменной, параметра и т.д."""
    name: str


@dataclass
class TypeCall(ASTNode):
    """
    Вызов конструктора типа: int(100), str("hello"), list(a, b)
    
    Атрибуты:
        typename: имя типа (int, float, str, bool, list, dict)
        args:     аргументы конструктора
    """
    typename: str
    args: List[ASTNode] = field(default_factory=list)


@dataclass
class BinaryOp(ASTNode):
    """
    Бинарная операция: a + b, x == y, hp <= 0
    
    Атрибуты:
        op:    оператор (+, -, *, /, ==, !=, <, >, <=, >=)
        left:  левый операнд
        right: правый операнд
    """
    op: str
    left: ASTNode
    right: ASTNode


@dataclass
class FieldAccess(ASTNode):
    """
    Доступ к полю: obj.field
    
    Атрибуты:
        obj:   объект (self, enemy, ...)
        field: имя поля
    """
    obj: ASTNode
    field: str


@dataclass
class MethodCall(ASTNode):
    """
    Вызов метода: obj:method(args)
    
    Атрибуты:
        obj:    объект
        method: имя метода
        args:   аргументы
    """
    obj: ASTNode
    method: str
    args: List[ASTNode] = field(default_factory=list)


@dataclass
class FunCall(ASTNode):
    """
    Вызов функции: name(args)
    """
    name: str
    args: List[ASTNode] = field(default_factory=list)


# ===== Инструкции =====

@dataclass
class Assignment(ASTNode):
    """Присваивание: name = value"""
    name: str
    value: ASTNode


@dataclass
class CompoundAssignment(ASTNode):
    """
    Составное присваивание: name += value, name -= value
    
    Атрибуты:
        name:  имя переменной
        op:    оператор (+=, -=, *=, /=)
        value: значение
    """
    name: str
    op: str
    value: ASTNode


@dataclass
class IfStmt(ASTNode):
    """
    Условный оператор: if condition: body [else: else_body]
    """
    condition: ASTNode
    body: List[ASTNode] = field(default_factory=list)
    else_body: Optional[List[ASTNode]] = None


@dataclass
class WhileStmt(ASTNode):
    """Цикл while: while condition: body"""
    condition: ASTNode
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class ForStmt(ASTNode):
    """Цикл for: for var in iterable: body"""
    var: str
    iterable: ASTNode
    body: List[ASTNode] = field(default_factory=list)


@dataclass
class ReturnStmt(ASTNode):
    """Возврат из метода: return [value]"""
    value: Optional[ASTNode] = None


@dataclass
class ContinueStmt(ASTNode):
    """continue"""
    pass


@dataclass
class BreakStmt(ASTNode):
    """break"""
    pass