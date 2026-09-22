"""Shared request-body guards for the models."""

from __future__ import annotations

import re

from pydantic import BaseModel

# The client POSTs the whole CharacterState / CharacterPatch on every call and
# it is fed straight into compute(). MAX_REQUEST_BYTES caps the transfer; this
# caps how many rows a single 12 MiB body can make the engine chew through. A
# real character is well under this in any one collection.
_MAX_COLLECTION = 2000

# JSON numbers have no size limit and Python ints none either, so a rating of
# 10**400 validates as an int and then raises OverflowError the first time the
# engine turns it into a float — a 500 rather than a 422. A trillion is far
# above any nuyen, karma or rating a character holds, and far below where a
# float stops being able to hold the products the engine takes of them.
MAX_INPUT_INT = 10**12

# The portrait goes straight into an <img src>. Only an inline raster image is
# a portrait: an http(s) URL would make every viewer of a shared or imported
# character fetch from a third party (a tracking pixel wherever the bundled
# CSP is not in front), and SVG is a document format rather than a picture.
_PORTRAIT = re.compile(r"data:image/(?:png|jpeg|gif|webp);base64,[A-Za-z0-9+/]*={0,2}")

# The editor refuses a file over 3 MB (`onPortraitFile`); base64 makes that 4
# MB of text. The same cap here covers the routes that skip the editor — a
# chum5 import, a JSON import, a hand-made patch — where a portrait of any
# size would otherwise ride along on every save, export and API response.
MAX_PORTRAIT_CHARS = 4_000_000 + len("data:image/jpeg;base64,")


def clean_portrait(value: str) -> str:
    """`value` if it is a base64 PNG / JPEG / GIF / WebP data: URI no longer
    than `MAX_PORTRAIT_CHARS`, else "".

    Whitespace is dropped first: a base64 body wrapped across lines is still
    the same image.
    """
    compact = re.sub(r"\s+", "", value)
    if len(compact) > MAX_PORTRAIT_CHARS:
        return ""
    return compact if _PORTRAIT.fullmatch(compact) else ""


#: Chummer's `<mugshots>` holds any number; three is what this app keeps —
#: `portrait` (the main one) and up to two more in `extra_portraits`.
MAX_PORTRAITS = 3


def clean_extra_portraits(values: list[str]) -> list[str]:
    """`values` run through `clean_portrait`, the refused ones dropped, cut to
    the `MAX_PORTRAITS - 1` that fit beside the main portrait."""
    return [c for c in (clean_portrait(v) for v in values) if c][: MAX_PORTRAITS - 1]


def _reject_oversized_collections(model: BaseModel) -> None:
    """Hold every list / dict in `model` to `_MAX_COLLECTION`, nested ones too,
    and every int to `MAX_INPUT_INT` either side of zero.

    Only the top level used to be checked, so a drug's parts, a gear piece's
    `array_order` or the settings' `books` could each carry every row the
    body limit allows.
    """
    _walk(model, "")


def _reject_oversized_input(data: object) -> object:
    """`_reject_oversized_collections` on the raw body, before any field is
    validated.

    Run after validation only, a body of 200,000 malformed rows was validated
    row by row first: ~5 s of CPU, and a 422 listing every one of them — 89 MB
    back for a 4 MB request. Checked on the raw JSON it is one error, sent
    before the rows are looked at.
    """
    _walk(data, "")
    return data


def _walk(value: object, path: str) -> None:
    # A stack, not recursion: the raw body can nest as deep as the JSON parser
    # allows, and a RecursionError here would be a 500.
    stack: list[tuple[object, str]] = [(value, path)]
    while stack:
        value, path = stack.pop()
        if isinstance(value, BaseModel):
            stack.extend((child, f"{path}.{name}" if path else name) for name, child in value.__dict__.items())
        elif isinstance(value, dict):
            if len(value) > _MAX_COLLECTION:
                raise ValueError(f"{path}: {len(value)} entries exceeds the {_MAX_COLLECTION} cap")
            # Keys of a raw body name fields; a model's dict fields keep the
            # path they were reached by.
            stack.extend((child, f"{path}.{k}" if path else str(k)) for k, child in value.items())
        elif isinstance(value, list):
            if len(value) > _MAX_COLLECTION:
                raise ValueError(f"{path}: {len(value)} entries exceeds the {_MAX_COLLECTION} cap")
            stack.extend((child, path) for child in value)
        elif isinstance(value, int) and not isinstance(value, bool) and abs(value) > MAX_INPUT_INT:
            raise ValueError(f"{path}: a number beyond ±{MAX_INPUT_INT} exceeds the cap")


def clamp_input_ints(value: object) -> object:
    """`value` with every int held to `MAX_INPUT_INT` either side of zero.

    An import reads a stranger's file, and a hand-edited `<karma>10**26</karma>`
    survives the read as a number the models then refuse — a 500 where the
    import owes either a state that computes or a refusal with a reason. The
    readers compose their numbers (an attribute is its minimum plus its base
    plus its karma), so a clamp on each field as it is read would still leave a
    sum past the cap; this runs once on the finished state instead.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return max(-MAX_INPUT_INT, min(MAX_INPUT_INT, value))
    if isinstance(value, dict):
        return {k: clamp_input_ints(v) for k, v in value.items()}
    if isinstance(value, list):
        return [clamp_input_ints(v) for v in value]
    return value
