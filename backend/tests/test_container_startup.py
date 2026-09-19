"""The container says where it is listening, and says it once, correctly.

Three servers announce themselves in the log and two of the addresses are
unreachable from outside — Next's `127.0.0.1:3000` is the one people try, and
it is not published. `deploy/announce-url` has the last word; these tests keep
its wiring and its port in step with the rest of the image, because the whole
failure mode is a number that disagrees with another number.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILE = (ROOT / "Dockerfile").read_text(encoding="utf-8")
SUPERVISORD = (ROOT / "deploy" / "supervisord.conf").read_text(encoding="utf-8")
CADDYFILE = (ROOT / "deploy" / "Caddyfile").read_text(encoding="utf-8")
ANNOUNCE = ROOT / "deploy" / "announce-url"

DEFAULT_PORT = "8080"


def test_the_announcer_is_copied_in_and_executable() -> None:
    """A supervisord program pointing at a file the image does not have is a
    FATAL line in the log where the address should have been."""
    command = re.search(r"^\[program:banner\]\ncommand=(\S+)", SUPERVISORD, re.M)
    assert command, "no [program:banner] in supervisord.conf"
    target = command.group(1)

    assert re.search(rf"^COPY deploy/announce-url\s+{re.escape(target)}$", DOCKERFILE, re.M), (
        f"{target} is never COPYed into the image"
    )
    assert ANNOUNCE.exists()
    # The mode recorded in git, not on disk: a Windows checkout has no POSIX
    # permission bits at all, and what ends up in the image is what `COPY`
    # reads out of the tree. A file committed 100644 gives supervisord an
    # EACCES where the address should have been.
    mode = subprocess.run(
        ["git", "ls-files", "-s", "--", "deploy/announce-url"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if mode.returncode != 0 or not mode.stdout.strip():
        pytest.skip("not a git checkout — cannot read the recorded file mode")
    assert mode.stdout.split()[0] == "100755", f"deploy/announce-url is committed as {mode.stdout.split()[0]}"


def test_the_announcer_runs_once_and_is_not_restarted() -> None:
    """It exits 0 on success; `autorestart=true` would print the banner forever."""
    block = SUPERVISORD.split("[program:banner]", 1)[1]
    assert "autorestart=false" in block
    assert "startsecs=0" in block  # or supervisord calls a 0.1s program a failure


def test_every_port_in_the_banner_agrees_with_the_image() -> None:
    """The announced port is Caddy's published one, not one of the internal two."""
    script = ANNOUNCE.read_text(encoding="utf-8")

    assert f'"${{PORT:-{DEFAULT_PORT}}}"' in script
    assert f"process.env.PORT||{DEFAULT_PORT}" in script
    assert f"EXPOSE {DEFAULT_PORT}" in DOCKERFILE
    assert f":{{$PORT:{DEFAULT_PORT}}} {{" in CADDYFILE

    # and it is Caddy's port, so it must not be either server behind it
    for internal in ("3000", "8000"):
        assert internal not in re.sub(r"(?m)^\s*#.*$", "", script), (
            f"the banner mentions {internal}, which is not reachable from outside the container"
        )


def test_it_waits_for_a_real_request_before_announcing() -> None:
    """Printing on start would point people at a URL that 502s for ~20 seconds."""
    script = ANNOUNCE.read_text(encoding="utf-8")
    assert "/api/health" in script
    assert "ready →" in script
