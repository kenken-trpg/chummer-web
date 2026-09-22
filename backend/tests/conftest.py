"""Test-wide setup.

The rate limiter counts per client IP, and every test here talks to the app
from the same socket. Tests that need their own bucket send a
`cf-connecting-ip`, which the app reads only when the deploy says it is
behind Cloudflare — so the tests say so.
"""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True, scope="session")
def _trust_forwarded_client_ip() -> None:
    import app.api.deploy

    app.api.deploy._TRUST_CLOUDFLARE_IP = True
