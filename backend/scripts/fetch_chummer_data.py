#!/usr/bin/env python3
"""Download only the Chummer data/lang files needed for phase 1.

The chummer5a ref is pinned to a specific commit for reproducibility — the
engine parses upstream's `<bonus>` schema, which changes on `master` without
notice and silently breaks tests / derived output. To move the pin: bump
``CHUMMER_REF`` below, re-run this script, run ``python -m pytest`` + ``mypy``,
and commit the new SHA together with any parser changes it needs. Set the
``CHUMMER_REF`` env var to fetch a different ref ad hoc (e.g. ``master``).
"""

from __future__ import annotations

import os
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "chummer"
# chummer5a/chummer5a @ 2026-09-02 "Fixed incorrect format for improvement on Master Archer"
CHUMMER_REF = os.environ.get("CHUMMER_REF") or "ed77aa3dcbe760064109d9af01ea9b5e4498294c"
BASE = f"https://raw.githubusercontent.com/chummer5a/chummer5a/{CHUMMER_REF}"

FILES = [
    "Chummer/data/books.xml",
    "Chummer/data/priorities.xml",
    "Chummer/data/metatypes.xml",
    "Chummer/data/skills.xml",
    "Chummer/data/qualities.xml",
    "Chummer/data/cyberware.xml",
    "Chummer/data/bioware.xml",
    "Chummer/data/powers.xml",
    "Chummer/data/gear.xml",
    "Chummer/data/drugcomponents.xml",
    "Chummer/data/armor.xml",
    "Chummer/data/weapons.xml",
    "Chummer/data/ranges.xml",
    "Chummer/data/vehicles.xml",
    "Chummer/data/lifestyles.xml",
    "Chummer/data/mentors.xml",
    "Chummer/data/spells.xml",
    "Chummer/data/traditions.xml",
    "Chummer/data/complexforms.xml",
    "Chummer/data/streams.xml",
    "Chummer/data/martialarts.xml",
    "Chummer/data/metamagic.xml",
    "Chummer/data/echoes.xml",
    "Chummer/lang/en-us.xml",
    "Chummer/lang/ja-jp.xml",
    "Chummer/lang/ja-jp_data.xml",
]


def main() -> int:
    for rel in FILES:
        dest = VENDOR / Path(rel).relative_to("Chummer")
        dest.parent.mkdir(parents=True, exist_ok=True)
        url = f"{BASE}/{rel}"
        print(f"GET {url}")
        with urllib.request.urlopen(url, timeout=120) as resp:
            dest.write_bytes(resp.read())
        print(f"  -> {dest} ({dest.stat().st_size} bytes)")
    notice = VENDOR / "NOTICE.txt"
    notice.write_text(
        "Game data and translations are copied from chummer5a/chummer5a (GPL-3.0).\n"
        f"https://github.com/chummer5a/chummer5a/tree/{CHUMMER_REF}\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
