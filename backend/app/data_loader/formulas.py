"""SR5 formula evaluation + availability / capacity string parsing.

Pure string maths, stdlib-only. Every loader (and the engine) leans on
``eval_formula``.
"""

from __future__ import annotations

import re


def eval_formula(
    expr: str | None,
    rating: int = 1,
    default: float = 0.0,
    extras: dict[str, int | float] | None = None,
) -> float:
    raw = (expr or "").strip()
    if not raw:
        return default
    env: dict[str, int | float] = {**(extras or {}), "Rating": int(rating)}
    env.setdefault("rating", int(rating))
    lookup = {str(key).lower(): value for key, value in env.items()}
    for key in sorted(env, key=len, reverse=True):
        raw = raw.replace("{" + str(key) + "}", str(env[key]))
    if re.search(r"[{}]", raw):
        return default
    if raw in env:
        return float(env[raw])
    if raw.lower() in lookup:
        return float(lookup[raw.lower()])
    fixed = re.fullmatch(r"FixedValues\((.+)\)", raw, re.I)
    if fixed:
        parts = [p.strip() for p in fixed.group(1).split(",")]
        idx = max(0, min(len(parts) - 1, int(rating) - 1))
        return eval_formula(parts[idx], rating, default, extras)

    def _subst_keys(text: str) -> str:
        out = text
        for key in sorted(env, key=len, reverse=True):
            out = out.replace(str(key), str(env[key]))
        return out

    def _number_repl(match: re.Match[str]) -> str:
        inner = _subst_keys(match.group(1)).replace(" ", "")
        inner = re.sub(r"(?<![<>!=])=(?!=)", "==", inner)
        try:
            if re.search(r"==|!=|<=|>=|<|>", inner):
                return "1" if bool(eval(inner, {"__builtins__": {}}, {})) else "0"
            return str(int(float(eval(inner, {"__builtins__": {}}, {"int": int}))))
        except Exception:
            return "0"

    raw = re.sub(r"number\(([^)]+)\)", _number_repl, raw, flags=re.I)
    s = _subst_keys(raw)
    s = re.sub(r"[RF]$", "", s.strip())
    s = re.sub(r"\bmod\b", "%", s, flags=re.I)
    s = s.replace(" ", "")
    if not re.fullmatch(r"[0-9+\-*/().><=%int]+", s):
        try:
            return float(s)
        except ValueError:
            return default
    try:
        return float(eval(s, {"__builtins__": {}}, {"int": int}))
    except Exception:
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
