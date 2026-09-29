"""Chummer's own test saves, fetched once into ``vendor/chummer-tests/``.

They come from ``Chummer.Tests/TestFiles`` at the same chummer5a ref as the
game data, so what the comparison is checked against and what it computes
from come from the same release.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

# backend/  (this file is scripts/reconcile/_saves.py)
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from scripts.fetch_chummer_data import DEFAULT_REF, REF_FILE, _download  # noqa: E402

CACHE = ROOT / "vendor" / "chummer-tests"
TESTFILES = "Chummer.Tests/TestFiles"


def _ref() -> str:
    return REF_FILE.read_text(encoding="utf-8").strip() if REF_FILE.exists() else DEFAULT_REF


def _listing(api: str) -> Any:
    """`api`, as JSON, signed in if this environment has a token.

    The saves themselves come off raw.githubusercontent, which is not rate
    limited, but naming them is one call to the API — and unauthenticated that
    is 60 an hour *per IP*, which on a shared CI runner is spent before the job
    starts (`HTTP Error 403: rate limit exceeded`). A token raises it to 5,000
    an hour for the account; GitHub Actions has one in `GITHUB_TOKEN`.
    """
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "chummer-web-reconcile"}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urllib.request.urlopen(urllib.request.Request(api, headers=headers), timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 429) and not token:
            raise SystemExit(
                f"{api}: {exc}. The GitHub API allows 60 unauthenticated calls an hour per address; "
                "set GITHUB_TOKEN (or GH_TOKEN) to a token with no scopes and try again."
            ) from exc
        raise


def fetch(ref: str) -> Path:
    """The test saves at `ref`, downloaded on first use."""
    target = CACHE / ref
    if target.is_dir() and any(target.glob("*.chum5")):
        return target
    api = f"https://api.github.com/repos/chummer5a/chummer5a/contents/{TESTFILES}?ref={ref}"
    listing = _listing(api)
    names = [row["name"] for row in listing if str(row.get("name", "")).endswith(".chum5")]
    print(f"fetching {len(names)} saves from chummer5a@{ref[:12]} …", file=sys.stderr)
    base = f"https://raw.githubusercontent.com/chummer5a/chummer5a/{ref}/{TESTFILES}"
    for name in names:
        _download(f"{base}/{urllib.parse.quote(name)}", target / name)
    return target
