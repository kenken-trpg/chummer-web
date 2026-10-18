/**
 * The Worker is the only way into production: Cloud Run answers 403 to
 * everyone else, so a mistake here is a total outage, and the first place it
 * shows is the live site. `tsc --noEmit` was all this file had.
 *
 * It runs under plain vitest in Node rather than the Workers runtime. What it
 * needs from the platform — WebCrypto, `fetch`, `Request`/`Headers`, `btoa` —
 * Node has, and `fetch` is stubbed anyway. What that cannot answer is runtime
 * behaviour proper (the real token endpoint, Cloudflare's own headers); what
 * it does answer is every line of logic in `index.ts`.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

type Worker = typeof import("./index").default;

const RUN_URL = "https://chummer-web-wtwm3u6tiq-an.a.run.app";
const TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token";

/** The platform's own base64, so this file needs nothing Node-only — the same
 *  surface the Worker itself is held to. */
function b64(bytes: Uint8Array): string {
  let s = "";
  for (const byte of bytes) s += String.fromCharCode(byte);
  return btoa(s);
}

function unb64url(seg: string): Uint8Array {
  const raw = atob(seg.replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from(raw, (c) => c.charCodeAt(0));
}

/** A throwaway RSA key in the shape the service-account JSON carries one. */
async function serviceAccount() {
  const pair = (await crypto.subtle.generateKey(
    {
      name: "RSASSA-PKCS1-v1_5",
      modulusLength: 2048,
      publicExponent: new Uint8Array([1, 0, 1]),
      hash: "SHA-256",
    },
    true,
    ["sign", "verify"],
  )) as CryptoKeyPair;
  const pkcs8 = (await crypto.subtle.exportKey(
    "pkcs8",
    pair.privateKey,
  )) as ArrayBuffer;
  const body = b64(new Uint8Array(pkcs8)).replace(/(.{64})/g, "$1\n");
  return {
    json: JSON.stringify({
      client_email: "proxy@chummer-web-81738.iam.gserviceaccount.com",
      private_key: `-----BEGIN PRIVATE KEY-----\n${body}\n-----END PRIVATE KEY-----\n`,
    }),
    publicKey: pair.publicKey,
  };
}

function decodeSegment(seg: string): Record<string, unknown> {
  return JSON.parse(new TextDecoder().decode(unb64url(seg)));
}

/** The token endpoint, then the service. Both are stubbed; neither is reached. */
function stubFetch(
  calls: Request[],
  tokenStatus = 200,
  tokenBody: unknown = undefined,
) {
  // A different token each time, so "it reused the cached one" and "it minted
  // a new one" are told apart by the header the service receives.
  let minted = 0;
  const fetchMock = vi.fn(
    async (input: Request | string, init?: RequestInit) => {
      const req = input instanceof Request ? input : new Request(input, init);
      calls.push(req);
      if (req.url === TOKEN_ENDPOINT) {
        minted += 1;
        return new Response(
          JSON.stringify(tokenBody ?? { id_token: `id-token-${minted}` }),
          {
            status: tokenStatus,
            headers: { "content-type": "application/json" },
          },
        );
      }
      return new Response("upstream", { status: 200 });
    },
  );
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

/**
 * A fresh copy per test: the token and the imported signing key are held in
 * module scope, which is the point of them — and which would otherwise leak
 * from one test into the next.
 */
async function freshWorker(): Promise<Worker> {
  vi.resetModules();
  return (await import("./index")).default;
}

let sa: Awaited<ReturnType<typeof serviceAccount>>;
let env: { RUN_URL: string; GCP_SA_KEY: string };
let calls: Request[];

beforeEach(async () => {
  sa = await serviceAccount();
  env = { RUN_URL, GCP_SA_KEY: sa.json };
  calls = [];
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

const tokenCalls = () => calls.filter((c) => c.url === TOKEN_ENDPOINT);
const upstreamCalls = () => calls.filter((c) => c.url !== TOKEN_ENDPOINT);

describe("the identity token", () => {
  it("is a JWT this service account signed, for this service", async () => {
    stubFetch(calls);
    const worker = await freshWorker();
    await worker.fetch(
      new Request("https://chummer-web.millionskenken.org/api/ready"),
      env,
    );

    expect(tokenCalls()).toHaveLength(1);
    const exchange = tokenCalls()[0];
    expect(exchange.method).toBe("POST");
    expect(exchange.headers.get("content-type")).toBe(
      "application/x-www-form-urlencoded",
    );
    const form = new URLSearchParams(await exchange.text());
    expect(form.get("grant_type")).toBe(
      "urn:ietf:params:oauth:grant-type:jwt-bearer",
    );

    const assertion = form.get("assertion")!;
    const [header, claims, sig] = assertion.split(".");
    expect(decodeSegment(header)).toEqual({ alg: "RS256", typ: "JWT" });

    const body = decodeSegment(claims) as Record<string, number | string>;
    expect(body.iss).toBe("proxy@chummer-web-81738.iam.gserviceaccount.com");
    // The exchange is addressed to Google; the minted token is for Cloud Run.
    // Swapping these two is the mistake that leaves a replayable token.
    expect(body.aud).toBe(TOKEN_ENDPOINT);
    expect(body.target_audience).toBe(RUN_URL);
    expect(body.exp).toBe((body.iat as number) + 3600);

    const ok = await crypto.subtle.verify(
      "RSASSA-PKCS1-v1_5",
      sa.publicKey,
      unb64url(sig),
      new TextEncoder().encode(`${header}.${claims}`),
    );
    expect(ok).toBe(true);
  });

  it("is minted once and reused while it is fresh", async () => {
    stubFetch(calls);
    const worker = await freshWorker();
    for (let i = 0; i < 3; i++) {
      await worker.fetch(
        new Request("https://chummer-web.millionskenken.org/"),
        env,
      );
    }
    expect(tokenCalls()).toHaveLength(1);
    expect(upstreamCalls()).toHaveLength(3);
    for (const call of upstreamCalls()) {
      expect(call.headers.get("authorization")).toBe("Bearer id-token-1");
    }
  });

  it("is minted again before it expires, not after", async () => {
    vi.useFakeTimers();
    vi.setSystemTime(new Date("2026-10-12T00:00:00Z"));
    const fetchMock = stubFetch(calls);
    const worker = await freshWorker();
    await worker.fetch(
      new Request("https://chummer-web.millionskenken.org/"),
      env,
    );

    // 54 minutes on: still inside the hour, but not inside the 5-minute margin
    vi.advanceTimersByTime(54 * 60_000);
    await worker.fetch(
      new Request("https://chummer-web.millionskenken.org/"),
      env,
    );
    expect(tokenCalls()).toHaveLength(1);

    // 56 minutes on: within EARLY_S of expiry, so it is replaced early
    fetchMock.mockClear();
    vi.advanceTimersByTime(2 * 60_000 + 1000);
    await worker.fetch(
      new Request("https://chummer-web.millionskenken.org/"),
      env,
    );
    expect(tokenCalls()).toHaveLength(2);
    // and the fresh one is what the service is shown
    expect(upstreamCalls().at(-1)!.headers.get("authorization")).toBe(
      "Bearer id-token-2",
    );
  });

  it("fails loudly when the exchange is refused", async () => {
    stubFetch(calls, 403);
    const worker = await freshWorker();
    await expect(
      worker.fetch(new Request("https://chummer-web.millionskenken.org/"), env),
    ).rejects.toThrow("token exchange failed: 403");
    expect(upstreamCalls()).toHaveLength(0);
  });

  it("fails loudly when the exchange answers 200 with no token", async () => {
    stubFetch(calls, 200, { access_token: "not the one we asked for" });
    const worker = await freshWorker();
    await expect(
      worker.fetch(new Request("https://chummer-web.millionskenken.org/"), env),
    ).rejects.toThrow("returned no id_token");
    expect(upstreamCalls()).toHaveLength(0);
  });
});

describe("the proxied request", () => {
  it("keeps the path, the query and the method, and goes to the service", async () => {
    stubFetch(calls);
    const worker = await freshWorker();
    await worker.fetch(
      new Request(
        "https://chummer-web.millionskenken.org/api/catalog?lang=ja",
        { method: "HEAD" },
      ),
      env,
    );
    const sent = upstreamCalls()[0];
    expect(sent.url).toBe(`${RUN_URL}/api/catalog?lang=ja`);
    expect(sent.method).toBe("HEAD");
    expect(sent.redirect).toBe("manual");
  });

  it("tells the app which name the visitor typed, and Cloud Run its own", async () => {
    stubFetch(calls);
    const worker = await freshWorker();
    await worker.fetch(
      new Request("https://chummer-web.millionskenken.org/api/ready", {
        // what a caller sent under these names is theirs, not ours
        headers: {
          "x-forwarded-host": "evil.example",
          "x-forwarded-proto": "http",
          authorization: "Bearer forged",
        },
      }),
      env,
    );
    const sent = upstreamCalls()[0];
    expect(sent.headers.get("x-forwarded-host")).toBe(
      "chummer-web.millionskenken.org",
    );
    expect(sent.headers.get("x-forwarded-proto")).toBe("https");
    expect(sent.headers.get("authorization")).toBe("Bearer id-token-1");
    expect(sent.headers.get("host")).toBe(new URL(RUN_URL).hostname);
  });

  it("carries the caller's IP over, and sends none when there is none", async () => {
    stubFetch(calls);
    const worker = await freshWorker();
    // TRUST_CLOUDFLARE_IP=1 on the app: this header decides who gets rate
    // limited, so it has to arrive, and it has to be a single value.
    await worker.fetch(
      new Request("https://chummer-web.millionskenken.org/", {
        headers: { "cf-connecting-ip": "203.0.113.7" },
      }),
      env,
    );
    expect(upstreamCalls()[0].headers.get("cf-connecting-ip")).toBe(
      "203.0.113.7",
    );

    await worker.fetch(
      new Request("https://chummer-web.millionskenken.org/"),
      env,
    );
    expect(upstreamCalls()[1].headers.has("cf-connecting-ip")).toBe(false);
  });

  it("hands the service's answer back as it came", async () => {
    stubFetch(calls);
    const worker = await freshWorker();
    const res = await worker.fetch(
      new Request("https://chummer-web.millionskenken.org/"),
      env,
    );
    expect(res.status).toBe(200);
    expect(await res.text()).toBe("upstream");
  });
});

describe("Strict-Transport-Security", () => {
  it("is added to an answer over HTTPS, for this hostname alone", async () => {
    stubFetch(calls);
    const worker = await freshWorker();
    const res = await worker.fetch(
      new Request("https://chummer-web.millionskenken.org/"),
      env,
    );
    expect(res.headers.get("strict-transport-security")).toBe("max-age=300");
    // the rest of the answer is untouched
    expect(res.status).toBe(200);
    expect(await res.text()).toBe("upstream");
  });

  it("replaces one the service sent, rather than doubling it", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async (input: Request | string) =>
        (input instanceof Request ? input.url : input) === TOKEN_ENDPOINT
          ? Response.json({ id_token: "t" })
          : new Response("upstream", {
              status: 302,
              headers: {
                location: "/manual/index.html",
                "strict-transport-security": "max-age=99999999; preload",
              },
            }),
      ),
    );
    const worker = await freshWorker();
    const res = await worker.fetch(
      new Request("https://chummer-web.millionskenken.org/manual"),
      env,
    );
    expect(res.status).toBe(302);
    expect(res.headers.get("location")).toBe("/manual/index.html");
    expect(res.headers.get("strict-transport-security")).toBe("max-age=300");
  });

  it("is not stated over plain HTTP", async () => {
    stubFetch(calls);
    const worker = await freshWorker();
    const res = await worker.fetch(
      new Request("http://chummer-web.millionskenken.org/"),
      env,
    );
    expect(res.headers.has("strict-transport-security")).toBe(false);
  });
});

describe("the keepalive cron", () => {
  it("pings /api/ready with a token and logs what it got", async () => {
    stubFetch(calls);
    const log = vi.spyOn(console, "log").mockImplementation(() => {});
    const waits: Promise<unknown>[] = [];
    const worker = await freshWorker();

    await worker.scheduled({} as ScheduledController, env, {
      waitUntil: (p: Promise<unknown>) => waits.push(p),
    } as unknown as ExecutionContext);
    await Promise.all(waits);

    expect(upstreamCalls()[0].url).toBe(`${RUN_URL}/api/ready`);
    expect(upstreamCalls()[0].headers.get("authorization")).toBe(
      "Bearer id-token-1",
    );
    expect(log).toHaveBeenCalledWith("keepalive: 200");
    log.mockRestore();
  });

  // A cron that throws is a red run every ten minutes for something no
  // visitor saw. It logs and gives up until the next tick instead.
  it("logs and gives up when the token cannot be minted", async () => {
    stubFetch(calls, 500);
    const log = vi.spyOn(console, "log").mockImplementation(() => {});
    const waits: Promise<unknown>[] = [];
    const worker = await freshWorker();

    await worker.scheduled({} as ScheduledController, env, {
      waitUntil: (p: Promise<unknown>) => waits.push(p),
    } as unknown as ExecutionContext);
    await expect(Promise.all(waits)).resolves.toBeDefined();

    expect(upstreamCalls()).toHaveLength(0);
    expect(log).toHaveBeenCalledWith(
      "keepalive failed: token exchange failed: 500",
    );
    log.mockRestore();
  });
});
