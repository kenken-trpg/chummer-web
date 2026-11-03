"""Chummer's rich-text boxes come in as plain text (app/chummer_import/rtf.py)."""

from __future__ import annotations

from app.chummer_import import chum5_to_state
from app.chummer_import.rtf import rtf_to_text
from tests.test_chummer_import import SAMPLE


def _hex(text: str, codepage: str) -> str:
    return "".join(f"\\'{b:02x}" for b in text.encode(codepage))


#: what a RichTextBox on Japanese Windows writes: the text in cp932 bytes
JA_RTF = (
    "{\\rtf1\\ansi\\ansicpg932\\deff0\\nouicompat\\deflang1033\\deflangfe1041"
    "{\\fonttbl{\\f0\\fnil\\fcharset128 " + _hex("ＭＳ Ｐゴシック", "cp932") + ";}}\r\n"
    "{\\*\\generator Riched20 10.0.19041}\\viewkind4\\uc1 \r\n"
    "\\pard\\f0\\fs18\\lang1041 "
    + _hex("銀髪の小柄な吸血鬼", "cp932")
    + "\\par\r\n"
    + _hex("左頬に傷", "cp932")
    + " & {\\b bold}\\par\r\n}\r\n"
)


def test_not_rtf_is_left_alone() -> None:
    for text in ("", "plain text", "銀髪\n\n左頬に傷", "{not rtf}"):
        assert rtf_to_text(text) == text


def test_japanese_bytes_in_the_document_code_page() -> None:
    assert rtf_to_text(JA_RTF) == "銀髪の小柄な吸血鬼\n左頬に傷 & bold"


def test_font_charset_wins_over_an_english_code_page() -> None:
    # English Windows: the document is cp1252, the font says Shift-JIS
    rtf = (
        "{\\rtf1\\ansi\\ansicpg1252\\deff0{\\fonttbl{\\f0\\fnil\\fcharset0 Arial;}"
        "{\\f1\\fnil\\fcharset128 MS Gothic;}}\\pard\\f0 Caf\\'e9 \\f1 " + _hex("牙", "cp932") + "\\par}"
    )
    assert rtf_to_text(rtf) == "Café 牙"


def test_unicode_escapes_skip_their_fallback() -> None:
    rtf = "{\\rtf1\\ansi\\uc1\\u37504?\\u39658?\\uc2\\u-3913??x\\par}"
    assert rtf_to_text(rtf) == "銀髪\uf0b7x"


def test_breaks_escapes_and_skipped_groups() -> None:
    rtf = (
        "{\\rtf1\\ansi{\\colortbl;\\red0\\green0\\blue0;}{\\*\\listtable{x}}"
        "a\\tab b\\line c\\{d\\}\\\\e\\~f\\par\\par g   \\par\\par}"
    )
    assert rtf_to_text(rtf) == "a\tb\nc{d}\\e\u00a0f\n\ng"


def test_chum5_import_turns_the_rich_text_boxes_into_text() -> None:
    fields = "".join(
        f"<{tag}>{JA_RTF.replace('&', '&amp;')}</{tag}>"
        for tag in ("description", "background", "concept", "notes", "gamenotes")
    )
    xml = SAMPLE.replace(b"</character>", fields.encode() + b"</character>")
    st, _ = chum5_to_state(xml)
    for field in ("appearance", "background", "concept", "notes", "game_notes"):
        assert st[field] == "銀髪の小柄な吸血鬼\n左頬に傷 & bold", field
