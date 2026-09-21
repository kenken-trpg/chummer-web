"""`POST /api/csp-report`: where the browser reports a Content-Security-Policy
violation."""

from __future__ import annotations

import json
import logging

from fastapi import APIRouter, Request, Response

from . import deploy
from .deploy import _CSP_REPORT_RATE_LIMIT, _CSP_REPORTS_PER_REQUEST, limiter

_log = logging.getLogger("chummer_web")

router = APIRouter()


#: The report fields worth a log line, and how much of each is kept. A report
#: body is written by the browser but *names* come from the page, and a page can
#: be made to fetch an attacker-chosen URL — so every value is truncated and
#: anything not listed here is dropped rather than logged.
_CSP_REPORT_FIELDS = {
    "document-uri": 200,
    "blocked-uri": 200,
    "effective-directive": 60,
    "violated-directive": 60,
    "disposition": 20,
    "status-code": 8,
}


def _csp_report_fields(report: object) -> dict[str, str]:
    """`{field: value}` for the listed fields, truncated, newlines stripped.

    A newline in a logged value would let a report forge a second log line,
    which matters more here than anywhere else in the app: this is the only
    endpoint whose body is written by something other than our own client.
    """
    if not isinstance(report, dict):
        return {}
    return {
        field: str(report[field]).replace("\r", " ").replace("\n", " ")[:limit]
        for field, limit in _CSP_REPORT_FIELDS.items()
        if report.get(field) not in (None, "")
    }


@router.post("/api/csp-report", status_code=204)
@limiter.limit(_CSP_REPORT_RATE_LIMIT)
async def csp_report(request: Request) -> Response:
    """Where the browser sends a Content-Security-Policy violation.

    Without this the policy is enforced and nobody finds out: a directive that
    is too tight breaks a feature silently, and one that is too loose is only
    discovered by whoever exploits it. `frontend/lib/csp.ts` names this URL in
    `report-uri` and `report-to`, which is why both report shapes are accepted:

    * `report-uri` sends `application/csp-report` — one `{"csp-report": {...}}`
    * the Reporting API sends `application/reports+json` — a *list* of
      `{"type": "csp-violation", "body": {...}}`

    Answers 204 to everything, malformed bodies included. There is no caller to
    tell anything to — the browser sends this and ignores the response — and a
    400 would only invite somebody to probe the parser.

    Extensions and injected scripts generate a steady trickle of reports on any
    public deployment, so these are `info`, not `warning`, and the rate limit is
    its own: a page can fire one report per violation per load.
    """
    try:
        payload = json.loads(await request.body() or b"")
    except ValueError:
        return Response(status_code=204)
    reports = payload if isinstance(payload, list) else [payload]
    for entry in reports[:_CSP_REPORTS_PER_REQUEST]:
        if isinstance(entry, dict):
            fields = _csp_report_fields(entry.get("csp-report") or entry.get("body") or entry)
            if fields:
                _log.info(
                    "csp violation: %s blocked %s",
                    fields.get("effective-directive") or fields.get("violated-directive") or "?",
                    fields.get("blocked-uri") or "?",
                    extra={"csp_report": fields, "client": deploy._client_ip(request)},
                )
    return Response(status_code=204)
