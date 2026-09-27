"""Fetching a filled-in キャラシテンプレート straight from its Google Sheets URL.

This is the only outbound request the backend makes. Everything else here is
either computed from the vendored game data or sent up by the client, so this
module is written as if it were the only door in the wall:

* **The URL is not used.** What the player pastes is only ever parsed for the
  document id, and the address actually fetched is built here from that id. A
  URL that is not a Google Sheets URL is refused before anything is opened, so
  there is no way to aim this at an address of someone's choosing.
* **Redirects are checked one hop at a time.** Sheets does redirect an export —
  to `*.googleusercontent.com` — so they cannot simply be refused. Each hop has
  to be https and land on a Google host, or it is not followed.
* **The environment's proxies are ignored**, so a `http_proxy` in the container
  cannot quietly become the thing being talked to.
* **The read is capped and timed out**, by the same ceiling the upload path uses.

What this cannot do is read a sheet that is not shared: without a Google
account, only 「リンクを知っている全員」 is readable. Google answers the rest with
its sign-in page, which is HTML rather than a workbook — so that case is
recognised and reported as itself, rather than as a broken file.
"""

from __future__ import annotations

import re
import urllib.error
import urllib.request
from typing import Any

from .notices import NoticeError, notice
from .xlsx_import._sheet import MAX_PART_BYTES

#: The host a sheet is asked for. Fixed: it is not taken from what was pasted.
HOST = "docs.google.com"

#: What a redirect may land on. Google serves the export body from its own user
#: content domain, so the export's first answer is a hop rather than the file.
#: Suffixes only: every host Sheets uses is under one of these two, and a bare
#: `google.com` is not one of them.
ALLOWED_SUFFIXES = (".google.com", ".googleusercontent.com")

#: How many hops are followed before giving up. Google uses one.
MAX_REDIRECTS = 5

#: Seconds. A sheet is a couple of megabytes; this is a stuck connection, not a
#: slow one.
TIMEOUT = 20.0

#: The most that is read. The same ceiling the uploaded-file path uses, so a URL
#: cannot get a bigger workbook through than a file picker can.
MAX_BYTES = MAX_PART_BYTES

_ID = r"[A-Za-z0-9_-]{16,256}"
#: The two shapes a sheet's address comes in: the one in the browser's bar, and
#: the 「ウェブに公開」 one, whose id is a different thing and is fetched
#: differently. Anything else is not a sheet.
_EDIT_URL = re.compile(rf"^https://(?:[a-z0-9-]+\.)?google\.com/spreadsheets/d/({_ID})(?:[/?#].*)?$")
_PUBLISHED_URL = re.compile(rf"^https://(?:[a-z0-9-]+\.)?google\.com/spreadsheets/d/e/({_ID})(?:[/?#].*)?$")

__all__ = ["MAX_BYTES", "export_url", "fetch_sheet"]


def _allowed(url: str) -> bool:
    """Whether a hop may be followed: https, and a Google host."""
    match = re.match(r"^https://([^/:?#]+)", url)
    if not match:
        return False
    host = match.group(1).lower()
    return host.endswith(ALLOWED_SUFFIXES)


def export_url(written: str) -> str:
    """The .xlsx export address for the sheet `written` points at.

    Built from the document id alone. Raises when what was pasted is not a
    Google Sheets URL — which is also the only check standing between this and
    an arbitrary outbound request, so it is deliberately strict rather than
    forgiving.
    """
    url = written.strip()
    published = _PUBLISHED_URL.match(url)
    if published:
        # 「ウェブに公開」 ids are not document ids and have their own endpoint.
        return f"https://{HOST}/spreadsheets/d/e/{published.group(1)}/pub?output=xlsx"
    edit = _EDIT_URL.match(url)
    if edit:
        return f"https://{HOST}/spreadsheets/d/{edit.group(1)}/export?format=xlsx"
    raise NoticeError(notice("api.sheetUrlNotASheet"))


class _CheckedRedirects(urllib.request.HTTPRedirectHandler):
    """Follows a redirect only to https on a Google host.

    Returning ``None`` leaves urllib to raise the 30x as an error, which is what
    a hop pointing somewhere else should be: not followed, and not silent.
    """

    max_redirections = MAX_REDIRECTS

    def redirect_request(self, req: Any, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Any:
        if not _allowed(newurl):
            return None
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _opener() -> urllib.request.OpenerDirector:
    """An opener that ignores the environment's proxies and checks every hop."""
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), _CheckedRedirects())


def fetch_sheet(written: str, opener: urllib.request.OpenerDirector | None = None) -> bytes:
    """The workbook behind a Google Sheets URL, as bytes ready for the importer.

    `opener` is for the tests, which have no business reaching the network.
    """
    url = export_url(written)
    try:
        with (opener or _opener()).open(url, timeout=TIMEOUT) as response:
            if not _allowed(response.geturl()):  # a hop urllib followed on its own
                raise NoticeError(notice("api.sheetUrlFailed"))
            body = bytes(response.read(MAX_BYTES + 1))
    except NoticeError:
        raise
    except urllib.error.HTTPError as exc:
        # 401/403/404 all mean the same thing from out here: this sheet is not
        # readable without an account.
        raise NoticeError(
            notice("api.sheetUrlNotShared" if exc.code in (401, 403, 404) else "api.sheetUrlFailed")
        ) from exc
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise NoticeError(notice("api.sheetUrlFailed")) from exc

    if len(body) > MAX_BYTES:
        raise NoticeError(notice("api.sheetUrlTooBig"))
    if not body.startswith(b"PK"):
        # Google answers a sheet that needs an account with its sign-in page.
        raise NoticeError(notice("api.sheetUrlNotShared"))
    return body
