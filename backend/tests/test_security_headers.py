"""The three senders of the security headers, held to one set.

A response reaches the browser through one of three things, and each sets the
headers itself:

* ``deploy/Caddyfile`` — the bundled container's edge, in front of both
* ``frontend/next.config.ts`` — a split deploy, or a bare ``next start``
* ``backend/app/main.py`` — every ``/api`` answer, and a split deploy's backend

There is nowhere for one literal to live across a Caddyfile, a TypeScript
config and a Python dict, so this is the shared place: it reads all three and
compares them. Two differences are deliberate and named below; everything else
agreeing is the point.

The CSP is *not* part of the set. A page's carries a per-request nonce and is
minted in ``frontend/proxy.ts``; Caddy only supplies a fallback for responses
that arrive without one, and the API sends the strict policy an answer that
renders nothing can afford. ``frontend/lib/csp.test.ts`` covers that side.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.main import _PERMISSIONS_POLICY, _SECURITY_HEADERS

_ROOT = Path(__file__).resolve().parents[2]
_CADDYFILE = _ROOT / "deploy" / "Caddyfile"
_NEXT_CONFIG = _ROOT / "frontend" / "next.config.ts"

#: What all three must send, byte for byte.
SHARED = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Cross-Origin-Resource-Policy": "same-site",
    "Permissions-Policy": _PERMISSIONS_POLICY,
}

#: Deliberate divergence. A document's referrer policy governs the links and
#: sub-requests the page makes; a JSON body has none, so the API can afford the
#: stricter value and does.
REFERRER = {"document": "strict-origin-when-cross-origin", "api": "no-referrer"}

#: Cross-Origin-Embedder-Policy is deliberately absent. Every resource this app
#: loads is `'self'` (see `lib/csp.ts`), so `require-corp` would isolate nothing
#: that is not already same-origin, and nothing here needs
#: `crossOriginIsolated`. It would only break the first cross-origin embed
#: somebody adds, silently, in production.
NOT_SENT = {"Cross-Origin-Embedder-Policy"}


def _caddy_headers() -> dict[str, str]:
    """The `header { ... }` block, as `{name: value}`.

    A leading `-` removes a header and `?` means "only if the upstream sent
    none"; neither is a value this set is about, so both are skipped.
    """
    text = _CADDYFILE.read_text(encoding="utf-8")
    block = text[text.index("\theader {") :]
    block = block[: block.index("\n\t}")]
    out: dict[str, str] = {}
    for line in block.split("\n")[1:]:
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-") or line.startswith("?"):
            continue
        name, _, value = line.partition(" ")
        out[name] = value.strip().strip('"')
    return out


def _next_headers() -> dict[str, str]:
    """The `securityHeaders` array from `next.config.ts`.

    A value is either a string literal or the name of a const defined above it
    (`permissionsPolicy`, built by joining a list), so both forms are resolved.
    """
    text = _NEXT_CONFIG.read_text(encoding="utf-8")
    consts = {
        "permissionsPolicy": ", ".join(
            f"{feature}=()" for feature in re.findall(r'^  "([a-z-]+)",$', text[: text.index(".map((feature)")], re.M)
        )
    }
    block = text[text.index("const securityHeaders = [") :]
    block = block[: block.index("\n];")]
    out: dict[str, str] = {}
    for key, literal, name in re.findall(r'key: "([^"]+)", value: (?:"([^"]*)"|(\w+))', block):
        out[key] = literal if not name else consts[name]
    return out


def test_the_three_senders_agree_on_the_shared_headers() -> None:
    senders = {
        "Caddyfile": _caddy_headers(),
        "next.config.ts": _next_headers(),
        "main.py": dict(_SECURITY_HEADERS),
    }
    drift = [
        f"{where} sends {name}={sent.get(name)!r}, want {want!r}"
        for name, want in SHARED.items()
        for where, sent in senders.items()
        if sent.get(name) != want
    ]
    assert not drift, "security headers drifted:\n  " + "\n  ".join(drift)


def test_the_referrer_policy_differs_only_where_it_is_meant_to() -> None:
    assert _caddy_headers()["Referrer-Policy"] == REFERRER["document"]
    assert _next_headers()["Referrer-Policy"] == REFERRER["document"]
    assert _SECURITY_HEADERS["Referrer-Policy"] == REFERRER["api"]


def test_nobody_sends_the_headers_we_decided_against() -> None:
    for where, sent in (
        ("Caddyfile", _caddy_headers()),
        ("next.config.ts", _next_headers()),
        ("main.py", dict(_SECURITY_HEADERS)),
    ):
        overreach = NOT_SENT & set(sent)
        assert not overreach, f"{where} sends {sorted(overreach)} — see NOT_SENT for why it should not"


def test_permissions_policy_switches_every_feature_off() -> None:
    """A `same-origin` allow-list would be a promise this app does not need to
    make; `()` is "nobody, not even us"."""
    features = dict(part.strip().split("=", 1) for part in _PERMISSIONS_POLICY.split(","))
    assert set(features.values()) == {"()"}
    for expected in ("camera", "microphone", "geolocation", "payment"):
        assert expected in features


def test_the_api_actually_sends_them() -> None:
    """The dict is only a dict until the middleware puts it on a response."""
    from fastapi.testclient import TestClient

    from app.main import app

    response = TestClient(app).get("/api/health", headers={"cf-connecting-ip": "203.0.113.9"})
    assert response.status_code == 200
    for name, value in _SECURITY_HEADERS.items():
        assert response.headers[name] == value
