"""SR5 formula evaluation + availability / capacity string parsing.

Pure string maths, stdlib-only. Every loader (and the engine) leans on
``eval_formula``.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from functools import lru_cache

from ..safe_eval import UnsafeExpression, evaluate_arithmetic

_FIXED_VALUES = re.compile(r"FixedValues\s*\((.*)\)", re.I | re.S)


def _fixed_values_parts(text: str) -> list[str]:
    """Split FixedValues arguments without splitting nested formula commas."""
    parts: list[str] = []
    start = depth = 0
    for index, char in enumerate(text):
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                return []
        elif char == "," and depth == 0:
            parts.append(text[start:index].strip())
            start = index + 1
    if depth:
        return []
    parts.append(text[start:].strip())
    return [part for part in parts if part]


def _replace_number_calls(raw: str, substitute: Callable[[str], str]) -> str:
    """Replace Chummer's ``number(...)`` calls using the bounded evaluator."""
    out: list[str] = []
    cursor = 0
    while True:
        match = re.search(r"\bnumber\s*\(", raw[cursor:], re.I)
        if match is None:
            out.append(raw[cursor:])
            return "".join(out)
        start = cursor + match.start()
        opening = cursor + match.end() - 1
        depth = 1
        end = opening + 1
        while end < len(raw) and depth:
            if raw[end] == "(":
                depth += 1
            elif raw[end] == ")":
                depth -= 1
            end += 1
        if depth:
            raise UnsafeExpression("unclosed number()")
        inner = substitute(raw[opening + 1 : end - 1])
        inner = re.sub(r"\bmod\b", "%", inner, flags=re.I)
        inner = re.sub(r"\bdiv\b", "/", inner, flags=re.I)
        inner = re.sub(r"(?<![<>=!])=(?!=)", "==", inner)
        result = evaluate_arithmetic(inner, allow_comparisons=True, allow_int=True)
        value = "1" if result is True else "0" if result is False else str(int(result))
        out.extend((raw[cursor:start], value))
        cursor = end


def eval_formula(
    expr: str | None,
    rating: int = 1,
    default: float = 0.0,
    extras: Mapping[str, float] | None = None,
) -> float:
    """Pure in its arguments, and the same few thousand catalog strings come
    through every compute, so the answers are memoised."""
    try:
        return _eval_cached(expr, rating, default, tuple(extras.items()) if extras else ())
    except TypeError:  # an unhashable extra
        return _eval_formula(expr, rating, default, extras)


@lru_cache(maxsize=8192)
def _eval_cached(expr: str | None, rating: int, default: float, extras: tuple[tuple[str, float], ...]) -> float:
    return _eval_formula(expr, rating, default, dict(extras))


def _eval_formula(
    expr: str | None,
    rating: int = 1,
    default: float = 0.0,
    extras: Mapping[str, float] | None = None,
) -> float:
    raw = (expr or "").strip()
    if not raw or len(raw) > 512:
        return default
    env: dict[str, int | float] = {**(extras or {}), "Rating": int(rating)}
    env.setdefault("rating", int(rating))
    lookup = {str(key).lower(): value for key, value in env.items()}
    for key in sorted(env, key=len, reverse=True):
        raw = raw.replace("{" + str(key) + "}", str(env[key]))
    if re.search(r"[{}]", raw):
        return default
    if raw in env:
        try:
            return float(evaluate_arithmetic(str(env[raw])))
        except (UnsafeExpression, ValueError, TypeError):
            return default
    if raw.lower() in lookup:
        try:
            return float(evaluate_arithmetic(str(lookup[raw.lower()])))
        except (UnsafeExpression, ValueError, TypeError):
            return default
    fixed = _FIXED_VALUES.fullmatch(raw)
    if fixed:
        parts = _fixed_values_parts(fixed.group(1))
        if not parts:
            return default
        idx = max(0, min(len(parts) - 1, int(rating) - 1))
        return eval_formula(parts[idx], rating, default, extras)

    def _subst_keys(text: str) -> str:
        out = text
        for key in sorted(env, key=len, reverse=True):
            out = out.replace(str(key), str(env[key]))
        return out

    try:
        raw = _replace_number_calls(raw, _subst_keys)
    except (UnsafeExpression, ValueError, TypeError):
        return default
    s = _subst_keys(raw)
    s = re.sub(r"[RF]$", "", s.strip())
    s = re.sub(r"\bmod\b", "%", s, flags=re.I)
    # XPath's division: a yearly contract priced by the month, `5000 div 12`
    s = re.sub(r"\bdiv\b", "/", s, flags=re.I)
    s = s.replace(" ", "")
    try:
        return float(evaluate_arithmetic(s, allow_int=True))
    except (UnsafeExpression, ValueError, TypeError):
        return default


CHARGEN_AVAIL_MAX = 12
CHARGEN_DEVICE_RATING_MAX = 6
CHARGEN_WARE_ATTR_BONUS_MAX = 4


def parse_avail(
    expr: str | None,
    rating: int = 1,
    extras: dict[str, int | float] | None = None,
) -> tuple[int, str, bool]:
    raw = (expr or "").strip()
    if not raw or raw == "-":
        return 0, "", False
    additive = raw.startswith("+")
    if additive:
        raw = raw[1:].lstrip()
    fixed = re.fullmatch(r"FixedValues\((.+)\)", raw, re.I)
    if fixed:
        parts = [part.strip() for part in fixed.group(1).split(",")]
        idx = max(0, min(len(parts) - 1, int(rating) - 1))
        value, suffix, _nested = parse_avail(parts[idx], rating, extras)
        return value, suffix, additive
    suffix = ""
    compact = raw.replace(" ", "")
    if re.search(r"[RF]$", compact, re.I):
        suffix = compact[-1].upper()
        raw = re.sub(r"[RF]\s*$", "", raw, flags=re.I).rstrip()
    value = int(eval_formula(raw, rating, 0, extras))
    return value, suffix, additive


def format_avail(value: int, suffix: str = "") -> str:
    shown = int(value)
    mark = (suffix or "").upper()
    if mark not in {"R", "F"}:
        mark = ""
    if shown <= 0 and not mark:
        return "0"
    return f"{shown}{mark}"


def sum_avail(parts: list[tuple[int, str]]) -> tuple[int, str]:
    total = 0
    suffix = ""
    rank = {"": 0, "R": 1, "F": 2}
    for value, mark in parts:
        total += int(value or 0)
        token = (mark or "").upper()
        if rank.get(token, 0) > rank.get(suffix, 0):
            suffix = token
    return max(0, total), suffix


def parse_capacity(expr: str | None) -> tuple[bool, str]:
    raw = (expr or "").strip()
    if raw.startswith("[") and raw.endswith("]") and "/" not in raw:
        return True, raw[1:-1]
    if "/" in raw:
        return False, raw.split("/", 1)[0].strip()
    return False, raw


def split_capacity(expr: str | None) -> tuple[bool, str, str]:
    raw = (expr or "").strip()
    if not raw:
        return False, "", ""
    if "/" in raw:
        host, rest = raw.split("/", 1)
        rest = rest.strip()
        if rest.startswith("[") and rest.endswith("]"):
            rest = rest[1:-1]
        return False, host.strip(), rest
    if raw.startswith("[") and raw.endswith("]"):
        return True, "", raw[1:-1]
    return False, raw, ""


def _is_variable_cost(cost: str) -> bool:
    return "Variable" in (cost or "")


def variable_cost_range(cost: str | None) -> tuple[int, int] | None:
    """`Variable(lo-hi)`: a price the player sets within the range (a Custom
    Item, Clothing, a Commlink App), or None for a fixed price."""
    match = re.fullmatch(r"\s*Variable\(\s*(\d+)\s*-\s*(\d+)\s*\)\s*", cost or "")
    if not match:
        return None
    lo, hi = int(match.group(1)), int(match.group(2))
    return (min(lo, hi), max(lo, hi))
