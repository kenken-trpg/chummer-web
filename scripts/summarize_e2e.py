#!/usr/bin/env python3
"""Summarize Playwright's JSON report, including retries on a green run.

The full report is an artifact; this small view goes in the Actions summary.
Durations include every attempt, so a retry cannot make a slow test look fast.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


def _cell(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace("|", "&#124;")
        .replace("\n", " ")
        .replace("\r", " ")
    )


def _tests(suites: list[dict[str, Any]], parents: tuple[str, ...] = ()) -> list[dict[str, Any]]:
    rows = []
    for suite in suites:
        titles = (*parents, suite["title"])
        for spec in suite.get("specs", []):
            for test in spec["tests"]:
                rows.append(
                    {
                        **test,
                        "title": " › ".join((*titles, spec["title"])),
                        "location": f"{spec['file']}:{spec['line']}",
                    }
                )
        rows.extend(_tests(suite.get("suites", []), titles))
    return rows


def summarize(report: dict[str, Any]) -> str:
    rows = _tests(report["suites"])
    counts = {
        status: sum(row["status"] == status for row in rows)
        for status in ("expected", "flaky", "unexpected", "skipped")
    }
    retries = sum(result["retry"] > 0 for row in rows for result in row["results"])
    lines = [
        "## E2E results",
        "",
        "| Expected | Flaky | Unexpected | Skipped | Retry attempts | Duration |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
        f"| {counts['expected']} | {counts['flaky']} | {counts['unexpected']} | {counts['skipped']} | {retries} | {report['stats']['duration'] / 1000:.1f}s |",
        "",
    ]
    if report.get("errors"):
        lines.extend([f"**Run-level errors: {len(report['errors'])}.** See the JSON report and job log.", ""])
    affected = [row for row in rows if row["status"] in {"flaky", "unexpected"} or len(row["results"]) > 1]
    if affected:
        lines.extend(
            [
                "### Failed or retried tests",
                "",
                "| Test | Location | Outcome | Attempts (retry: status, duration) |",
                "| --- | --- | --- | --- |",
            ]
        )
        for row in affected:
            attempts = "; ".join(f"{r['retry']}: {r['status']}, {r['duration'] / 1000:.1f}s" for r in row["results"])
            lines.append(
                f"| {_cell(row['title'])} [{_cell(row['projectName'])}] | {_cell(row['location'])} | {row['status']} | {_cell(attempts)} |"
            )
        lines.append("")
    lines.extend(["### Slowest tests (all attempts)", "", "| Test | Location | Duration |", "| --- | --- | ---: |"])
    for row in sorted(rows, key=lambda row: sum(r["duration"] for r in row["results"]), reverse=True)[:10]:
        seconds = sum(r["duration"] for r in row["results"]) / 1000
        lines.append(
            f"| {_cell(row['title'])} [{_cell(row['projectName'])}] | {_cell(row['location'])} | {seconds:.1f}s |"
        )
    lines.extend(["", "Full attempts, errors and timings: `playwright-results` artifact.", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args()
    try:
        summary = summarize(json.loads(args.report.read_text(encoding="utf-8")))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        summary = f"## E2E results\n\nReport unavailable or invalid: {_cell(exc)}. Inspect the setup and test logs.\n"
        result = 1
    else:
        result = 0
    print(summary)
    if target := os.environ.get("GITHUB_STEP_SUMMARY"):
        with Path(target).open("a", encoding="utf-8") as output:
            output.write(summary)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
