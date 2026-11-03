"""RTF as plain text, for the five boxes Chummer keeps as rich text.

Chummer edits a character's description, background, concept, notes and GM
notes in a rich-text box (`Controls/Editors/RtfEditor.cs`) and saves what the
box holds: `{\\rtf1\\ansi\\ansicpg932…\\'8b\\'e2…}`. Its own print sheet runs
that through `RtfToHtml`; this app keeps plain text, so it takes the text out
here. A value that is not RTF (older saves, or one this app wrote) comes back
as it is.

Only what a WinForms RichTextBox writes is handled: groups, control words,
`\\'hh` bytes in the document or font code page, `\\uN` with its `\\ucN`
fallback, paragraph and line breaks. Formatting is dropped.
"""

from __future__ import annotations

import re

__all__ = ["is_rtf", "rtf_to_text"]

_TOKEN = re.compile(
    r"\\([a-zA-Z]+)(-?\d+)? ?"  # control word, with its optional space delimiter
    r"|\\'([0-9a-fA-F]{2})"  # a byte in the current code page
    r"|\\(.)"  # control symbol
    r"|([{}])"
    r"|\r\n|\r|\n"  # raw line breaks are not text in RTF
    r"|([^\\{}\r\n]+)",
    re.DOTALL,
)

#: destinations that hold no text of the document (`\*` groups are skipped too)
_SKIP = frozenset(
    {
        "colortbl",
        "stylesheet",
        "info",
        "pict",
        "object",
        "header",
        "footer",
        "headerl",
        "headerr",
        "footerl",
        "footerr",
        "fldinst",
        "listtable",
        "listoverridetable",
        "rsidtbl",
        "themedata",
        "colorschememapping",
        "datastore",
        "latentstyles",
        "xmlnstbl",
        "generator",
    }
)

#: `\fcharsetN` -> code page (0 and 1 mean "the document's")
_CHARSETS = {
    2: "latin-1",
    77: "mac-roman",
    128: "cp932",
    129: "cp949",
    130: "johab",
    134: "gbk",
    136: "cp950",
    161: "cp1253",
    162: "cp1254",
    163: "cp1258",
    177: "cp1255",
    178: "cp1256",
    186: "cp1257",
    204: "cp1251",
    222: "cp874",
    238: "cp1250",
    255: "cp437",
}


def is_rtf(text: str) -> bool:
    return text.lstrip().startswith("{\\rtf")


_WORD_TEXT = {
    "par": "\n",
    "line": "\n",
    "sect": "\n",
    "row": "\n",
    "tab": "\t",
    "emdash": "\u2014",
    "endash": "\u2013",
    "bullet": "\u2022",
}
_SYMBOL_TEXT = {"\\": "\\", "{": "{", "}": "}", "~": "\u00a0", "\r": "\n", "\n": "\n"}


def rtf_to_text(text: str) -> str:
    """`text` without its RTF markup, or `text` itself when it is not RTF."""
    if not text or not is_rtf(text):
        return text
    reader = _Reader()
    for m in _TOKEN.finditer(text):
        reader.token(*m.groups())
    reader.flush()
    return _tidy("".join(reader.out))


class _Reader:
    """The state a pass over the tokens keeps, group by group."""

    def __init__(self) -> None:
        self.out: list[str] = []
        self.pending = bytearray()  # \'hh bytes, decoded together (a DBCS pair is two)
        self.doc_cp = "cp1252"
        self.font_cp: dict[int, str] = {}
        self.font_no: int | None = None  # the font table entry being read
        self.default_font: int | None = None  # \deffN: the font text is in until a \fN
        # per group: (skipping, unicode fallback length, code page, in the font table)
        self.stack: list[tuple[bool, int, str | None, bool]] = []
        self.skip, self.uc, self.in_fonts = False, 1, False
        self.cp: str | None = None  # the code page of the font in use
        self.to_drop = 0  # fallback characters still to skip after a \uN
        self.star = False  # the destination just opened with \*

    def flush(self) -> None:
        if self.pending:
            fallback = self.font_cp.get(self.default_font) if self.default_font is not None else None
            self.out.append(self.pending.decode(self.cp or fallback or self.doc_cp, errors="replace"))
            self.pending.clear()

    def token(
        self,
        word: str | None,
        arg: str | None,
        hexbyte: str | None,
        symbol: str | None,
        brace: str | None,
        plain: str | None,
    ) -> None:
        if hexbyte is not None:
            if self.to_drop:
                self.to_drop -= 1
            elif not self.skip and not self.in_fonts:
                self.pending.append(int(hexbyte, 16))
            return
        self.flush()
        if brace is not None:
            self.group(brace == "{")
        elif word is not None:
            self.word(word, int(arg) if arg is not None else None)
        elif symbol is not None:
            self.symbol(symbol)
        elif plain is not None and not self.skip and not self.in_fonts:
            dropped = min(self.to_drop, len(plain))
            self.to_drop -= dropped
            self.out.append(plain[dropped:])

    def group(self, opens: bool) -> None:
        if opens:
            self.stack.append((self.skip, self.uc, self.cp, self.in_fonts))
            self.star = False
        elif self.stack:
            self.skip, self.uc, self.cp, self.in_fonts = self.stack.pop()
        self.to_drop = 0

    def word(self, word: str, n: int | None) -> None:
        if self.star or word in _SKIP:
            self.skip = True
        self.star = False
        if word == "fonttbl":
            self.in_fonts = True
        elif self.in_fonts:
            self.font_entry(word, n)
        elif n is not None and self.setting(word, n):
            pass
        elif self.skip:
            pass
        elif word == "u" and n is not None:
            self.out.append(chr(n + 0x10000 if n < 0 else n))
            self.to_drop = self.uc
        elif word in _WORD_TEXT:
            self.out.append(_WORD_TEXT[word])

    def font_entry(self, word: str, n: int | None) -> None:
        if word == "f" and n is not None:
            self.font_no = n
        elif word == "fcharset" and n in _CHARSETS and self.font_no is not None:
            self.font_cp[self.font_no] = _CHARSETS[n]

    def setting(self, word: str, n: int) -> bool:
        """The control words that change how the bytes read; true if `word` was one."""
        if word == "deff":
            self.default_font = n
        elif word == "ansicpg":
            self.doc_cp = f"cp{n}" if n else self.doc_cp
        elif word == "f":
            self.cp = self.font_cp.get(n)
        elif word == "uc":
            self.uc = max(0, n)
        else:
            return False
        return True

    def symbol(self, symbol: str) -> None:
        if symbol == "*":
            self.star = self.skip = True
        elif self.skip or self.in_fonts:
            pass
        elif self.to_drop:
            self.to_drop -= 1
        elif symbol in _SYMBOL_TEXT:
            # \- (optional hyphen), \_ and the rest are dropped
            self.out.append(_SYMBOL_TEXT[symbol])


def _tidy(text: str) -> str:
    """RichTextBox ends every save with `\\par`; trailing spaces on lines go too."""
    lines = [line.rstrip() for line in text.split("\n")]
    return "\n".join(lines).strip("\n")
