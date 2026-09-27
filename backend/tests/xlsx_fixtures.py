"""A minimal stand-in for シャドウラン_キャラシテンプレート.

The real template is a 270 KB workbook of twelve sheets, most of it reference
data the import never reads, and a filled-in one is somebody's character. So the
tests build the smallest workbook the reader accepts and put the cells under
test in it by address, the same addresses the template uses.

Cells are written as inline strings, which the reader handles alongside the
shared strings and formula results a real download holds — those two shapes are
covered by `test_reads_both_string_kinds`.
"""

from __future__ import annotations

import io
import re
import zipfile

from app.xlsx_import._common import SHEET_BASICS

#: The sheets `is_template_workbook` insists on, in the order the template has
#: them. Only the first is ever read.
SHEETS = (SHEET_BASICS, "能動技能／技能グループ", "編集不可")

_CONTENT_TYPES = """<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
</Types>"""

_ROOT_RELS = """<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>"""


def _row_of(ref: str) -> int:
    return int(re.sub(r"[^0-9]", "", ref))


def _sheet_xml(cells: dict[str, str], *, shared: dict[str, int] | None = None) -> str:
    """One worksheet part. `shared` names the cells to write as shared-string
    references instead of inline strings."""
    shared = shared or {}
    by_row: dict[int, list[str]] = {}
    for ref, value in cells.items():
        if ref in shared:
            cell = f'<c r="{ref}" t="s"><v>{shared[ref]}</v></c>'
        elif re.fullmatch(r"-?\d+(\.\d+)?", value):
            cell = f'<c r="{ref}"><v>{value}</v></c>'
        else:
            escaped = value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            cell = f'<c r="{ref}" t="inlineStr"><is><t>{escaped}</t></is></c>'
        by_row.setdefault(_row_of(ref), []).append(cell)
    rows = "".join(f'<row r="{r}">{"".join(by_row[r])}</row>' for r in sorted(by_row))
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        f"<sheetData>{rows}</sheetData></worksheet>"
    )


def workbook(
    cells: dict[str, str],
    *,
    sheets: tuple[str, ...] = SHEETS,
    shared_strings: list[str] | None = None,
    shared: dict[str, int] | None = None,
) -> bytes:
    """A .xlsx holding `cells` on the 優先度／能力値／資質 sheet."""
    sheet_tags = "".join(
        f'<sheet name="{name}" sheetId="{i}" r:id="rId{i}"/>' for i, name in enumerate(sheets, start=1)
    )
    rel_tags = "".join(
        f'<Relationship Id="rId{i}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        f'Target="worksheets/sheet{i}.xml"/>'
        for i in range(1, len(sheets) + 1)
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", _CONTENT_TYPES)
        archive.writestr("_rels/.rels", _ROOT_RELS)
        archive.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f"<sheets>{sheet_tags}</sheets></workbook>",
        )
        archive.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            f"{rel_tags}</Relationships>",
        )
        for index in range(1, len(sheets) + 1):
            body = _sheet_xml(cells, shared=shared) if index == 1 else _sheet_xml({})
            archive.writestr(f"xl/worksheets/sheet{index}.xml", body)
        if shared_strings is not None:
            items = "".join(f"<si><t>{text}</t></si>" for text in shared_strings)
            archive.writestr(
                "xl/sharedStrings.xml",
                '<?xml version="1.0" encoding="UTF-8"?>'
                '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                f'count="{len(shared_strings)}" uniqueCount="{len(shared_strings)}">{items}</sst>',
            )
    return buffer.getvalue()


#: The sheet as the template ships it, filled in for a plain priority build.
#: Every test starts from this and overrides the cells it is about.
BASELINE = {
    "W1": "通常のプレイレベル",
    "C3": "A",
    "C7": "B",
    "C8": "E",
    "C12": "C",
    "C13": "D",
    "C16": "ヒューマン",
    "C17": "－",
    **{f"H{row}": "1.0" for row in range(19, 27)},
    "H27": "2.0",
    "H28": "0",
    "H29": "0",
}


def filled(**overrides: str) -> bytes:
    """A workbook of `BASELINE` plus `overrides`; a cell set to "" is removed."""
    cells = {**BASELINE, **overrides}
    return workbook({ref: value for ref, value in cells.items() if value != ""})
