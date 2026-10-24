"""The compare links at the foot of CHANGELOG.md, rebuilt from its headings."""

import importlib.util
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("release_notes", SCRIPTS / "release_notes.py")
assert spec is not None and spec.loader is not None
release_notes = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release_notes)

BASE = "https://github.com/kenken-trpg/chummer-web"
BODY = (
    "# Changelog\n\n## [Unreleased]\n\n- next\n\n## [0.2.0] — 2026-09-10\n\n- two\n\n## [0.1.0] — 2026-09-02\n\n- one\n"
)
LINKS = (
    f"[Unreleased]: {BASE}/compare/v0.2.0...HEAD\n"
    f"[0.2.0]: {BASE}/compare/v0.1.0...v0.2.0\n"
    f"[0.1.0]: {BASE}/releases/tag/v0.1.0\n"
)


class LinkFooterTest(unittest.TestCase):
    def test_builds_the_links_newest_first(self) -> None:
        self.assertEqual(release_notes.link_footer(BODY), LINKS)

    def test_replaces_a_footer_that_stopped_at_an_old_release(self) -> None:
        # the real file's footer stopped at 0.5.4 while ten more were tagged
        stale = BODY + f"\n[Unreleased]: {BASE}/compare/v0.1.0...HEAD\n[0.1.0]: {BASE}/releases/tag/v0.1.0\n"
        self.assertEqual(release_notes.with_links(stale), BODY + "\n" + LINKS)

    def test_adds_a_footer_where_there_was_none(self) -> None:
        self.assertEqual(release_notes.with_links(BODY), BODY + "\n" + LINKS)

    def test_leaves_an_up_to_date_file_alone(self) -> None:
        current = BODY + "\n" + LINKS
        self.assertEqual(release_notes.with_links(current), current)

    def test_keeps_links_the_text_itself_uses(self) -> None:
        # only the trailing block is the footer; a link inside a section stays
        body = BODY.replace("- one\n", f"- one\n\n[the PR]: {BASE}/pull/1\n\nmore\n")
        self.assertIn(f"[the PR]: {BASE}/pull/1", release_notes.with_links(body))


if __name__ == "__main__":
    unittest.main()
