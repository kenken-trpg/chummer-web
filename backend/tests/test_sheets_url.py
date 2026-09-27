"""Reading a キャラシテンプレート from its Google Sheets address.

Nothing here reaches the network: every test hands `fetch_sheet` an opener of
its own. What is under test is the part that has to be right — which address is
built, which hops are followed, and what each failure is reported as — not
Google's behaviour.
"""

from __future__ import annotations

import io
import urllib.error
import urllib.request
from typing import Any

import pytest
from limits import parse
from starlette.testclient import TestClient
from xlsx_fixtures import filled

from app.api import deploy
from app.api.deploy import _IMPORT_RATE_LIMIT, _SHEET_URL_RATE_LIMIT, limiter
from app.main import app
from app.notices import NoticeError
from app.sheets_url import MAX_BYTES, MAX_REDIRECTS, _allowed, _CheckedRedirects, _opener, export_url, fetch_sheet

ID = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"
EDIT = f"https://docs.google.com/spreadsheets/d/{ID}/edit?gid=0#gid=0"


class _Response(io.BytesIO):
    """The little of a urllib response these tests use."""

    def __init__(self, body: bytes, url: str = f"https://docs.google.com/spreadsheets/d/{ID}/export") -> None:
        super().__init__(body)
        self._url = url

    def geturl(self) -> str:
        return self._url

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


class _Opener:
    """Answers with what it was given, and records what was asked for."""

    def __init__(self, answer: Any) -> None:
        self.answer = answer
        self.asked: list[str] = []

    def open(self, url: str, timeout: float | None = None) -> Any:
        self.asked.append(url)
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


# --- which address is built -----------------------------------------------


@pytest.mark.parametrize(
    "written",
    [
        EDIT,
        f"https://docs.google.com/spreadsheets/d/{ID}",
        f"https://docs.google.com/spreadsheets/d/{ID}/",
        f"  https://docs.google.com/spreadsheets/d/{ID}/edit  ",
    ],
)
def test_an_address_is_rebuilt_from_the_document_id_alone(written: str) -> None:
    assert export_url(written) == f"https://docs.google.com/spreadsheets/d/{ID}/export?format=xlsx"


def test_a_published_sheet_has_its_own_endpoint() -> None:
    """「ウェブに公開」 hands out a different kind of id, which the ordinary
    export address does not accept."""
    written = f"https://docs.google.com/spreadsheets/d/e/2PACX-{ID}/pubhtml"
    assert export_url(written) == f"https://docs.google.com/spreadsheets/d/e/2PACX-{ID}/pub?output=xlsx"


@pytest.mark.parametrize(
    "written",
    [
        "",
        "not a url",
        f"http://docs.google.com/spreadsheets/d/{ID}/edit",  # not https
        f"https://docs.google.com.evil.example/spreadsheets/d/{ID}/edit",
        f"https://evil.example/spreadsheets/d/{ID}/edit",
        f"https://docs.google.com/document/d/{ID}/edit",  # a doc, not a sheet
        "https://docs.google.com/spreadsheets/d/short/edit",
        "file:///etc/passwd",
        "http://169.254.169.254/latest/meta-data/",
    ],
)
def test_what_is_not_a_sheet_is_refused_before_anything_is_opened(written: str) -> None:
    with pytest.raises(NoticeError) as raised:
        export_url(written)
    assert raised.value.notice["key"] == "api.sheetUrlNotASheet"


def test_the_pasted_url_is_never_the_one_fetched() -> None:
    """A query string of someone's choosing does not ride along: only the id is
    taken, and the address is built here."""
    opener = _Opener(_Response(filled()))
    fetch_sheet(f"https://docs.google.com/spreadsheets/d/{ID}/edit?next=https://evil.example", opener)
    assert opener.asked == [f"https://docs.google.com/spreadsheets/d/{ID}/export?format=xlsx"]


# --- which hops are followed ----------------------------------------------


@pytest.mark.parametrize(
    "url,ok",
    [
        ("https://docs.google.com/x", True),
        ("https://doc-0s-1c-sheets.googleusercontent.com/x", True),
        ("https://accounts.google.com/signin", True),
        ("http://docs.google.com/x", False),
        ("https://google.com.evil.example/x", False),
        ("https://evil.example/x", False),
        ("file:///etc/passwd", False),
        ("https://169.254.169.254/", False),
    ],
)
def test_only_https_google_hops_are_followed(url: str, ok: bool) -> None:
    assert _allowed(url) is ok


def test_a_body_served_from_somewhere_else_is_refused() -> None:
    """Belt and braces: the redirect handler will not follow a hop off Google,
    and the host the body actually came from is checked again afterwards."""
    opener = _Opener(_Response(filled(), url="https://evil.example/sheet.xlsx"))
    with pytest.raises(NoticeError) as raised:
        fetch_sheet(EDIT, opener)
    assert raised.value.notice["key"] == "api.sheetUrlFailed"


# --- what each failure is reported as -------------------------------------


def test_a_workbook_comes_back_as_bytes() -> None:
    body = filled()
    assert fetch_sheet(EDIT, _Opener(_Response(body))) == body


@pytest.mark.parametrize("code", [401, 403, 404])
def test_a_sheet_that_needs_an_account_says_so(code: int) -> None:
    error = urllib.error.HTTPError(EDIT, code, "no", {}, None)  # type: ignore[arg-type]
    with pytest.raises(NoticeError) as raised:
        fetch_sheet(EDIT, _Opener(error))
    assert raised.value.notice["key"] == "api.sheetUrlNotShared"


def test_the_sign_in_page_is_not_a_broken_file() -> None:
    """Google answers an unshared sheet with HTML, which would otherwise arrive
    as 「読み込めませんでした」 and send the player looking at their sheet."""
    with pytest.raises(NoticeError) as raised:
        fetch_sheet(EDIT, _Opener(_Response(b"<!DOCTYPE html><title>Sign in</title>")))
    assert raised.value.notice["key"] == "api.sheetUrlNotShared"


def test_a_server_error_is_not_read_as_unshared() -> None:
    error = urllib.error.HTTPError(EDIT, 500, "boom", {}, None)  # type: ignore[arg-type]
    with pytest.raises(NoticeError) as raised:
        fetch_sheet(EDIT, _Opener(error))
    assert raised.value.notice["key"] == "api.sheetUrlFailed"


def test_a_connection_that_never_answers_is_reported_not_raised() -> None:
    with pytest.raises(NoticeError) as raised:
        fetch_sheet(EDIT, _Opener(urllib.error.URLError(TimeoutError("timed out"))))
    assert raised.value.notice["key"] == "api.sheetUrlFailed"


def test_more_than_the_upload_path_allows_is_refused() -> None:
    """Read with one byte to spare rather than whole, so an endless body is not
    held in memory to be measured."""
    with pytest.raises(NoticeError) as raised:
        fetch_sheet(EDIT, _Opener(_Response(b"PK" + b"\0" * MAX_BYTES)))
    assert raised.value.notice["key"] == "api.sheetUrlTooBig"


def test_the_environments_proxies_are_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    """A proxy in the container must not become the thing being talked to.

    `ProxyHandler({})` carries no per-scheme method, so urllib drops it from the
    opener entirely — which is the point: what is left has no proxy handler at
    all, where a default opener would have one loaded from the environment.
    """
    monkeypatch.setenv("https_proxy", "http://127.0.0.1:9/")
    monkeypatch.setenv("http_proxy", "http://127.0.0.1:9/")
    default = urllib.request.build_opener()
    assert any(isinstance(h, urllib.request.ProxyHandler) and h.proxies for h in default.handlers)
    assert not any(isinstance(h, urllib.request.ProxyHandler) for h in _opener().handlers)


def test_every_hop_is_checked_by_the_opener_that_is_used() -> None:
    """The handler that vets redirects is the one really installed, not just a
    class sitting in the module."""
    installed = [h for h in _opener().handlers if isinstance(h, urllib.request.HTTPRedirectHandler)]
    assert installed and all(type(h) is _CheckedRedirects for h in installed)
    assert installed[0].max_redirections == MAX_REDIRECTS


def test_a_hop_off_google_is_not_followed() -> None:
    """Returning None is how urllib is told not to follow: the 30x then comes
    back as an error rather than as a quiet fetch of somewhere else."""
    handler = _CheckedRedirects()
    assert handler.redirect_request(None, None, 302, "found", {}, "https://evil.example/x") is None


# --- through the API ------------------------------------------------------


def test_the_route_imports_a_sheet_and_answers_like_the_upload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.api.characters.fetch_sheet", lambda url: filled())
    with TestClient(app) as client:
        res = client.post("/api/characters/import-sheet-url", json={"url": EDIT})
    assert res.status_code == 200
    body = res.json()
    assert body["character"]["metatype"]
    assert set(body) == {"character", "warnings", "pending_gear"}


def test_the_route_says_what_went_wrong_rather_than_failing() -> None:
    with TestClient(app) as client:
        res = client.post("/api/characters/import-sheet-url", json={"url": "https://evil.example/"})
    assert res.status_code == 400
    assert res.json()["detail"]["key"] == "api.sheetUrlNotASheet"


# --- how often it may be asked --------------------------------------------


def test_the_route_is_limited_more_tightly_than_the_other_imports() -> None:
    """Not about load: this is the only route that makes this host fetch from
    somewhere else, so the number that matters is how much traffic a caller can
    aim at Google through it, not how much CPU it costs here."""
    per_caller = parse(_SHEET_URL_RATE_LIMIT)
    imports = parse(_IMPORT_RATE_LIMIT)
    assert per_caller.amount / per_caller.GRANULARITY.seconds < imports.amount / imports.GRANULARITY.seconds


def _fetches(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Patch the fetch out and record what the route would have asked for."""
    asked: list[str] = []

    def fake(url: str) -> bytes:
        asked.append(url)
        return filled()

    monkeypatch.setattr("app.api.characters.fetch_sheet", fake)
    limiter.reset()
    return asked


def test_a_caller_asking_over_and_over_is_refused_before_the_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    asked = _fetches(monkeypatch)
    allowed = parse(_SHEET_URL_RATE_LIMIT).amount
    with TestClient(app) as client:
        codes = [
            client.post("/api/characters/import-sheet-url", json={"url": EDIT}).status_code for _ in range(allowed + 2)
        ]
    assert codes[:allowed] == [200] * allowed
    assert codes[allowed:] == [429, 429]
    # The refusals cost Google nothing: the limit is checked before the fetch.
    assert len(asked) == allowed


def test_the_shared_ceiling_holds_when_every_caller_looks_different(monkeypatch: pytest.MonkeyPatch) -> None:
    """The per-caller limit is keyed on an address, so a caller with many of
    them has a bucket each. This host has one outbound reputation, so there is a
    second count that they all share.

    Both halves are here on purpose: the first shows the addresses really do get
    separate buckets — eight fetches past a five-per-caller limit — so the
    refusals in the second half can only be the shared ceiling.
    """
    asked = _fetches(monkeypatch)
    monkeypatch.setattr(deploy, "_TRUST_CLOUDFLARE_IP", True)
    per_caller = parse(_SHEET_URL_RATE_LIMIT).amount
    monkeypatch.setattr("app.api.characters._SHEET_URL_TOTAL_LIMIT", parse("1000/minute"))

    def ask(client: TestClient, n: int) -> int:
        return client.post(
            "/api/characters/import-sheet-url",
            json={"url": EDIT},
            headers={"cf-connecting-ip": f"203.0.113.{n}"},
        ).status_code

    with TestClient(app) as client:
        loose = [ask(client, n) for n in range(1, per_caller + 4)]
        assert loose == [200] * len(loose) and len(loose) > per_caller, "the buckets are not per address"
        monkeypatch.setattr("app.api.characters._SHEET_URL_TOTAL_LIMIT", parse("1/minute"))
        limiter.reset()
        asked.clear()
        tight = [ask(client, n) for n in range(100, 104)]
    assert tight == [200, 429, 429, 429]
    assert len(asked) == 1


def test_the_shared_refusal_says_to_wait_or_use_the_file(monkeypatch: pytest.MonkeyPatch) -> None:
    _fetches(monkeypatch)
    monkeypatch.setattr("app.api.characters._SHEET_URL_TOTAL_LIMIT", parse("1/minute"))
    with TestClient(app) as client:
        client.post("/api/characters/import-sheet-url", json={"url": EDIT})
        res = client.post("/api/characters/import-sheet-url", json={"url": EDIT})
    assert res.status_code == 429
    assert res.json()["detail"]["key"] == "api.sheetUrlBusy"
