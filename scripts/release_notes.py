#!/usr/bin/env python3
"""Release notes for a tag, and the checks that make them trustworthy.

    python3 scripts/release_notes.py 0.1.0        # print the notes
    python3 scripts/release_notes.py 0.1.0 --check  # verify only, print nothing

CI runs this on a `v*` tag before publishing the GitHub Release, so a tag that
was pushed without a CHANGELOG entry, or without bumping the version the API
reports, fails loudly instead of shipping a release whose notes say nothing.

Three things have to agree, because nothing else makes them:

- ``CHANGELOG.md`` has a ``## [<version>]`` section with content under it
- ``backend/pyproject.toml``'s ``version``
- the ``version=`` FastAPI reports at ``/docs`` (``backend/app/main.py``)

`frontend/package.json` is deliberately not in the list: it is `"private": true`
and never published, so its version is noise.

The compare links at the foot of ``CHANGELOG.md`` follow from its version
headings, so ``--write-links`` rewrites them and ``--check`` fails when they lag
(they stopped at 0.5.4 for ten releases). The tag build leaves them alone: a
stale link is not a reason to hold back a release whose code is already out.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO = "kenken-trpg/chummer-web"


def changelog_section(version: str) -> str:
    """The body of ``## [<version>]``, up to the next ``## ``."""
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    # the heading is `## [0.1.0] — 2026-09-02`; the date is optional
    pattern = rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text, re.M | re.S)
    if not match:
        raise SystemExit(f"CHANGELOG.md has no `## [{version}]` section — add one before tagging.")
    body = match.group(1).strip()
    if not body:
        raise SystemExit(f"CHANGELOG.md's `## [{version}]` section is empty.")
    return body


LINK = re.compile(r"^\[(?:Unreleased|\d+\.\d+\.\d+)\]: https://\S+$", re.M)


def link_footer(text: str) -> str:
    """The compare links ``CHANGELOG.md`` should end with, newest first.

    Built from the ``## [x.y.z]`` headings in file order: ``[Unreleased]``
    compares the newest tag with ``HEAD``, each version the one below it, and
    the oldest links to its own release."""
    versions = re.findall(r"^## \[(\d+\.\d+\.\d+)\]", text, re.M)
    if not versions:
        raise SystemExit("CHANGELOG.md has no `## [x.y.z]` headings to link.")
    base = f"https://github.com/{REPO}"
    lines = [f"[Unreleased]: {base}/compare/v{versions[0]}...HEAD"]
    for newer, older in zip(versions, versions[1:], strict=False):
        lines.append(f"[{newer}]: {base}/compare/v{older}...v{newer}")
    lines.append(f"[{versions[-1]}]: {base}/releases/tag/v{versions[-1]}")
    return "\n".join(lines) + "\n"


def with_links(text: str) -> str:
    """``text`` with its trailing block of link definitions replaced."""
    body = text.rstrip("\n").split("\n")
    while body and LINK.match(body[-1]):
        body.pop()
    return "\n".join(body).rstrip("\n") + "\n\n" + link_footer(text)


def check_links() -> None:
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    if with_links(text) != text:
        raise SystemExit(
            "CHANGELOG.md's compare links do not match its version headings — "
            "run `python3 scripts/release_notes.py <version> --write-links`."
        )


def _declared(path: str, pattern: str) -> str:
    text = (ROOT / path).read_text(encoding="utf-8")
    match = re.search(pattern, text, re.M)
    if not match:
        raise SystemExit(f"no version found in {path} (pattern: {pattern})")
    return match.group(1)


def check_versions(version: str) -> None:
    declared = {
        "backend/pyproject.toml": _declared("backend/pyproject.toml", r'^version = "([^"]+)"'),
        "backend/app/main.py": _declared("backend/app/main.py", r'^\s*version="([^"]+)",'),
    }
    wrong = {path: found for path, found in declared.items() if found != version}
    if wrong:
        lines = "\n".join(f"  {path}: {found}" for path, found in wrong.items())
        raise SystemExit(f"tag says {version}, but:\n{lines}\nBump them, or tag the right commit.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="without the leading v, e.g. 0.2.0")
    parser.add_argument("--check", action="store_true", help="validate only; print nothing")
    parser.add_argument("--write-links", action="store_true", help="rewrite CHANGELOG.md's compare links and exit")
    args = parser.parse_args()

    version = args.version.removeprefix("v")
    if args.write_links:
        path = ROOT / "CHANGELOG.md"
        path.write_text(with_links(path.read_text(encoding="utf-8")), encoding="utf-8")
        return 0
    check_versions(version)
    notes = changelog_section(version)
    if args.check:
        check_links()
        return 0

    print(notes)
    print()
    print("---")
    print()
    print("```bash")
    print(f"docker pull ghcr.io/{REPO.split('/')[0]}/chummer-web:{version}")
    print("```")
    print()
    print(f"Full changelog: https://github.com/{REPO}/blob/v{version}/CHANGELOG.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
