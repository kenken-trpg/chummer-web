"""The `.chum5lz` container: every way a save arrives compressed, each one bounded."""

from __future__ import annotations

import lzma
import os
import zlib

from ..notices import NoticeError, notice

# Upper bound on the decompressed size of a .chum5lz payload — a guard against
# decompression bombs on the import endpoint. A real Chummer save (even with
# base64 portraits) is a few MB; the default sits well clear of that.
_MAX_DECOMPRESSED_BYTES = int(os.environ.get("CHUM5_MAX_DECOMPRESSED_BYTES") or 32 * 1024 * 1024)


def _bounded_lzma(raw: bytes, fmt: int) -> bytes:
    d = lzma.LZMADecompressor(format=fmt)
    out = d.decompress(raw, _MAX_DECOMPRESSED_BYTES + 1)
    if len(out) > _MAX_DECOMPRESSED_BYTES or not d.eof:
        raise ValueError("decompressed .chum5lz exceeds the size limit")
    return out


def _bounded_zlib(raw: bytes, wbits: int) -> bytes:
    d = zlib.decompressobj(wbits)
    out = d.decompress(raw, _MAX_DECOMPRESSED_BYTES + 1)
    if d.unconsumed_tail:
        raise ValueError("decompressed .chum5lz exceeds the size limit")
    out += d.flush()
    if len(out) > _MAX_DECOMPRESSED_BYTES:
        raise ValueError("decompressed .chum5lz exceeds the size limit")
    return out


def decompress_chum5lz(raw: bytes | str) -> bytes:
    """Return the inner XML bytes from a ``.chum5`` / ``.chum5lz`` payload.

    Plain XML is returned as-is. Chummer5a's ``.chum5lz`` (LzmaHelper.cs
    ``CompressToLzmaFile``) is the legacy ``.lzma`` "alone" container: a 5-byte
    LZMA property header, an 8-byte little-endian uncompressed size (``0xFF``*8
    when written with an end marker), then a raw LZMA1 stream — i.e. Python's
    ``lzma.FORMAT_ALONE``. xz / zlib / gzip are also tried as a courtesy.

    Every branch is bounded to ``_MAX_DECOMPRESSED_BYTES`` so a crafted payload
    cannot expand without limit (decompression bomb).
    """
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    head = raw.lstrip()[:64].lstrip(b"\xef\xbb\xbf").lstrip()
    if head.startswith(b"<"):  # already plain XML
        return raw
    errors: list[str] = []  # exception class names, for the failure message
    for attempt in (
        lambda: _bounded_lzma(raw, lzma.FORMAT_ALONE),  # Chummer's format
        lambda: _bounded_lzma(raw, lzma.FORMAT_AUTO),  # xz / auto
        lambda: _bounded_zlib(raw, zlib.MAX_WBITS),
        lambda: _bounded_zlib(raw, -zlib.MAX_WBITS),
        lambda: _bounded_zlib(raw, zlib.MAX_WBITS | 16),  # gzip
    ):
        try:
            out = attempt()
            if out.lstrip()[:16].lower().startswith((b"<?xml", b"<character", b"\xef\xbb\xbf")):
                return out
        except Exception as exc:  # noqa: BLE001 - trying formats
            errors.append(type(exc).__name__)
    raise NoticeError(notice("api.chum5lzUndecompressible", formats=", ".join(dict.fromkeys(errors))))
