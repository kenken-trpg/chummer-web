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


class NotAWorkbook(Exception):
    """The upload is not a readable .xlsx. Every malformed shape ends here."""


def _part(archive: zipfile.ZipFile, name: str) -> ET.Element:
    """One XML part of the archive, refused if it unzips too large."""
    try:
        info = archive.getinfo(name)
    except KeyError as exc:
        raise NotAWorkbook(f"missing part: {name}") from exc
    if info.file_size > MAX_PART_BYTES:
        raise NotAWorkbook(f"part too large: {name}")
    with archive.open(info) as stream:
        raw = stream.read(MAX_PART_BYTES + 1)
    if len(raw) > MAX_PART_BYTES:
        raise NotAWorkbook(f"part too large: {name}")
    try:
        return parse_untrusted(raw)
    except ET.ParseError as exc:
        raise NotAWorkbook(f"unreadable part: {name}") from exc


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
        book = _part(self._zip, "xl/workbook.xml")
        rels = {
            rel.get("Id"): rel.get("Target") or ""
            for rel in _part(self._zip, "xl/_rels/workbook.xml.rels").iter(_PKG_REL + "Relationship")
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

    @property
    def sheet_names(self) -> list[str]:
        return list(self._sheets)

    def _shared_strings(self) -> list[str]:
        if self._strings is None:
            if "xl/sharedStrings.xml" in self._zip.namelist():
                root = _part(self._zip, "xl/sharedStrings.xml")
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
        for cell in _part(self._zip, part).iter(_MAIN + "c"):
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
