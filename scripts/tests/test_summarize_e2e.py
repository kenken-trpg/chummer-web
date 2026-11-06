"""A retry, a deliberate failure and a setup failure must not look alike."""

import unittest

from scripts.summarize_e2e import summarize


def _test(status: str, attempts: list[tuple[str, int]], expected: str = "passed") -> dict:
    return {
        "projectName": "chromium",
        "status": status,
        "expectedStatus": expected,
        "results": [{"retry": n, "status": state, "duration": ms} for n, (state, ms) in enumerate(attempts)],
    }


def _report(*tests: dict, errors: list | None = None) -> dict:
    return {
        "suites": [
            {
                "title": "persistence.spec.ts",
                "suites": [
                    {
                        "title": "reload",
                        "specs": [
                            {"title": "saved | <value>", "file": "persistence.spec.ts", "line": 7, "tests": list(tests)}
                        ],
                    }
                ],
            }
        ],
        "stats": {"duration": 12000},
        "errors": errors or [],
    }


class SummaryTest(unittest.TestCase):
    def test_flaky_attempts_and_their_combined_time_remain_visible(self) -> None:
        text = summarize(_report(_test("flaky", [("timedOut", 6000), ("passed", 2000)])))
        self.assertIn("| 0 | 1 | 0 | 0 | 1 | 12.0s |", text)
        self.assertIn("0: timedOut, 6.0s; 1: passed, 2.0s", text)
        self.assertIn("| 8.0s |", text)
        self.assertIn("persistence.spec.ts › reload › saved &#124; &lt;value>", text)
        self.assertIn("persistence.spec.ts:7", text)

    def test_expected_failures_are_not_counted_as_unexpected(self) -> None:
        text = summarize(_report(_test("expected", [("failed", 100)], expected="failed")))
        self.assertIn("| 1 | 0 | 0 | 0 | 0 |", text)
        self.assertNotIn("### Failed or retried tests", text)

    def test_final_failure_skips_and_global_errors_are_distinct(self) -> None:
        text = summarize(
            _report(
                _test("unexpected", [("failed", 100)]), _test("skipped", []), errors=[{"message": "server stopped"}]
            )
        )
        self.assertIn("| 0 | 0 | 1 | 1 | 0 |", text)
        self.assertIn("Run-level errors: 1", text)
        self.assertIn("| unexpected | 0: failed, 0.1s |", text)

    def test_a_setup_failure_can_have_no_tests(self) -> None:
        text = summarize({"suites": [], "stats": {"duration": 500}, "errors": [{"message": "setup failed"}]})
        self.assertIn("| 0 | 0 | 0 | 0 | 0 | 0.5s |", text)
        self.assertIn("Run-level errors: 1", text)


if __name__ == "__main__":
    unittest.main()
