"""A bonus's values worked out at its owner's rating, as Chummer works them out."""

from __future__ import annotations

import ast
import re
import xml.etree.ElementTree as ET
from copy import deepcopy


def _rated(bonus: ET.Element, rating: int) -> ET.Element:
    """A copy of `bonus` with every value that depends on the rating worked
    out, as `ImprovementManager.ValueToDec` does: `Rating`, `{Rating}`,
    `FixedValues(3,6,9)` (the rating-th), `number(Rating >= 2)` and plain
    arithmetic of them. A value that comes out fractional is left as it was,
    so it makes nothing."""
    out = deepcopy(bonus)
    for el in out.iter():
        text = (el.text or "").strip()
        if not text or not re.search(r"Rating|FixedValues", text):
            continue
        text = re.sub(
            r"FixedValues\(([^)]*)\)",
            lambda m: m.group(1).split(",")[max(0, min(rating, len(m.group(1).split(","))) - 1)].strip(),
            text,
        )
        text = re.sub(
            r"number\(\s*\{?Rating\}?\s*>=\s*(\d+)\s*\)", lambda m: "1" if rating >= int(m.group(1)) else "0", text
        )
        text = re.sub(r"\{?Rating\}?", str(rating), text)
        if re.fullmatch(r"[\d\s+\-*/().]+", text):
            value = _arithmetic(ast.parse(text, mode="eval").body)
            if value is not None and float(value).is_integer():
                el.text = str(int(value))
    return out


def _arithmetic(node: ast.expr) -> float | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return float(node.value)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        inner = _arithmetic(node.operand)
        return None if inner is None else -inner
    if isinstance(node, ast.BinOp):
        left, right = _arithmetic(node.left), _arithmetic(node.right)
        if left is None or right is None:
            return None
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div) and right:
            return left / right
    return None
