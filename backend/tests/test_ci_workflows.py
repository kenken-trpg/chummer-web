"""Exercise deploy result classification and the bot changelog boundary."""

import importlib.util
import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.skipif(os.name == "nt", reason="The deployment shell runs on Linux")
@pytest.mark.parametrize(
    ("ready", "page", "expected", "incomplete"),
    [
        ("ok", "ok", 0, False),
        ("challenge", "challenge", 0, True),
        ("challenge", "ok", 0, True),
        ("challenge", "403", 1, False),
        ("500", "challenge", 1, False),
        ("wrong", "ok", 1, False),
        ("network", "ok", 1, False),
    ],
)
def test_public_smoke_results(tmp_path: Path, ready: str, page: str, expected: int, incomplete: bool) -> None:
    workflow = yaml.safe_load((ROOT / ".github/workflows/deploy-cloudrun.yml").read_text())
    script = next(
        s["run"] for s in workflow["jobs"]["deploy"]["steps"] if s.get("name") == "Smoke-test the public path"
    )
    # Isolate the workflow's fixed scratch paths so xdist workers cannot race.
    script = script.replace("/tmp/smoke-", str(tmp_path / "smoke-"))
    fake_curl = tmp_path / "curl"
    fake_curl.write_text(
        "#!/usr/bin/env python3\n"
        "import os, sys\n"
        "from pathlib import Path\n"
        "args = sys.argv[1:]\n"
        'ready = args[-1].endswith("/api/ready")\n'
        'mode = os.environ["READY_RESULT" if ready else "PAGE_RESULT"]\n'
        'headers = "cf-mitigated: challenge\\r\\n" if mode == "challenge" else ""\n'
        'body = (\'{"ready":true}\' if ready else "<html></html>") if mode == "ok" else "error"\n'
        'Path(args[args.index("-D") + 1]).write_text(headers)\n'
        'Path(args[args.index("-o") + 1]).write_text(body)\n'
        'print(mode if mode in ("403", "500") else "403" if mode == "challenge" else "200", end="")\n'
        'sys.exit(7 if mode == "network" else 0)\n'
    )
    fake_curl.chmod(0o755)
    sleep = tmp_path / "sleep"
    sleep.write_text("#!/bin/sh\nexit 0\n")
    sleep.chmod(0o755)
    summary = tmp_path / "summary"
    result = subprocess.run(
        ["bash", "-e", "-c", script],
        env={
            **os.environ,
            "PATH": f"{tmp_path}{os.pathsep}{os.environ['PATH']}",
            "PUBLIC_URL": "https://example.test",
            "SERVICE": "test",
            "REGION": "test",
            "GITHUB_STEP_SUMMARY": str(summary),
            "READY_RESULT": ready,
            "PAGE_RESULT": page,
        },
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == expected, result.stdout + result.stderr
    assert (summary.exists() and "verification incomplete" in summary.read_text()) == incomplete
    assert ("public path OK" in result.stdout) == (ready == page == "ok")


@pytest.mark.parametrize(
    ("author", "changed", "expected"),
    [
        ("dependabot[bot]", "frontend/package.json\nfrontend/package-lock.json", 0),
        ("dependabot[bot]", "backend/requirements.txt", 0),
        ("dependabot[bot]", "Dockerfile", 0),
        ("dependabot[bot]", "frontend/package.json\nfrontend/app/page.tsx", 1),
        ("human", "backend/requirements.txt", 1),
    ],
)
def test_changelog_bot_boundary(author: str, changed: str, expected: int) -> None:
    spec = importlib.util.spec_from_file_location("changelog", ROOT / "scripts/changelog.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with patch.object(module.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, changed)):
        assert module.check_pr("base", author=author) == expected
