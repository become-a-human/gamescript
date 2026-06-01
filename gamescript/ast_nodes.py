"""
Узлы AST (Абстрактного Синтаксического Дерева) для GameScript.

Каждый класс представляет один тип узла, который парсер создаёт из токенов.
Кодген обходит эти узлы и генерирует C++ код.
"""

from dataclasses import dataclass, field
from typing import List, Optional


# ===== Базовый класс =====

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
    @load "filename"       — обязательный импорт
    @load? "filename"      — опциональный импорт
    @load "file" like "X"  — импорт с псевдонимом
    """
    filename: str
    alias: Optional[str] = None
    optional: bool = False


# ===== Литералы =====

@dataclass
class StringLiteral(ASTNode):
    """Строковый литерал: "текст" """
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
    """None (аналог null/nullptr)"""
    pass


# ===== Словари и списки =====

@dataclass
class DictLiteral(ASTNode):
    """Анонимный словарь: { "key": value, ... }"""
    pairs: List[tuple] = field(default_factory=list)


@dataclass
class DictDef(ASTNode):
    """Именованный словарь: NAME = { ... }"""
    name: str
    value: ASTNode


@dataclass
class ListLiteral(ASTNode):
    """Список: [1, 2, 3]"""
    elements: List[ASTNode] = field(default_factory=list)


# ===== Классы и методы =====

@dataclass
class ClassDef(ASTNode):
    """
    Определение класса: class Name(Parent): ...
    parent может быть None для класса без родителя.
    """
    name: str
    parent: Optional[str] = None
    doc: Optional[str] = None
    methods: List['MethodDef'] = field(default_factory=list)


@dataclass
class MethodDef(ASTNode):
    """
    Определение метода: def name(params): body
    Поддерживает *args через vararg.
    """
    name: str
    params: List[tuple] = field(default_factory=list)  # [(name, type), ...]
    vararg: Optional[str] = None  # *args
    body: List[ASTNode] = field(default_factory=list)


# ===== Выражения =====

@dataclass
class Identifier(ASTNode):
    """Идентификатор: имя переменной, параметра, класса."""
    name: str


@dataclass
class TypeCall(ASTNode):
    """Вызов конструктора типа: int(100), str("hello"), list(a, b)"""
    typename: str
    args: List[ASTNode] = field(default_factory=list)


@dataclass
class BinaryOp(ASTNode):
    """Бинарная операция: a + b, x == y, hp <= 0"""
    op: str
    left: ASTNode
    right: ASTNode


@dataclass
class UnaryOp(ASTNode):
    """Унарная операция: not x, ++a, --b"""
    op: str
    expr: ASTNode


@dataclass
class FieldAccess(ASTNode):
    """Доступ к полю: obj.field"""
    obj: ASTNode
    field: str


@dataclass
class MethodCall(ASTNode):
    """Вызов метода через ':' : obj:method(args)"""
    obj: ASTNode
    method: str
    args: List[ASTNode] = field(default_factory=list)


@dataclass
class FunCall(ASTNode):
    """Вызов функции: name(args) или конструктора ClassName(args)"""
    name: str
    args: List[ASTNode] = field(default_factory=list)


@dataclass
class LambdaExpr(ASTNode):
    """Лямбда-выражение: fn(x): x + 1 или fn(): self.gold = self.gold + 1"""
    params: List[tuple] = field(default_factory=list)
    body: List[ASTNode] = field(default_factory=list)


# ===== Инструкции =====

@dataclass
class Assignment(ASTNode):
    """Присваивание: name = value"""
    name: str
    value: ASTNode


@dataclass
class CompoundAssignment(ASTNode):
    """Составное присваивание: name += value, name -= value"""
    name: str
    op: str
    value: ASTNode


@dataclass
class IfStmt(ASTNode):
    """Условный оператор: if condition: body [elif: ...] [else: ...]"""
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


@dataclass
class PrintStmt(ASTNode):
    """Вывод в консоль: print(value)"""
    value: ASTNode


@dataclass
class AssertStmt(ASTNode):
    """Проверка условия: assert condition"""
    condition: ASTNode


# ===== Файловые операции =====

@dataclass
class FileOpen(ASTNode):
    """Открытие файла: open("path", "mode")"""
    filename: ASTNode
    mode: str


@dataclass
class FileRead(ASTNode):
    """Чтение файла: read(file)"""
    file: ASTNode


@dataclass
class FileWrite(ASTNode):
    """Запись в файл: write(file, content)"""
    file: ASTNode
    content: ASTNode


@dataclass
class FileClose(ASTNode):
    """Закрытие файла: close(file)"""
    file: ASTNode