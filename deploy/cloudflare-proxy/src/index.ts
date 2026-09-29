/**
 * Cloudflare Worker in front of a **private** Cloud Run service.
 *
 * Cloud Run here has no `allUsers` binding: the only principal that may invoke
 * it is one service account, and this Worker is the only holder of its key. So
 * `*.run.app` answers 403 to everyone, and the hostname on this zone is the
 * single way in — which is what makes the rest safe:
 *
 *  - Cloudflare's WAF, rate-limiting rules and Access sit in front of the only
 *    route that works. A domain mapping would have to be grey-clouded (Google
 *    issues the certificate), which turns all of that off.
 *  - `TRUST_CLOUDFLARE_IP=1` on the app is sound for the same reason. The app
 *    reads `cf-connecting-ip`, and nobody can reach the container carrying a
 *    forged one, because reaching it at all needs a token only this Worker can
 *    mint.
 *
 * Invoking a private service means an OIDC identity token whose audience is
 * the service's URL. Google mints one in exchange for a JWT signed with the
 * service account's key (RFC 7523), which is what `identityToken()` does. The
 * token lasts an hour and is cached for slightly less, so a request pays that
 * exchange roughly once an hour rather than every time.
 */

export interface Env {
  /** The service's own https://…run.app URL. Also the token's audience. */
  RUN_URL: string;
  /** The service-account key JSON, whole, as a Worker secret. */
  GCP_SA_KEY: string;
}

const TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token";
/** Refreshed this long before it actually expires, so no request races it. */
const EARLY_S = 300;

let cached: { token: string; expires: number } | null = null;
let key: CryptoKey | null = null;

function b64url(bytes: ArrayBuffer | Uint8Array): string {
  const b = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);
  let s = "";
  for (const byte of b) s += String.fromCharCode(byte);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

/** The PEM in the key file -> a WebCrypto signing key. Imported once. */
async function signingKey(pem: string): Promise<CryptoKey> {
  if (key) return key;
  const der = Uint8Array.from(
    atob(pem.replace(/-----[A-Z ]+-----/g, "").replace(/\s+/g, "")),
    (c) => c.charCodeAt(0),
  );
  key = await crypto.subtle.importKey(
    "pkcs8",
    der,
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["sign"],
  );
  return key;
}

async function identityToken(env: Env): Promise<string> {
  const now = Math.floor(Date.now() / 1000);
  if (cached && cached.expires - EARLY_S > now) return cached.token;

  const sa = JSON.parse(env.GCP_SA_KEY) as { client_email: string; private_key: string };
  const header = b64url(new TextEncoder().encode(JSON.stringify({ alg: "RS256", typ: "JWT" })));
  const claims = b64url(
    new TextEncoder().encode(
      JSON.stringify({
        iss: sa.client_email,
        aud: TOKEN_ENDPOINT,
        // What the minted token will be *for*: Cloud Run checks that the
        // audience is its own URL, so a token leaked from here cannot be
        // replayed against another service.
        target_audience: env.RUN_URL,
        iat: now,
        exp: now + 3600,
      }),
    ),
  );
  const signed = `${header}.${claims}`;
  const sig = await crypto.subtle.sign(
    "RSASSA-PKCS1-v1_5",
    await signingKey(sa.private_key),
    new TextEncoder().encode(signed),
  );

  const res = await fetch(TOKEN_ENDPOINT, {
    method: "POST",
    headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "urn:ietf:params:oauth:grant-type:jwt-bearer",
      assertion: `${signed}.${b64url(sig)}`,
    }),
  });
  if (!res.ok) throw new Error(`token exchange failed: ${res.status}`);
  const body = (await res.json()) as { id_token?: string };
  if (!body.id_token) throw new Error("token exchange returned no id_token");

  cached = { token: body.id_token, expires: now + 3600 };
  return body.id_token;
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const upstream = new URL(request.url);
    const run = new URL(env.RUN_URL);
    upstream.protocol = run.protocol;
    upstream.hostname = run.hostname;
    upstream.port = run.port;

    const headers = new Headers(request.headers);
    // Whatever the caller sent under this name is theirs, not ours: replaced,
    // never appended to. Same for the forwarded IP — the app trusts
    // `cf-connecting-ip` (TRUST_CLOUDFLARE_IP=1), so it has to be the one
    // Cloudflare wrote on the way in and not one the caller supplied. A
    // subrequest does not carry it over by itself.
    const token = await identityToken(env);
    headers.set("authorization", `Bearer ${token}`);
    const ip = request.headers.get("cf-connecting-ip");
    if (ip) headers.set("cf-connecting-ip", ip);
    else headers.delete("cf-connecting-ip");
    // Cloud Run routes on Host, so it has to stay the service's own.
    headers.set("host", run.hostname);

    return fetch(
      new Request(upstream.toString(), {
        method: request.method,
        headers,
        body: request.body,
        redirect: "manual",
      }),
    );
  },
};
