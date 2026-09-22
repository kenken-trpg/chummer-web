"""Deploy-time knobs read from the environment, and the caller identity the
rate limiter keys on.

Read through the module (`deploy.TRUSTED_PROXY_HOPS`) rather than imported by
name wherever the value is used at request time, so a test that patches it
here is seen everywhere.
"""

from __future__ import annotations

import os

from fastapi import Request
from slowapi import Limiter

# --- deploy-time knobs (env-overridable) --------------------------------------
_ALLOWED_ORIGINS = [
    o.strip()
    for o in (os.environ.get("ALLOWED_ORIGINS") or "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if o.strip()
]
# 12 MiB: a CharacterState carrying base64 portraits (≤3 MB image each) is POSTed whole
_MAX_REQUEST_BYTES = int(os.environ.get("MAX_REQUEST_BYTES") or 12 * 1024 * 1024)
_RATE_LIMIT = os.environ.get("RATE_LIMIT") or "120/minute"
_IMPORT_RATE_LIMIT = os.environ.get("IMPORT_RATE_LIMIT") or "20/minute"
# A page can legitimately fire one report per violation per load, so this is
# looser than the import limit and tighter than the default.
_CSP_REPORT_RATE_LIMIT = os.environ.get("CSP_REPORT_RATE_LIMIT") or "60/minute"
#: Reporting API batches; a browser sends a handful, never hundreds.
_CSP_REPORTS_PER_REQUEST = 20
# How many entries to count in from the *right* of `x-forwarded-for` to find the
# real client. 0 (default) = don't trust `x-forwarded-for` at all — a direct
# client can put anything in it, and taking the leftmost hop lets it forge a
# fresh IP per request and walk straight past every rate limit. Behind a
# platform LB (Cloud Run / Fly) set 2; behind a single self-managed reverse
# proxy that appends the peer, set 1.
_TRUSTED_PROXY_HOPS = int(os.environ.get("TRUSTED_PROXY_HOPS") or 0)
#: `cf-connecting-ip` is only meaningful behind Cloudflare, which overwrites
#: it on the way in. Anywhere else the caller writes it, and a fresh value per
#: request walks past every rate limit — so it is read only when the deploy
#: says it is behind Cloudflare.
_TRUST_CLOUDFLARE_IP = (os.environ.get("TRUST_CLOUDFLARE_IP") or "").strip().lower() in {"1", "true", "yes", "on"}


def _client_ip(request: Request) -> str:
    """Best-effort caller identity for rate limiting. Only reads forwarded
    headers that infrastructure we trust is known to have written."""
    cf = (request.headers.get("cf-connecting-ip") or "").strip() if _TRUST_CLOUDFLARE_IP else ""
    if cf:
        return cf
    if _TRUSTED_PROXY_HOPS > 0:
        hops = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
        if len(hops) >= _TRUSTED_PROXY_HOPS:
            return hops[-_TRUSTED_PROXY_HOPS]
    return request.client.host if request.client else "anon"


limiter = Limiter(key_func=_client_ip, default_limits=[_RATE_LIMIT])
