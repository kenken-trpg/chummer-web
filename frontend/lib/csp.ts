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
 */
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
  ].join("; ");
}

/** A fresh, unguessable nonce: 122 random bits from `randomUUID`, base64. */
export function makeNonce(): string {
  return btoa(crypto.randomUUID());
}
