"""One sheet of an uploaded .xlsx as ``{"C16": "ヒューマン"}``.

Not a spreadsheet library: this reads the *values* a sheet holds and nothing
else — no styles, no merges, no recalculation. That is all the template import
needs, and it keeps the dependency list where it is (the backend has five).

Two things about the files this reads are worth knowing at the call site:

* **The formulas are dead.** The template is a Google Sheets document, and
  downloading it as .xlsx turns every Sheets-only function into
  ``__xludf.DUMMYFUNCTION("…")`` with the last computed value cached beside it.
  So the cached value is the only thing worth reading, and re-deriving anything
  from the formulas is not an option.
* **A cell's kind matters.** The template's dropdowns land in ``t="s"``
  (shared string) while the cells a formula fills — the metatype and the kind
  of magic user among them — land in ``t="str"``. Reading only the first kind
  loses half the character.
"""

from __future__ import annotations

import io
import xml.etree.ElementTree as ET  # the Element type only — parsing goes through parse_untrusted
import zipfile

from ..data_loader._xml import parse_untrusted

_MAIN = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_PKG_REL = "{http://schemas.openxmlformats.org/package/2006/relationships}"
_DOC_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"

#: The largest a single part may be once unzipped. The template's own biggest
#: sheet is ~1 MB; this leaves room for a bigger one without letting a
#: zip bomb decompress into the process.
MAX_PART_BYTES = 32 * 1024 * 1024

#: How many entries the archive may hold at all. The template has fourteen;
#: a few hundred leaves room for one written by another tool. Without this the
#: per-part ceiling says nothing about an archive of a hundred thousand names,
#: which costs memory in the central directory alone.
MAX_ENTRIES = 512

#: How much this reader will unzip over the whole workbook. The per-part
#: ceiling is per part, so a file holding a hundred 32 MB parts walks the
#: process through 3.2 GB one allowed part at a time. Twelve template sheets
#: at their real size come to ~12 MB, so this is the same kind of headroom
#: MAX_PART_BYTES leaves.
MAX_TOTAL_BYTES = 64 * 1024 * 1024


class NotAWorkbook(Exception):
    """The upload is not a readable .xlsx. Every malformed shape ends here."""


class Workbook:
    """An uploaded .xlsx, read one sheet at a time.

    Held open rather than read whole: the template has twelve sheets and the
    biggest of them is data the import never looks at.
    """

    def __init__(self, body: bytes) -> None:
        try:
            self._zip = zipfile.ZipFile(io.BytesIO(body))
        except (zipfile.BadZipFile, OSError) as exc:
            raise NotAWorkbook("not a zip archive") from exc
        if len(self._zip.infolist()) > MAX_ENTRIES:
            raise NotAWorkbook("too many entries")
        #: What is left of MAX_TOTAL_BYTES. Every part this reader unzips spends
        #: from it, so the sheets are read within one ceiling rather than each
        #: within its own.
        self._budget = MAX_TOTAL_BYTES
        book = self._part("xl/workbook.xml")
        rels = {
            rel.get("Id"): rel.get("Target") or ""
            for rel in self._part("xl/_rels/workbook.xml.rels").iter(_PKG_REL + "Relationship")
        }
        self._sheets: dict[str, str] = {}
        for sheet in book.iter(_MAIN + "sheet"):
            name, rid = sheet.get("name"), sheet.get(_DOC_REL + "id")
            target = rels.get(rid or "")
            if name and target:
                # The relationship target is relative to xl/, but a file written
                # elsewhere may spell it absolutely.
                self._sheets[name] = "xl/" + target.lstrip("/").removeprefix("xl/")
        if not self._sheets:
            raise NotAWorkbook("no sheets")
        self._strings: list[str] | None = None

    def _part(self, name: str) -> ET.Element:
        """One XML part, refused if it unzips too large or spends the budget."""
        try:
            info = self._zip.getinfo(name)
        except KeyError as exc:
            raise NotAWorkbook(f"missing part: {name}") from exc
        allowed = min(MAX_PART_BYTES, self._budget)
        if info.file_size > allowed:
            raise NotAWorkbook(f"part too large: {name}")
        with self._zip.open(info) as stream:
            raw = stream.read(allowed + 1)
        if len(raw) > allowed:
            raise NotAWorkbook(f"part too large: {name}")
        self._budget -= len(raw)
        try:
            return parse_untrusted(raw)
        except ET.ParseError as exc:
            raise NotAWorkbook(f"unreadable part: {name}") from exc

    @property
    def sheet_names(self) -> list[str]:
        return list(self._sheets)

    def _shared_strings(self) -> list[str]:
        if self._strings is None:
            if "xl/sharedStrings.xml" in self._zip.namelist():
                root = self._part("xl/sharedStrings.xml")
                # A cell's string may be split across runs (<si><r><t>…): join them.
                self._strings = [
                    "".join(t.text or "" for t in si.iter(_MAIN + "t")) for si in root.findall(_MAIN + "si")
                ]
            else:
                self._strings = []
        return self._strings

    def cells(self, sheet_name: str) -> dict[str, str]:
        """``{"C16": "ヒューマン"}`` for the non-empty cells of one sheet."""
        try:
            part = self._sheets[sheet_name]
        except KeyError as exc:
            raise NotAWorkbook(f"no sheet named {sheet_name}") from exc
        strings = self._shared_strings()
        out: dict[str, str] = {}
        for cell in self._part(part).iter(_MAIN + "c"):
            ref = cell.get("r")
            if not ref:
                continue
            kind = cell.get("t") or "n"
            if kind == "inlineStr":
                value = "".join(t.text or "" for t in cell.iter(_MAIN + "t"))
            else:
                node = cell.find(_MAIN + "v")
                value = (node.text or "") if node is not None else ""
                if kind == "s" and value.isdigit() and int(value) < len(strings):
                    value = strings[int(value)]
            value = value.strip()
            if value:
                out[ref] = value
        return out
