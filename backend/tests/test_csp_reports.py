"""`POST /api/csp-report` — where a Content-Security-Policy violation lands.

Without it the policy is enforced and nobody finds out: a directive that is too
tight breaks a feature silently, and one that is too loose is only discovered by
whoever exploits it.

This is the only endpoint whose body is written by something other than our own
client, which is what most of these tests are about: it answers 204 to anything,
keeps only the fields it knows, truncates them, and cannot be made to write a
second log line.
"""

from __future__ import annotations

import json
import logging

import pytest
from starlette.testclient import TestClient

from app.api.csp import _CSP_REPORT_FIELDS, _csp_report_fields
from app.main import app

client = TestClient(app)

#: A distinct source IP per test, so the shared rate limiter does not leak
#: between them the way it would on a single address.
_IPS = iter(f"203.0.113.{n}" for n in range(30, 90))


@pytest.fixture
def ip() -> dict[str, str]:
    return {"cf-connecting-ip": next(_IPS)}


def _report_uri_body() -> bytes:
    """What `report-uri` sends: one object under a `csp-report` key."""
    return json.dumps(
        {
            "csp-report": {
                "document-uri": "https://example.test/chargen",
                "violated-directive": "script-src",
                "effective-directive": "script-src-elem",
                "blocked-uri": "https://evil.test/x.js",
                "disposition": "enforce",
                "status-code": 200,
            }
        }
    ).encode()


def _reporting_api_body() -> bytes:
    """What the Reporting API sends: a *list* of `{type, body}`."""
    return json.dumps(
        [
            {
                "type": "csp-violation",
                "url": "https://example.test/chargen",
                "body": {
                    "documentURL": "https://example.test/chargen",
                    "effective-directive": "img-src",
                    "blocked-uri": "https://evil.test/pixel.gif",
                    "disposition": "enforce",
                },
            }
        ]
    ).encode()


@pytest.mark.parametrize(
    ("label", "body", "expected"),
    [
        ("report-uri", _report_uri_body(), "https://evil.test/x.js"),
        ("reporting-api", _reporting_api_body(), "https://evil.test/pixel.gif"),
    ],
)
def test_both_report_shapes_are_logged(
    label: str, body: bytes, expected: str, ip: dict[str, str], caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger="chummer_web"):
        response = client.post(
            "/api/csp-report",
            content=body,
            headers={**ip, "content-type": "application/csp-report"},
        )
    assert response.status_code == 204
    lines = [r for r in caplog.records if r.getMessage().startswith("csp violation")]
    assert len(lines) == 1, label
    assert lines[0].csp_report["blocked-uri"] == expected  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    "body",
    [b"", b"not json", b"null", b"[]", b'{"csp-report": "a string"}', b"[1, 2, 3]"],
    ids=["empty", "garbage", "null", "empty-list", "wrong-type", "scalars"],
)
def test_a_malformed_body_is_204_and_silent(body: bytes, ip: dict[str, str], caplog: pytest.LogCaptureFixture) -> None:
    """There is no caller to tell anything to — the browser ignores the response
    — and a 400 would only invite somebody to probe the parser."""
    with caplog.at_level(logging.INFO, logger="chummer_web"):
        response = client.post("/api/csp-report", content=body, headers=ip)
    assert response.status_code == 204
    assert not [r for r in caplog.records if r.getMessage().startswith("csp violation")]


def test_a_report_cannot_forge_a_second_log_line() -> None:
    """A page can be made to fetch an attacker-chosen URL, and that URL comes
    back in `blocked-uri`. A newline in it would end the log line and start
    another one saying whatever the attacker likes."""
    fields = _csp_report_fields({"blocked-uri": "https://evil.test/\r\nINFO forged line"})
    assert "\n" not in fields["blocked-uri"]
    assert "\r" not in fields["blocked-uri"]


def test_every_field_is_bounded_and_the_rest_dropped() -> None:
    fields = _csp_report_fields(
        {
            "blocked-uri": "https://evil.test/" + "a" * 5_000,
            "script-sample": "x" * 5_000,  # not in the list: a page's own source
            "sneaked-in": "y" * 5_000,
        }
    )
    assert set(fields) == {"blocked-uri"}
    assert len(fields["blocked-uri"]) == _CSP_REPORT_FIELDS["blocked-uri"]


def test_a_batch_is_capped(ip: dict[str, str], caplog: pytest.LogCaptureFixture) -> None:
    """A browser sends a handful per request. A thousand is somebody using the
    endpoint as a log-writing primitive."""
    batch = [{"body": {"blocked-uri": f"https://evil.test/{n}"}} for n in range(200)]
    with caplog.at_level(logging.INFO, logger="chummer_web"):
        response = client.post("/api/csp-report", json=batch, headers=ip)
    assert response.status_code == 204
    logged = [r for r in caplog.records if r.getMessage().startswith("csp violation")]
    assert len(logged) == 20
