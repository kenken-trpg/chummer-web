"""Small, bounded interpreters for arithmetic and boolean expressions.

Input expressions come from Chummer XML and user-uploaded custom data. Python's
``eval`` is intentionally not used: this module accepts only the AST nodes each
caller explicitly needs, and bounds parse size, tree size and numeric results.
"""

from __future__ import annotations

import ast
import math
from collections.abc import Callable, Collection

MAX_EXPRESSION_LENGTH = 512
MAX_AST_NODES = 128
MAX_AST_DEPTH = 32
MAX_ABS_NUMBER = 1e100

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
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise UnsafeExpression("expression is too long")
    operations = set(allowed_ops if allowed_ops is not None else (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod))
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise UnsafeExpression("invalid expression") from exc

    visited = 0

    def walk(node: ast.AST, depth: int = 0) -> float | bool:
        nonlocal visited
        visited += 1
        if visited > MAX_AST_NODES or depth > MAX_AST_DEPTH:
            raise UnsafeExpression("expression is too complex")

        if isinstance(node, ast.Expression):
            return walk(node.body, depth + 1)
        if isinstance(node, ast.Constant) and isinstance(node.value, int | float) and not isinstance(node.value, bool):
            return _bounded_number(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub | ast.UAdd):
            inner = walk(node.operand, depth + 1)
            if isinstance(inner, bool):
                raise UnsafeExpression("boolean arithmetic is not allowed")
            return _bounded_number(-inner if isinstance(node.op, ast.USub) else inner)
        if isinstance(node, ast.BinOp) and type(node.op) in operations:
            left, right = walk(node.left, depth + 1), walk(node.right, depth + 1)
            if isinstance(left, bool) or isinstance(right, bool):
                raise UnsafeExpression("boolean arithmetic is not allowed")
            if isinstance(node.op, ast.Add):
                result = left + right
            elif isinstance(node.op, ast.Sub):
                result = left - right
            elif isinstance(node.op, ast.Mult):
                result = left * right
            elif isinstance(node.op, ast.Div):
                result = left / right
            else:
                result = left % right
            return _bounded_number(result)
        if isinstance(node, ast.Call) and allow_int:
            if isinstance(node.func, ast.Name) and node.func.id == "int" and len(node.args) == 1 and not node.keywords:
                value = walk(node.args[0], depth + 1)
                if isinstance(value, bool):
                    raise UnsafeExpression("int() needs a number")
                return _bounded_number(int(value))
        if isinstance(node, ast.Compare) and allow_comparisons:
            left = walk(node.left, depth + 1)
            if isinstance(left, bool):
                raise UnsafeExpression("comparison needs numbers")
            for operator, comparator in zip(node.ops, node.comparators, strict=True):
                compare = _COMPARISONS.get(type(operator))
                right = walk(comparator, depth + 1)
                if compare is None or isinstance(right, bool):
                    raise UnsafeExpression("unsupported comparison")
                if not compare(left, right):
                    return False
                left = right
            return True
        raise UnsafeExpression(f"unsupported expression node: {type(node).__name__}")

    try:
        return walk(tree)
    except (ArithmeticError, OverflowError, RecursionError) as exc:
        raise UnsafeExpression("arithmetic failed") from exc


def evaluate_boolean(expression: str) -> bool:
    """Evaluate only ``True``/``False`` joined by ``and``/``or`` and groups."""
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise UnsafeExpression("expression is too long")
    try:
        tree = ast.parse(expression, mode="eval")
    except (SyntaxError, ValueError, RecursionError) as exc:
        raise UnsafeExpression("invalid boolean expression") from exc

    visited = 0

    def walk(node: ast.AST, depth: int = 0) -> bool:
        nonlocal visited
        visited += 1
        if visited > MAX_AST_NODES or depth > MAX_AST_DEPTH:
            raise UnsafeExpression("expression is too complex")
        if isinstance(node, ast.Expression):
            return walk(node.body, depth + 1)
        if isinstance(node, ast.Constant) and isinstance(node.value, bool):
            return node.value
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.And | ast.Or):
            values = [walk(value, depth + 1) for value in node.values]
            return all(values) if isinstance(node.op, ast.And) else any(values)
        raise UnsafeExpression(f"unsupported boolean node: {type(node).__name__}")

    return walk(tree)
