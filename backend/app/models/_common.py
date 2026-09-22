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


def _walk(value: object, path: str) -> None:
    if isinstance(value, BaseModel):
        for name, child in value.__dict__.items():
            _walk(child, f"{path}.{name}" if path else name)
    elif isinstance(value, (list, dict)):
        if len(value) > _MAX_COLLECTION:
            raise ValueError(f"{path}: {len(value)} entries exceeds the {_MAX_COLLECTION} cap")
        for child in value.values() if isinstance(value, dict) else value:
            _walk(child, path)
