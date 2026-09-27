"""Write a .xlsx from ``{"C3": value}`` per sheet, and nothing more.

The counterpart of `xlsx_import._sheet`, and just as narrow: it writes the
*values* of a set of cells and no styling, no formulas, no merges, no column
widths. That is what this export needs, and it keeps the dependency list where
it is (the backend has five, and openpyxl would be a sixth for one file).

Why a workbook is built rather than the template filled in:

* **The template is not ours to ship.** It is 音の兔 様's work, so bundling it
  would need their permission.
* **Filling it in would not work anyway.** The template is a Google Sheets
  document, and the .xlsx it downloads as has every Sheets-only function
  replaced by ``__xludf.DUMMYFUNCTION("…")`` with the last cached value beside
  it. Writing new inputs into that file would leave every derived cell showing
  the *previous* character's numbers, which is worse than not writing them.

So what comes out is a workbook with the template's sheet names and the
template's input addresses, holding one character's inputs. The import reads it
back whole; a spreadsheet application opens it as a plain grid.
"""

from __future__ import annotations

import re
import zipfile
from io import BytesIO
from xml.sax.saxutils import escape, quoteattr

#: A cell reference, as the callers write it.
_REF = re.compile(r"^([A-Z]+)([1-9]\d*)$")

#: Characters XML 1.0 has no way to carry. A character name pasted out of a
#: chat log can hold one, and it would make the file unreadable rather than
#: merely odd, so it comes out.
_FORBIDDEN = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")

Value = str | int | float
Cells = dict[str, Value]


def column_index(letters: str) -> int:
    """``"A"`` -> 1, ``"AC"`` -> 29."""
    index = 0
    for char in letters:
        index = index * 26 + (ord(char) - 64)
    return index


def _sorted_cells(cells: Cells) -> list[tuple[int, list[tuple[int, str, Value]]]]:
    """`cells` grouped into rows, each row's cells left to right.

    A sheet's XML has to be written in order: a reader is entitled to stop at
    the first row whose number goes backwards.
    """
    rows: dict[int, list[tuple[int, str, Value]]] = {}
    for ref, value in cells.items():
        matched = _REF.match(ref)
        if not matched:
            raise ValueError(f"not a cell reference: {ref}")
        letters, number = matched.groups()
        rows.setdefault(int(number), []).append((column_index(letters), ref, value))
    return [(number, sorted(rows[number])) for number in sorted(rows)]


class _Strings:
    """The shared string table, built as the sheets are written."""

    def __init__(self) -> None:
        self._index: dict[str, int] = {}

    def of(self, text: str) -> int:
        if text not in self._index:
            self._index[text] = len(self._index)
        return self._index[text]

    def xml(self) -> str:
        items = "".join(f'<si><t xml:space="preserve">{escape(text)}</t></si>' for text in self._index)
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            f'count="{len(self._index)}" uniqueCount="{len(self._index)}">{items}</sst>'
        )


def _sheet_xml(cells: Cells, strings: _Strings) -> str:
    out = [
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        "<sheetData>"
    ]
    for number, row in _sorted_cells(cells):
        out.append(f'<row r="{number}">')
        for _column, ref, value in row:
            if isinstance(value, bool):  # bool is an int; nothing here means one
                raise TypeError(f"{ref}: a cell holds text or a number")
            if isinstance(value, int | float):
                out.append(f'<c r="{ref}"><v>{value}</v></c>')
                continue
            text = _FORBIDDEN.sub("", value)
            if not text:
                continue
            out.append(f'<c r="{ref}" t="s"><v>{strings.of(text)}</v></c>')
        out.append("</row>")
    out.append("</sheetData></worksheet>")
    return "".join(out)


#: The smallest styles part a spreadsheet application will accept. Excel treats
#: a workbook with no styles at all as damaged and offers to repair it.
_STYLES = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>'
    '<fills count="1"><fill><patternFill patternType="none"/></fill></fills>'
    '<borders count="1"><border/></borders>'
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
    "</styleSheet>"
)

_ROOT_RELS = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Id="rId1" '
    'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
    'Target="xl/workbook.xml"/>'
    "</Relationships>"
)


def write_workbook(sheets: list[tuple[str, Cells]]) -> bytes:
    """A .xlsx holding `sheets`, in the order given.

    Each sheet is ``(name, {"C3": value})``. A string cell goes through the
    shared string table, a number is written as it is, and an empty string is
    left out — an absent cell and a blank one read back the same, and leaving it
    out keeps the file to what the character actually has.
    """
    if not sheets:
        raise ValueError("a workbook needs a sheet")
    strings = _Strings()
    # The sheets are rendered first: the string table is only complete afterwards.
    rendered = [_sheet_xml(cells, strings) for _name, cells in sheets]

    entries = "".join(
        f'<sheet name={quoteattr(name)} sheetId="{number}" r:id="rId{number}"/>'
        for number, (name, _cells) in enumerate(sheets, 1)
    )
    workbook = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
        'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        f"<sheets>{entries}</sheets></workbook>"
    )
    rels = "".join(
        f'<Relationship Id="rId{number}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        f'Target="worksheets/sheet{number}.xml"/>'
        for number in range(1, len(sheets) + 1)
    )
    extra = len(sheets) + 1
    workbook_rels = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        f"{rels}"
        f'<Relationship Id="rId{extra}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/sharedStrings" '
        'Target="sharedStrings.xml"/>'
        f'<Relationship Id="rId{extra + 1}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
        'Target="styles.xml"/>'
        "</Relationships>"
    )
    overrides = "".join(
        f'<Override PartName="/xl/worksheets/sheet{number}.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        for number in range(1, len(sheets) + 1)
    )
    content_types = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        '<Default Extension="xml" ContentType="application/xml"/>'
        '<Override PartName="/xl/workbook.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
        f"{overrides}"
        '<Override PartName="/xl/sharedStrings.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sharedStrings+xml"/>'
        '<Override PartName="/xl/styles.xml" '
        'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
        "</Types>"
    )

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types)
        archive.writestr("_rels/.rels", _ROOT_RELS)
        archive.writestr("xl/workbook.xml", workbook)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels)
        archive.writestr("xl/styles.xml", _STYLES)
        archive.writestr("xl/sharedStrings.xml", strings.xml())
        for number, body in enumerate(rendered, 1):
            archive.writestr(f"xl/worksheets/sheet{number}.xml", body)
    return buffer.getvalue()


__all__ = ["Cells", "Value", "column_index", "write_workbook"]
