"""CHANGELOG fragments: one file per PR, folded into CHANGELOG.md at release.

Every PR used to add its entry right under `## [Unreleased]`, so any two open
PRs edited the same lines and the second one always conflicted. Now a PR adds
`changelog.d/<name>.<type>.md` instead — a file nobody else touches — and
`make changelog` moves them all into `[Unreleased]` when it is time to cut a
release.

    python scripts/changelog.py collect         # fold fragments in, delete them
    python scripts/changelog.py check-empty     # fail if any fragment is left
    python scripts/changelog.py check-pr BASE   # CI: a code PR adds a fragment
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FRAGMENTS = ROOT / "changelog.d"
CHANGELOG = ROOT / "CHANGELOG.md"
# Keep a Changelog order; the file suffix is the lower-case heading.
TYPES = ["Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"]
# A PR touching only these needs no entry (docs, CI, the changelog itself).
CODE = ("backend/", "frontend/", "Dockerfile", "compose.yaml", "deploy/")
SKIP_MARK = "[skip changelog]"


def fragments() -> dict[str, list[Path]]:
    found: dict[str, list[Path]] = {t: [] for t in TYPES}
    bad = []
    for path in sorted(FRAGMENTS.glob("*.md")):
        if path.name == "README.md":
            continue
        kind = path.name.removesuffix(".md").rsplit(".", 1)[-1].capitalize()
        if kind not in found:
            bad.append(path.name)
            continue
        found[kind].append(path)
    if bad:
        sys.exit(f"unknown type in {', '.join(bad)} — use one of: {', '.join(t.lower() for t in TYPES)}")
    return found


def collect() -> int:
    found = fragments()
    if not any(found.values()):
        print("no fragments")
        return 0
    text = CHANGELOG.read_text(encoding="utf-8")
    start = text.index("## [Unreleased]\n") + len("## [Unreleased]\n")
    nxt = re.search(r"^## \[", text[start:], re.M)
    end = start + nxt.start() if nxt else len(text)
    body = text[start:end]
    for kind in TYPES:
        if not found[kind]:
            continue
        entries = "\n".join(p.read_text(encoding="utf-8").strip() + "\n" for p in found[kind])
        heading = re.search(rf"^### {kind}\n\n", body, re.M)
        if heading:
            # Newest first, as the section has always been written.
            body = body[: heading.end()] + entries + "\n" + body[heading.end() :]
        else:
            # Before the first later heading, so the Keep a Changelog order holds.
            later = [f"### {t}\n" for t in TYPES[TYPES.index(kind) + 1 :]]
            at = min((body.find(h) for h in later if h in body), default=-1)
            block = f"### {kind}\n\n{entries}\n"
            if at == -1:
                body = body.rstrip("\n") + "\n\n" + block
            else:
                body = body[:at] + block + body[at:]
    body = "\n" + body.strip("\n") + "\n\n"
    CHANGELOG.write_text(text[:start] + body + text[end:], encoding="utf-8")
    done = [p for ps in found.values() for p in ps]
    for path in done:
        path.unlink()
    print(f"folded {len(done)} fragment(s) into [Unreleased]")
    return 0


def check_empty() -> int:
    left = [p.name for ps in fragments().values() for p in ps]
    if left:
        print(f"changelog.d/ still has {len(left)} fragment(s) — run `make changelog` first")
        return 1
    return 0


def check_pr(base: str, title: str = "") -> int:
    fragments()  # a misnamed fragment fails here, not at release time
    changed = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...HEAD"],
        capture_output=True,
        text=True,
        check=True,
        cwd=ROOT,
    ).stdout.split()
    if SKIP_MARK in title:
        print(f"{SKIP_MARK} in the title — not checking")
        return 0
    if not any(f.startswith(CODE) for f in changed):
        print("no code changes — no entry needed")
        return 0
    if any(f.startswith("changelog.d/") and f != "changelog.d/README.md" for f in changed):
        print("ok — the PR adds a changelog fragment")
        return 0
    print(
        "This PR changes code but adds no changelog.d/<name>.<type>.md.\n"
        "See changelog.d/README.md, or put " + SKIP_MARK + " in the PR title if nobody would notice."
    )
    return 1


def main(argv: list[str]) -> int:
    if argv[:1] == ["collect"]:
        return collect()
    if argv[:1] == ["check-empty"]:
        return check_empty()
    if argv[:1] == ["check-pr"] and len(argv) in (2, 3):
        return check_pr(*argv[1:])
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
