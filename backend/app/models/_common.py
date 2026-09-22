"""Shared request-body guards for the models."""

from __future__ import annotations

import re

from pydantic import BaseModel

# The client POSTs the whole CharacterState / CharacterPatch on every call and
# it is fed straight into compute(). MAX_REQUEST_BYTES caps the transfer; this
# caps how many rows a single 12 MiB body can make the engine chew through. A
# real character is well under this in any one collection.
_MAX_COLLECTION = 2000

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


def _reject_oversized_collections(model: BaseModel) -> None:
    """Hold every list / dict in `model` to `_MAX_COLLECTION`, nested ones too.

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
