import { afterEach, describe, expect, it, vi } from "vitest";

const headerValues: Record<string, string> = {};

vi.mock("next/headers", () => ({
  headers: async () => new Headers(headerValues),
}));

async function siteOriginWith(values: Record<string, string>, env?: string): Promise<string> {
  for (const key of Object.keys(headerValues)) delete headerValues[key];
  Object.assign(headerValues, values);
  vi.stubEnv("PUBLIC_ORIGIN", env);
  const { siteOrigin } = await import("./site");
  return siteOrigin();
}

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("siteOrigin", () => {
  it("is what the proxy forwarded, which is what the reader typed", () => {
    // the whole reason this is per request: `Sitemap:` and `<loc>` have to be
    // absolute, and a build-time origin is wrong for every deploy but one
    return expect(
      siteOriginWith({ host: "127.0.0.1:3000", "x-forwarded-host": "chummer.example" }),
    ).resolves.toBe("https://chummer.example");
  });

  it("prefers PUBLIC_ORIGIN over any header", () =>
    expect(
      siteOriginWith({ "x-forwarded-host": "wrong.example" }, "https://chummer.example"),
    ).resolves.toBe("https://chummer.example"));

  it("falls back to this request's own Host, over https", () =>
    expect(siteOriginWith({ host: "chummer.example" })).resolves.toBe("https://chummer.example"));

  it("keeps http for a loopback host, so local dev is not told to use TLS", async () => {
    await expect(siteOriginWith({ host: "localhost:3000" })).resolves.toBe("http://localhost:3000");
    await expect(siteOriginWith({ host: "127.0.0.1:3000" })).resolves.toBe("http://127.0.0.1:3000");
  });

  it("has an origin even with no Host at all", () =>
    expect(siteOriginWith({})).resolves.toBe("http://localhost:3000"));

  it.each(["[::1]:3000", "127.0.0.2:3000", "app.localhost:3000"])(
    "uses http for the local host %s, directly and through a proxy",
    async (host) => {
      await expect(siteOriginWith({ host })).resolves.toBe(`http://${host}`);
      await expect(siteOriginWith({ "x-forwarded-host": host })).resolves.toBe(`http://${host}`);
    },
  );

  it.each([
    "not a url",
    "file:///tmp/site",
    "ftp://chummer.example",
    "https://user:pass@chummer.example",
  ])("ignores invalid PUBLIC_ORIGIN %s", (env) =>
    expect(siteOriginWith({ host: "chummer.example" }, env)).resolves.toBe(
      "https://chummer.example",
    ),
  );

  it.each(["evil.example/path", "user@evil.example", "evil.example:99999", "https://evil.example"])(
    "ignores invalid host %s without breaking metadata rendering",
    async (host) => {
      await expect(
        siteOriginWith({ host: "chummer.example", "x-forwarded-host": host }),
      ).resolves.toBe("https://chummer.example");
      await expect(siteOriginWith({ host })).resolves.toBe("http://localhost:3000");
    },
  );

  it("uses the first forwarded host and strips configured paths", async () => {
    await expect(
      siteOriginWith({ "x-forwarded-host": "chummer.example, inner.example" }),
    ).resolves.toBe("https://chummer.example");
    await expect(siteOriginWith({}, "https://chummer.example/path?query#fragment")).resolves.toBe(
      "https://chummer.example",
    );
  });
});
