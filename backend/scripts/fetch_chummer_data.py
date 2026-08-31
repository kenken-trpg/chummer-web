#!/usr/bin/env python3
"""Download only the Chummer data/lang files needed for phase 1."""

from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "chummer"
BASE = "https://raw.githubusercontent.com/chummer5a/chummer5a/master"

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
        "https://github.com/chummer5a/chummer5a\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
