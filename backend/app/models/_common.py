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


def clean_portrait(value: str) -> str:
    """`value` if it is a base64 PNG / JPEG / GIF / WebP data: URI, else "".

    Whitespace is dropped first: a base64 body wrapped across lines is still
    the same image.
    """
    compact = re.sub(r"\s+", "", value)
    return compact if _PORTRAIT.fullmatch(compact) else ""


def _reject_oversized_collections(model: BaseModel) -> None:
    for name, value in model.__dict__.items():
        if isinstance(value, (list, dict)) and len(value) > _MAX_COLLECTION:
            raise ValueError(f"{name}: {len(value)} entries exceeds the {_MAX_COLLECTION} cap")
