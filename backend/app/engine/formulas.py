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


_ATTR_TOKEN = re.compile(r"\{(STR|AGI)(?:Unaug|Base)?\}", re.I)


def _eval_attr_stat(raw: str, attrs: dict[str, int]) -> str:
    text = str(raw or "")
    if "{" not in text:
        return text
    values = {key.upper(): int(val) for key, val in attrs.items()}

    def _token(match: re.Match[str]) -> str:
        return str(values.get(match.group(1).upper(), 0))

    replaced = _ATTR_TOKEN.sub(_token, text)
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
