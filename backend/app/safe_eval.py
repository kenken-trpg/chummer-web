"""Small, bounded interpreters for arithmetic and boolean expressions.

Input expressions come from Chummer XML and user-uploaded custom data. Python's
``eval`` is intentionally not used: this module accepts only the AST nodes each
caller explicitly needs, and bounds parse size, tree size and numeric results.
"""

from __future__ import annotations

import ast
import math
import operator
import warnings
from collections.abc import Callable, Collection

MAX_EXPRESSION_LENGTH = 512
MAX_AST_NODES = 128
MAX_AST_DEPTH = 32
MAX_ABS_NUMBER = 1e100

#: the operators a caller may allow; any other is refused, never computed as something else
_ARITHMETIC: dict[type[ast.operator], Callable[[float, float], float]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
}

_COMPARISONS: dict[type[ast.cmpop], Callable[[float, float], bool]] = {
    ast.Eq: lambda left, right: left == right,
    ast.NotEq: lambda left, right: left != right,
    ast.Lt: lambda left, right: left < right,
    ast.LtE: lambda left, right: left <= right,
    ast.Gt: lambda left, right: left > right,
    ast.GtE: lambda left, right: left >= right,
}


class UnsafeExpression(ValueError):
    """The expression is outside the bounded arithmetic language."""


def _bounded_number(value: int | float) -> float:
    try:
        number = float(value)
    except (OverflowError, ValueError) as exc:
        raise UnsafeExpression("number is outside the supported range") from exc
    if not math.isfinite(number) or abs(number) > MAX_ABS_NUMBER:
        raise UnsafeExpression("number is outside the supported range")
    return number


def evaluate_arithmetic(
    expression: str,
    *,
    allow_comparisons: bool = False,
    allow_int: bool = False,
    allowed_ops: Collection[type[ast.operator]] | None = None,
) -> float | bool:
    """Evaluate numbers, unary signs and a bounded set of arithmetic nodes.

    Comparisons and ``int(...)`` are opt-in for the Chummer formula dialect.
    Power, floor division, attributes, names and all other calls are rejected.
    """
    tree = _parse(expression, "invalid expression")
    operations = set(allowed_ops if allowed_ops is not None else _ARITHMETIC) & _ARITHMETIC.keys()
    evaluator = _Arithmetic(operations, allow_comparisons=allow_comparisons, allow_int=allow_int)
    try:
        return evaluator.walk(tree)
    except (ArithmeticError, OverflowError, RecursionError) as exc:
        raise UnsafeExpression("arithmetic failed") from exc


def _parse(expression: str, invalid: str) -> ast.Expression:
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise UnsafeExpression("expression is too long")
    try:
        # An invalid escape in a string literal makes the parser warn on
        # stderr; uploaded data must not be able to write to the server log.
        with warnings.catch_warnings(action="ignore"):
            return ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise UnsafeExpression(invalid) from exc


class _Walker:
    """Counts every node visited and how deep, and refuses past the bounds."""

    def __init__(self) -> None:
        self.visited = 0

    def enter(self, depth: int) -> None:
        self.visited += 1
        if self.visited > MAX_AST_NODES or depth > MAX_AST_DEPTH:
            raise UnsafeExpression("expression is too complex")


class _Arithmetic(_Walker):
    def __init__(self, operations: set[type[ast.operator]], *, allow_comparisons: bool, allow_int: bool) -> None:
        super().__init__()
        self.operations = operations
        self.allow_comparisons = allow_comparisons
        self.allow_int = allow_int

    def walk(self, node: ast.AST, depth: int = 0) -> float | bool:
        self.enter(depth)
        if isinstance(node, ast.Expression):
            return self.walk(node.body, depth + 1)
        if isinstance(node, ast.Constant) and isinstance(node.value, int | float) and not isinstance(node.value, bool):
            return _bounded_number(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub | ast.UAdd):
            inner = self.number(node.operand, depth, "boolean arithmetic is not allowed")
            return _bounded_number(-inner if isinstance(node.op, ast.USub) else inner)
        if isinstance(node, ast.BinOp) and type(node.op) in self.operations:
            left, right = self.walk(node.left, depth + 1), self.walk(node.right, depth + 1)
            if isinstance(left, bool) or isinstance(right, bool):
                raise UnsafeExpression("boolean arithmetic is not allowed")
            return _bounded_number(_ARITHMETIC[type(node.op)](left, right))
        if isinstance(node, ast.Call) and self.allow_int and _is_int_call(node):
            return _bounded_number(int(self.number(node.args[0], depth, "int() needs a number")))
        if isinstance(node, ast.Compare) and self.allow_comparisons:
            return self.compare(node, depth)
        raise UnsafeExpression(f"unsupported expression node: {type(node).__name__}")

    def number(self, node: ast.AST, depth: int, refusal: str) -> float:
        """A child that must be a number, not the result of a comparison."""
        value = self.walk(node, depth + 1)
        if isinstance(value, bool):
            raise UnsafeExpression(refusal)
        return value

    def compare(self, node: ast.Compare, depth: int) -> bool:
        left = self.number(node.left, depth, "comparison needs numbers")
        for operator_node, comparator in zip(node.ops, node.comparators, strict=True):
            compare = _COMPARISONS.get(type(operator_node))
            right = self.walk(comparator, depth + 1)
            if compare is None or isinstance(right, bool):
                raise UnsafeExpression("unsupported comparison")
            if not compare(left, right):
                return False
            left = right
        return True


def _is_int_call(node: ast.Call) -> bool:
    return isinstance(node.func, ast.Name) and node.func.id == "int" and len(node.args) == 1 and not node.keywords


def evaluate_boolean(expression: str) -> bool:
    """Evaluate only ``True``/``False`` joined by ``and``/``or`` and groups."""
    tree = _parse(expression, "invalid boolean expression")
    walker = _Walker()

    def walk(node: ast.AST, depth: int = 0) -> bool:
        walker.enter(depth)
        if isinstance(node, ast.Expression):
            return walk(node.body, depth + 1)
        if isinstance(node, ast.Constant) and isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And | ast.Or):
            values = [walk(value, depth + 1) for value in node.values]
            return all(values) if isinstance(node.op, ast.And) else any(values)
        raise UnsafeExpression(f"unsupported boolean node: {type(node).__name__}")

    return walk(tree)
