/**
 * The Content-Security-Policy for every page, built per request around a nonce.
 *
 * `script-src` carries the nonce and nothing inline: Next reads the nonce back
 * out of this header while it renders and stamps it on its own bootstrap and
 * bundle tags, so a script an attacker manages to inject has no nonce and does
 * not run. `'strict-dynamic'` lets the scripts that do carry it load the chunks
 * they ask for; browsers that understand it ignore `'self'`, which stays for
 * the ones that do not.
 *
 * `style-src` keeps `'unsafe-inline'` and deliberately has no nonce. React
 * writes `style={...}` as an attribute, a nonce cannot cover an attribute, and
 * a browser that sees a nonce in a directive ignores `'unsafe-inline'` there —
 * so adding one would switch off every inline style in the app. Injected CSS
 * cannot run code; injected script can, and that is what this closes.
 *
 * `img-src` allows `data:` (base64 portraits) and `blob:` (the `.chum5`
 * download's object URL).
 *
 * Violations go to `/api/csp-report`, named twice because browsers are split:
 * `report-uri` is deprecated but is what Safari and older Chrome implement,
 * and `report-to` is the Reporting API's way, which needs the group to be
 * declared in a `Reporting-Endpoints` header — `proxy.ts` sends that alongside
 * this. A browser that understands both uses `report-to` only, so the endpoint
 * receives one report per violation, not two.
 */
export const REPORT_ENDPOINT = "/api/csp-report";

/** The reporting group `report-to` names; declared in `Reporting-Endpoints`. */
export const REPORT_GROUP = "csp";

export function contentSecurityPolicy(nonce: string, { dev = false } = {}): string {
  return [
    "default-src 'self'",
    // React reconstructs server error stacks with eval in development only
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${dev ? " 'unsafe-eval'" : ""}`,
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data: blob:",
    "font-src 'self' data:",
    // the dev server's HMR socket
    `connect-src 'self'${dev ? " ws:" : ""}`,
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
    `report-uri ${REPORT_ENDPOINT}`,
    `report-to ${REPORT_GROUP}`,
  ].join("; ");
}

/** A host and nothing else: `example.com`, `example.com:8443`.
 *
 * `x-forwarded-host` arrives from a proxy, and a second hop may append to it
 * rather than replace it, so only the first value is read and it has to be a
 * bare host. A scheme, a path, a `@`, a space or a `"` would be spliced
 * straight into a response header, which is the one thing this must not do.
 */
const BARE_HOST = /^[a-z0-9.-]+(?::\d{1,5})?$/i;

/** Hosts that are this machine, where the proxy in front speaks plain HTTP. */
const LOOPBACK = /^(?:localhost|127\.\d+\.\d+\.\d+|\[::1\]|[a-z0-9-]+\.localhost)(?::\d+)?$/i;

/**
 * Where the browser can reach this app from the outside.
 *
 * Needed because the CSP's `Reporting-Endpoints` has to carry an absolute URL
 * and `request.nextUrl.origin` is the *internal* one: in every deploy Next sits
 * behind a proxy that forwards to `127.0.0.1:3000`, so the header read
 * `csp="http://localhost:3000/api/csp-report"` and no violation report ever
 * left the browser.
 *
 * `PUBLIC_ORIGIN` wins when it is set, because a deploy that knows its own
 * address should not have to infer it. Otherwise the proxy's
 * `x-forwarded-host` is used: `deploy/Caddyfile` sets it from the real `Host`
 * and the Cloudflare Worker sets it from the URL the visitor asked for, both
 * replacing whatever the caller put there. With neither, there is no proxy and
 * the internal origin is the real one.
 *
 * The scheme is *not* read from `x-forwarded-proto`. A proxy that forwards the
 * host at all is the one terminating TLS — that is why it is in front — so the
 * only question is whether the host is this machine, and that the host itself
 * answers. One fewer spoofable input for a value that ends up in a response
 * header.
 */
export function publicOrigin(
  headers: { get(name: string): string | null },
  fallback: string,
  configured?: string,
): string {
  if (configured) {
    try {
      return new URL(configured).origin;
    } catch {
      // a malformed PUBLIC_ORIGIN is worth ignoring, not worth a 500
    }
  }
  const host = (headers.get("x-forwarded-host") ?? "").split(",")[0]!.trim();
  if (!BARE_HOST.test(host)) return fallback;
  return `${LOOPBACK.test(host) ? "http" : "https"}://${host}`;
}

/** The `Reporting-Endpoints` header value declaring the group `report-to` names. */
export function reportingEndpoints(origin: string): string {
  return `${REPORT_GROUP}="${new URL(REPORT_ENDPOINT, origin).toString()}"`;
}

/** A fresh, unguessable nonce: 122 random bits from `randomUUID`, base64. */
export function makeNonce(): string {
  return btoa(crypto.randomUUID());
}
