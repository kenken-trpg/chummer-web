#!/usr/bin/env python3
"""Generate the TypeScript view of `app.models` into the frontend.

The character state crosses the wire as JSON, so the browser needs the same
shape the Pydantic models describe. That shape used to be typed twice — once in
`app/models.py`, once by hand in `frontend/lib/types/` — and the two drifted
(`SpellInstall.alchemical` and `.source_quality_id` never reached the browser).
This writes the TypeScript half from the Python one instead.

    python scripts/gen_frontend_types.py           # write the file
    python scripts/gen_frontend_types.py --check    # fail if it is stale (CI)

Only the state models are generated. The derived bundle and the catalog are
plain dicts on the Python side, so there is nothing to generate them from;
`derived.ts` and `catalog.ts` stay hand-written.
"""

from __future__ import annotations

import argparse
import ast
import sys
import types
import typing
from pathlib import Path
from typing import Any, Union, get_args, get_origin

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pydantic import BaseModel  # noqa: E402

from app import models  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "frontend/lib/types/generated.ts"

#: Python class -> TypeScript name, where the browser already had its own word
#: for the thing. Renaming the Python class instead would touch far more code.
RENAMES = {
    "CyberwareInstall": "WareInstall",
    "SettingsState": "CharacterSettings",
    "CharacterState": "Character",
}

#: Fields the browser types more tightly than Python does. `Priorities` is five
#: `str` attributes on the Python side; the browser has had the letters as a
#: union since the start and the pickers rely on it.
OVERRIDES = {
    ("CharacterState", "priorities"): "Record<PriorityCategory, PriorityLetter>",
    ("CharacterState", "build_method"): '"Priority" | "SumToTen" | "Karma" | string',
    ("InitiationChoice", "kind"): '"metamagic" | "art" | string',
    # `dict[str, Any]` on the Python side, but the engine's own output: the
    # top-level keys are `DerivedDict`, the row lists under them are not typed
    # there at all, so the browser keeps the richer hand-written shape.
    ("CharacterState", "derived"): "Derived",
}

#: Emitted in this order; `Priorities` is dropped because `OVERRIDES` replaces
#: its only use, and the request/response wrappers never reach the browser.
SKIP = {"Priorities", "StateRequest", "PatchRequest", "CharacterCreate", "CustomDataUpload", "CharacterPatch"}

#: TypeScript's `?` says "may be omitted", and these models are read and
#: written from the browser, so a defaulted field has to be optional — except
#: for these, which the reading code has always taken for granted because
#: `assemble` always fills them in. `id` is deliberately *not* here: the
#: browser really does build rows without one and let the server assign it.
ALWAYS_SENT = {
    ("CharacterState", "derived"),
    ("CharacterState", "talent"),
    ("CharacterState", "skills"),
    ("CharacterState", "skill_groups"),
    ("CharacterState", "knowledge_skills"),
    ("CharacterState", "quality_ids"),
}

#: Hand-written types the generated file leans on.
IMPORTED = {"./installs": ("PriorityCategory", "PriorityLetter"), "./derived": ("Derived",)}


def _ts_name(cls: type) -> str:
    return RENAMES.get(cls.__name__, cls.__name__)


def _ts_type(ann: Any) -> str:
    """One Python annotation as TypeScript."""
    origin = get_origin(ann)
    if origin in (Union, types.UnionType):
        parts = [_ts_type(a) for a in get_args(ann) if a is not type(None)]
        out = " | ".join(dict.fromkeys(parts))
        return f"{out} | null" if type(None) in get_args(ann) else out
    if origin in (list, set, tuple):
        inner = _ts_type(get_args(ann)[0])
        return f"({inner})[]" if " " in inner else f"{inner}[]"
    if origin is dict:
        key, value = get_args(ann)
        return f"Record<{_ts_type(key)}, {_ts_type(value)}>"
    if ann in (str, int, float, bool):
        return {str: "string", int: "number", float: "number", bool: "boolean"}[ann]
    if ann is Any or ann is type(None):
        return "unknown" if ann is Any else "null"
    if isinstance(ann, type) and issubclass(ann, BaseModel):
        return _ts_name(ann)
    raise SystemExit(f"gen_frontend_types: no TypeScript for {ann!r}")


def _comments() -> dict[tuple[str, str], list[str]]:
    """The `#` / `#:` lines above each model field, keyed by (class, field).

    Pydantic keeps no trace of them, and they are the only documentation these
    models carry — dropping them on the way out would make the generated file
    worse than the hand-written one it replaces.
    """
    source = Path(models.__file__).read_text(encoding="utf-8").split("\n")
    out: dict[tuple[str, str], list[str]] = {}
    tree = ast.parse("\n".join(source))
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for stmt in node.body:
            if not isinstance(stmt, ast.AnnAssign) or not isinstance(stmt.target, ast.Name):
                continue
            lines: list[str] = []
            i = stmt.lineno - 2  # 0-indexed, the line above
            while i >= 0 and source[i].lstrip().startswith("#"):
                lines.insert(0, source[i].lstrip().lstrip("#").lstrip(":").strip())
                i -= 1
            if lines:
                out[(node.name, stmt.target.id)] = lines
    return out


def _jsdoc(lines: list[str], indent: str = "  ") -> list[str]:
    if len(lines) == 1:
        return [f"{indent}/** {lines[0]} */"]
    body = [f"{indent} *  {line}" for line in lines[1:]]
    return [f"{indent}/** {lines[0]}", *body, f"{indent} */"]


def render() -> str:
    comments = _comments()
    out = [
        "// Generated by backend/scripts/gen_frontend_types.py from app/models.py.",
        "// Do not edit: change the Pydantic model and re-run the script.",
        "",
        *[f'import type {{ {", ".join(names)} }} from "{mod}";' for mod, names in IMPORTED.items()],
        "",
    ]
    for name, cls in vars(models).items():
        if not isinstance(cls, type) or not issubclass(cls, BaseModel) or cls is BaseModel:
            continue
        if cls.__module__ != models.__name__ or name in SKIP or name != cls.__name__:
            continue
        hints = typing.get_type_hints(cls)
        out.append(f"export interface {_ts_name(cls)} {{")
        for field, info in cls.model_fields.items():
            note = comments.get((name, field))
            if note:
                out.extend(_jsdoc(note))
            ts = OVERRIDES.get((name, field)) or _ts_type(hints[field])
            always = (name, field) in ALWAYS_SENT or (None, field) in ALWAYS_SENT
            optional = not info.is_required() and not always
            out.append(f"  {field}{'?' if optional else ''}: {ts};")
        out.append("}")
        out.append("")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if the file on disk is stale")
    args = parser.parse_args()
    text = render()
    if args.check:
        if not OUT.exists() or OUT.read_text(encoding="utf-8") != text:
            print(f"{OUT} is out of date — run backend/scripts/gen_frontend_types.py", file=sys.stderr)
            return 1
        return 0
    OUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
