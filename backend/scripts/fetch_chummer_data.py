#!/usr/bin/env python3
"""Download the Chummer data/lang files the engine parses into backend/vendor/.

The chummer5a ref is pinned to a specific commit for reproducibility — the
engine parses upstream's ``<bonus>`` schema, which changes on ``master`` without
notice and silently breaks tests / derived output. To move the pin: bump
``CHUMMER_REF`` below (or pass ``--ref``), re-run, run ``python -m pytest`` +
``mypy``, and commit the new SHA with any parser changes it needs.

Re-running is cheap: it skips the download when ``vendor/`` already holds every
file for the requested ref. ``--force`` re-fetches anyway.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "chummer"
REF_FILE = VENDOR / ".chummer-ref"
# chummer5a/chummer5a @ 2026-09-02 "Fixed incorrect format for improvement on Master Archer"
DEFAULT_REF = "ed77aa3dcbe760064109d9af01ea9b5e4498294c"

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


def _dest(rel: str) -> Path:
    return VENDOR / Path(rel).relative_to("Chummer")


def _already_have(ref: str) -> bool:
    if not REF_FILE.exists() or REF_FILE.read_text(encoding="utf-8").strip() != ref:
        return False
    return all(_dest(rel).exists() and _dest(rel).stat().st_size > 0 for rel in FILES)


def _download(url: str, dest: Path, *, retries: int = 4) -> int:
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                data = resp.read()
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(data)
            return len(data)
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            last = exc
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"{url}: {last}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ref", default=os.environ.get("CHUMMER_REF") or DEFAULT_REF, help="chummer5a git ref")
    ap.add_argument("--force", action="store_true", help="re-download even if vendor/ is already complete")
    ap.add_argument("--jobs", type=int, default=8, help="parallel downloads")
    args = ap.parse_args()

    if not args.force and _already_have(args.ref):
        print(f"vendor/chummer already at {args.ref} — nothing to do (use --force to re-fetch)")
        return 0

    base = f"https://raw.githubusercontent.com/chummer5a/chummer5a/{args.ref}"
    print(f"fetching {len(FILES)} files from chummer5a@{args.ref[:12]} …")
    failures: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        futures = {pool.submit(_download, f"{base}/{rel}", _dest(rel)): rel for rel in FILES}
        for fut in concurrent.futures.as_completed(futures):
            rel = futures[fut]
            try:
                size = fut.result()
                print(f"  ok  {rel}  ({size:,} bytes)")
            except Exception as exc:
                print(f"  FAIL {rel}: {exc}", file=sys.stderr)
                failures.append(rel)

    if failures:
        print(
            f"\n{len(failures)} file(s) failed to download. Check your network / proxy, "
            "then re-run `make data` (or this script). You can also target a different "
            "ref with `--ref master` if the pinned commit is unavailable.",
            file=sys.stderr,
        )
        return 1

    (VENDOR / "NOTICE.txt").write_text(
        "Game data and translations are copied from chummer5a/chummer5a (GPL-3.0).\n"
        f"https://github.com/chummer5a/chummer5a/tree/{args.ref}\n",
        encoding="utf-8",
    )
    REF_FILE.write_text(args.ref + "\n", encoding="utf-8")
    print(f"done — vendor/chummer is at {args.ref}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
