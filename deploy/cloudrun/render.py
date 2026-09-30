"""Render `service.yaml` for one deploy: the image to run, and who serves.

Kept out of the workflow because a heredoc cannot be indented inside a YAML
block scalar without breaking one of the two languages, and because this is the
part with a decision in it — see `_traffic`.

    render.py <image> [currently-serving-revision]
"""

from __future__ import annotations

import pathlib
import sys
from typing import Any

import yaml

HERE = pathlib.Path(__file__).parent


def _traffic(current: str) -> list[dict[str, Any]]:
    """Hold traffic where it is, and give the new revision a name to reach it by.

    The new revision is created serving nothing, so `services replace` has to
    wait for it to become Ready — its startup probe asks `/api/ready`, which is
    503 until the warm-up has finished — before anything moves. A revision that
    cannot serve therefore fails the deploy while the old one keeps every
    request, and the traffic switch afterwards is the only step that changes
    what a visitor sees.

    On the first deploy there is no revision to hold traffic on, so the file's
    own `latestRevision: true` stands and the new one takes it all.
    """
    if not current:
        return []
    return [
        {"revisionName": current, "percent": 100},
        {"latestRevision": True, "percent": 0, "tag": "candidate"},
    ]


def render(image: str, current: str = "") -> str:
    service = yaml.safe_load((HERE / "service.yaml").read_text())
    service["spec"]["template"]["spec"]["containers"][0]["image"] = image
    if traffic := _traffic(current):
        service["spec"]["traffic"] = traffic
    return str(yaml.safe_dump(service, sort_keys=False, allow_unicode=True))


if __name__ == "__main__":
    sys.stdout.write(render(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else ""))
