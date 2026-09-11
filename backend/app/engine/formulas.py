"""Pure string / number helpers for stat expressions (armor values, damage
codes, leading-integer tweaks, STR/AGI token substitution). No engine imports
beyond ``eval_formula``.
"""

from __future__ import annotations

import math
import re

from ..data_loader import eval_formula


def _ceil_div(n: float) -> int:
    return int(math.ceil(n))


def parse_armor_value(raw: str, rating: int = 1) -> tuple[int, bool]:
    text = (raw or "0").strip()
    additive = text.startswith("+") or text.startswith("-")
    if text.lower() == "rating":
        return int(rating), False
    try:
        return int(float(text)), additive
    except ValueError:
        return int(eval_formula(text, rating, 0)), additive


def _add_signed_stat(raw: str | None, delta: int) -> str:
    text = str(raw or "").strip()
    if not delta:
        return text
    match = re.match(r"^([+-]?\d+)(.*)$", text)
    if match:
        return f"{int(match.group(1)) + delta}{match.group(2)}"
    if text in {"", "-", "—"}:
        return str(delta)
    return text


def _set_damage_type(damage: str, dtype: str) -> str:
    match = re.match(r"^([+-]?\d+)(.*)$", str(damage or "").strip())
    if not match:
        return dtype
    return f"{match.group(1)}{dtype}"


_ATTR_TOKEN = re.compile(r"\{(STR|AGI|MAG)(?:Unaug|Base)?\}", re.I)


#: Chummer's ``number(cond)`` — 1 when the comparison holds, else 0 (Osmium
#: Mace, TCT p.185: ``3+number({STR} >= 5)+number({STR} >= 7)``).
_NUMBER_TEST = re.compile(r"number\(\s*(-?\d+)\s*(>=|<=|==|>|<)\s*(-?\d+)\s*\)")
_COMPARE = {
    ">=": lambda a, b: a >= b,
    "<=": lambda a, b: a <= b,
    "==": lambda a, b: a == b,
    ">": lambda a, b: a > b,
    "<": lambda a, b: a < b,
}


def _number_test(match: re.Match[str]) -> str:
    left, op, right = int(match.group(1)), match.group(2), int(match.group(3))
    return "1" if _COMPARE[op](left, right) else "0"


def _eval_attr_stat(raw: str, attrs: dict[str, int]) -> str:
    text = str(raw or "")
    if "{" not in text:
        return text
    values = {key.upper(): int(val) for key, val in attrs.items()}

    def _token(match: re.Match[str]) -> str:
        return str(values.get(match.group(1).upper(), 0))

    replaced = _NUMBER_TEST.sub(_number_test, _ATTR_TOKEN.sub(_token, text))
    if "{" in replaced:
        return text

    def _try_eval(expr: str) -> str | None:
        compact = expr.replace(" ", "")
        if not re.fullmatch(r"[0-9+\-*/().]+", compact):
            return None
        try:
            return str(int(eval(compact, {"__builtins__": {}}, {})))
        except Exception:
            return None

    out = replaced
    while True:

        def _inner(match: re.Match[str]) -> str:
            value = _try_eval(match.group(1))
            return value if value is not None else match.group(0)

        nxt = re.sub(r"\(([0-9+\-*/. ]+)\)", _inner, out)
        if nxt == out:
            break
        out = nxt
    # a bare sum left at the top (`3+1+0`) — but not a signed number (`+1` AP)
    if re.search(r"\d\s*[+\-*/]\s*\d", out):
        return _try_eval(out) or out
    return out


def _leading_int(raw: str | None) -> int | None:
    match = re.match(r"^([+-]?\d+)", str(raw or "").strip())
    if not match:
        return None
    return int(match.group(1))


def _add_leading_int(raw: str | None, delta: int) -> str:
    text = str(raw or "").strip()
    if not delta:
        return text
    match = re.match(r"^([+-]?\d+)(.*)$", text)
    if not match:
        return text
    return f"{int(match.group(1)) + delta}{match.group(2)}"


def _add_accuracy(raw: str | None, delta: int) -> str:
    """:func:`_add_leading_int`, plus the limit-based Accuracy of natural and
    ware weapons (``Physical-1`` for a Raptor Foot): the offset moves, the
    limit stays a word — it is resolved nowhere else either."""
    text = str(raw or "").strip()
    match = re.match(r"^([A-Za-z]+)\s*([+-]\s*\d+)?$", text)
    if not delta or not match:
        return _add_leading_int(text, delta)
    offset = int((match.group(2) or "0").replace(" ", "")) + delta
    return match.group(1) + (f"{offset:+d}" if offset else "")


def _replace_leading_int(raw: str | None, value: int) -> str:
    text = str(raw or "").strip()
    match = re.match(r"^([+-]?\d+)(.*)$", text)
    if not match:
        return str(value)
    return f"{int(value)}{match.group(2)}"


def _add_weapon_dv(raw: str | None, delta: int) -> str:
    text = str(raw or "").strip()
    if not delta:
        return text
    match = re.search(r"([+-]?\d+)(?=[^0-9]*$)", text)
    if match:
        start, end = match.span(1)
        token = match.group(1)
        new_val = int(token) + delta
        if token.startswith("+") and new_val >= 0:
            replacement = f"+{new_val}"
        else:
            replacement = str(new_val)
        return f"{text[:start]}{replacement}{text[end:]}"
    type_match = re.match(r"^(.*?)([PS].*)$", text)
    if type_match:
        sign = "+" if delta > 0 else ""
        return f"{type_match.group(1)}{sign}{delta}{type_match.group(2)}"
    return f"{text}+{delta}" if delta > 0 else f"{text}{delta}"
