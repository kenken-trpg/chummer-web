- **API answers keep their `Referrer-Policy: no-referrer` behind the bundled
  Caddy, and pages no longer say `X-Powered-By: Next.js`.** Caddy set the page
  referrer policy on every response, overwriting the API's stricter one; it is
  now only a fallback. Next's `X-Powered-By` header is switched off.
