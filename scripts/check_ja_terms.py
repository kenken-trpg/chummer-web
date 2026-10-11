"""Fail the Japanese UI strings that use a term the glossary rejects.

`docs/translation-glossary.md` is this project's canon, but checking against it
cannot be made automatic: a Japanese sentence does not say which English term it
translates, so there is no way to ask "is this the adopted word for Quality?"
from the string alone. What can be checked is the other direction — a word we
have already established is the wrong one.

So `docs/translation-banned-terms.md` records the mistakes that actually reached
the UI, and this walks `frontend/lib/i18n/locales/ja/` for them. Each entry is
written once, when the drift is fixed, and from then on that word cannot come
back. It catches recurrence, not a brand new mistranslation.

    python scripts/check_ja_terms.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BANNED = ROOT / "docs/translation-banned-terms.md"
LOCALE = ROOT / "frontend/lib/i18n/locales/ja"


class Rule:
    def __init__(self, wrong: str, right: str, source: str, allowed: list[str]) -> None:
        self.wrong = wrong
        self.right = right
        self.source = source
        # Longest first, so `アップグレード` is tried before any shorter word
        # that also contains the banned term.
        self.allowed = sorted(allowed, key=len, reverse=True)

    def hits(self, line: str) -> int:
        """Occurrences of the banned term that no allowed word accounts for."""
        for word in self.allowed:
            line = line.replace(word, "")
        return line.count(self.wrong)


def rules(text: str) -> list[Rule]:
    found = []
    for row in re.findall(r"^\|(.+)\|$", text, re.M):
        cells = [c.strip() for c in row.split("|")]
        if len(cells) != 5 or cells[0] in {"誤", "---"} or set(cells[0]) == {"-"}:
            continue
        wrong, right, source, allowed = cells[0], cells[1], cells[2], cells[3]
        found.append(Rule(wrong, right, source, [w.strip() for w in allowed.split(",") if w.strip()]))
    if not found:
        sys.exit(f"{BANNED.name} has no rules — did its table change shape?")
    return found


def check(locale: Path, banned: Path) -> list[str]:
    found = rules(banned.read_text(encoding="utf-8"))
    problems = []
    for path in sorted(locale.rglob("*.ts")):
        for number, line in enumerate(path.read_text(encoding="utf-8").split("\n"), start=1):
            for rule in found:
                if rule.hits(line):
                    where = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path
                    problems.append(f"{where}:{number}: 「{rule.wrong}」は「{rule.right}」（{rule.source}）")
    return problems


def main() -> int:
    if not LOCALE.is_dir():
        print("frontend/ not checked out — nothing to check")
        return 0
    problems = check(LOCALE, BANNED)
    if problems:
        print("\n".join(["", *problems, "", f"See docs/{BANNED.name} and docs/translation-glossary.md."]))
        return 1
    print(f"ok — no banned term in {LOCALE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
