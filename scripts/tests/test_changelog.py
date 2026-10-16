"""`collect` folds fragments into CHANGELOG.md, against a scratch copy."""

import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("changelog", SCRIPTS / "changelog.py")
assert spec is not None and spec.loader is not None
changelog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(changelog)

HEAD = "# Changelog\n\nNotable changes.\n\n"
RELEASED = "## [0.5.3] — 2026-10-16\n\n### Fixed\n\n- old fix\n"


class CollectTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "changelog.d").mkdir()
        self.fragments = root / "changelog.d"
        self.changelog = root / "CHANGELOG.md"
        for name, value in (("FRAGMENTS", self.fragments), ("CHANGELOG", self.changelog)):
            old = getattr(changelog, name)
            setattr(changelog, name, value)
            self.addCleanup(setattr, changelog, name, old)

    def fold(self, text: str) -> str:
        self.changelog.write_text(text, encoding="utf-8")
        (self.fragments / "new.fixed.md").write_text("- new fix\n", encoding="utf-8")
        self.assertEqual(changelog.collect(), 0)
        self.assertFalse((self.fragments / "new.fixed.md").exists())
        return self.changelog.read_text(encoding="utf-8")

    def test_folds_into_existing_unreleased(self) -> None:
        out = self.fold(HEAD + "## [Unreleased]\n\n" + RELEASED)
        self.assertEqual(out, HEAD + "## [Unreleased]\n\n### Fixed\n\n- new fix\n\n" + RELEASED)

    def test_restores_unreleased_a_release_renamed_away(self) -> None:
        # The release step renames [Unreleased] to the version; the next
        # collect used to die on `substring not found`.
        out = self.fold(HEAD + RELEASED)
        self.assertEqual(out, HEAD + "## [Unreleased]\n\n### Fixed\n\n- new fix\n\n" + RELEASED)


if __name__ == "__main__":
    unittest.main()
