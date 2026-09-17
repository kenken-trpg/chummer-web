import { expect, test } from "@playwright/test";

/**
 * What the production server actually sends. `lib/csp.test.ts` checks the
 * policy string; only a built server shows how `next.config.ts` headers,
 * `proxy.ts` and the `/api` rewrite combine. No browser: `request` only.
 */

const BASELINE = {
  "x-content-type-options": "nosniff",
  "x-frame-options": "DENY",
};

for (const path of ["/", "/share"]) {
  test(`${path} is framed by nobody and carries a nonce CSP`, async ({ request }) => {
    const res = await request.get(path);
    expect(res.status()).toBe(200);
    const headers = res.headers();
    for (const [key, value] of Object.entries(BASELINE)) expect(headers[key]).toBe(value);
    expect(headers["referrer-policy"]).toBe("strict-origin-when-cross-origin");
    expect(headers["cross-origin-opener-policy"]).toBe("same-origin");

    const csp = headers["content-security-policy"] ?? "";
    expect(csp).toMatch(/script-src [^;]*'nonce-/);
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).toContain("object-src 'none'");
    // a production build must not carry the dev server's allowances
    expect(csp).not.toContain("'unsafe-eval'");
    expect(csp).not.toContain("ws:");
  });
}

test("/api keeps the backend's own locked-down CSP through the rewrite", async ({ request }) => {
  const res = await request.get("/api/health");
  expect(res.ok()).toBe(true);
  const headers = res.headers();
  for (const [key, value] of Object.entries(BASELINE)) expect(headers[key]).toContain(value);

  // proxy.ts must not match /api: its page policy would loosen this one
  const csp = headers["content-security-policy"] ?? "";
  expect(csp).toContain("default-src 'none'");
  expect(csp).not.toContain("nonce-");
});

test("a request body over the backend's 12 MB cap is refused, not buffered", async ({
  request,
}) => {
  // The server answers once the cap is crossed, without reading the rest, so
  // the client sees either the 413 or a reset mid-upload depending on timing.
  // Both are a refusal; a 2xx or 400 would mean the body was taken in whole.
  // Windows reports the same cut as ECONNABORTED rather than ECONNRESET.
  const outcome = await request
    .post("/api/characters/import", {
      headers: { "content-type": "application/json" },
      data: `{"name":"${"a".repeat(13 * 1024 * 1024)}"}`,
    })
    .then(
      (res) => res.status(),
      (err: Error) =>
        /ECONNRESET|ECONNABORTED|EPIPE|socket hang up/.test(err.message) ? "reset" : err.message,
    );
  expect([413, "reset"]).toContain(outcome);
});
