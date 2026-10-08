"""Render `service.yaml` for one deploy: the image to run, and who serves.

Kept out of the workflow because a heredoc cannot be indented inside a YAML
block scalar without breaking one of the two languages, and because this is the
part with a decision in it — see `_traffic`.

    render.py <image> [currently-serving-revision] [public-origin]
"""

from __future__ import annotations

import pathlib
import sys
from typing import Any
from urllib.parse import urlsplit

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


def render(image: str, current: str = "", public_origin: str = "") -> str:
    service = yaml.safe_load((HERE / "service.yaml").read_text())
    container = service["spec"]["template"]["spec"]["containers"][0]
    container["image"] = image
    if public_origin:
        url = urlsplit(public_origin)
        if (
            url.scheme not in {"http", "https"}
            or not url.hostname
            or url.username is not None
            or url.password is not None
            or url.path not in {"", "/"}
            or url.query
            or url.fragment
        ):
            raise ValueError("PUBLIC_URL must be an HTTP(S) origin without credentials, path, query or fragment")
        _ = url.port  # Reject invalid ports before deploying.
        env = [row for row in container.get("env", []) if row["name"] != "PUBLIC_ORIGIN"]
        env.append({"name": "PUBLIC_ORIGIN", "value": public_origin.rstrip("/")})
        container["env"] = env
    if traffic := _traffic(current):
        service["spec"]["traffic"] = traffic
    return str(yaml.safe_dump(service, sort_keys=False, allow_unicode=True))


if __name__ == "__main__":
    sys.stdout.write(
        render(
            sys.argv[1],
            sys.argv[2] if len(sys.argv) > 2 else "",
            sys.argv[3] if len(sys.argv) > 3 else "",
        )
    )
