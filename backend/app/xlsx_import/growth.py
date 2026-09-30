"""The 成長ログ sheet: what the character has earned since it was made.

The sheet keeps one row per session — 報酬 in 新円 (A), カルマ (B), the date (C)
and what it was for (D) — and adds them up at the top. A character with rows
here is one that has been played, so it comes over as a career character rather
than as a build still in creation: that is the mode in which this app shows a
reward ledger at all, and it is what the rows mean.

Nothing is double-billed by that. The career baseline is the ratings the sheet
arrived with (`_econ_karma` snapshots it when the state carries none), so every
point on the sheet is still paid for as character creation and the log is what
was earned on top of it.

Two columns are read past and not stored:

* **経過日数 (E)** is the sheet's own arithmetic for lifestyle rent, which this
  app works out from the lifestyle itself.
* The **row 4 preset** 「ライフタイムによる収入」 carries no amounts until a
  player fills it in, and a row with neither karma nor nuyen is not a row.
"""

from __future__ import annotations

import datetime
import math
import re
import uuid
from typing import Any

from ..notices import Notice, notice

#: The log runs from row 4 to row 1000 — the range the sheet's own
#: ``SUM(A4:A1000)`` totals, which is the whole of the grid under the heading.
LOG_FIRST_ROW = 4
LOG_LAST_ROW = 1000
REWARD_NUYEN = "A"
REWARD_KARMA = "B"
REWARD_DATE = "C"
REWARD_NOTE = "D"

#: A spreadsheet writes a date as a day count from 1899-12-30. Only a number in
#: a range that reads as a date is turned back into one: a player may well have
#: typed 「第3話」 into the column instead, and that is worth keeping as written.
_EPOCH = datetime.date(1899, 12, 30)
_EARLIEST = 20000  # 1954
_LATEST = 100000  # 2173


def _amount(text: str | None) -> int:
    """A signed number from a cell, or 0. `cell_int` is for ratings and this is
    for money, so a minus sign matters and is kept."""
    if not text:
        return 0
    try:
        value = float(text)
    except ValueError:
        return 0
    if not math.isfinite(value):
        return 0
    return int(round(value))


def _date(text: str | None) -> str:
    """The date column as written, with a serial day count spelled out."""
    written = (text or "").strip()
    if not re.fullmatch(r"\d+(\.0+)?", written):
        return written
    serial = int(float(written))
    if not _EARLIEST <= serial <= _LATEST:
        return written
    return (_EPOCH + datetime.timedelta(days=serial)).isoformat()


def _label(cells: dict[str, str], row: int) -> str:
    """What the row was for, as the ledger shows it. The date is kept in front
    of the note because the log is read in order and this app has nowhere else
    to put a date — a row with neither is left empty on purpose, so the front
    end can word it in the reader's language."""
    date = _date(cells.get(f"{REWARD_DATE}{row}"))
    note = (cells.get(f"{REWARD_NOTE}{row}") or "").strip()
    return " ".join(part for part in (date, note) if part)


def import_growth(cells: dict[str, str], st: dict[str, Any], warn: list[Notice]) -> None:
    """Fill the reward ledger from the 成長ログ sheet."""
    rewards: list[dict[str, Any]] = []
    spent: list[dict[str, Any]] = []
    for row in range(LOG_FIRST_ROW, LOG_LAST_ROW + 1):
        karma = _amount(cells.get(f"{REWARD_KARMA}{row}"))
        nuyen = _amount(cells.get(f"{REWARD_NUYEN}{row}"))
        if not karma and not nuyen:
            continue
        entry = {"id": str(uuid.uuid4()), "label": _label(cells, row), "karma": karma, "nuyen": nuyen}
        # A negative row is the sheet being used to write something off rather
        # than to earn it. Kept as history: the ledger clamps a reward at zero,
        # so putting it there would turn a loss into nothing at all.
        (spent if karma < 0 or nuyen < 0 else rewards).append(entry)
    if not rewards and not spent:
        return
    if rewards:
        st["reward_log"] = rewards
    if spent:
        st["expense_log"] = spent
    st["career"] = True
    warn.append(notice("engine.import.xlsxGrowthLog", count=len(rewards) + len(spent)))


__all__ = ["LOG_FIRST_ROW", "LOG_LAST_ROW", "import_growth"]
