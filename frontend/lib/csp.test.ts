import { describe, expect, it } from "vitest";
import {
  REPORT_ENDPOINT,
  REPORT_GROUP,
  contentSecurityPolicy,
  makeNonce,
  publicOrigin,
  reportingEndpoints,
} from "./csp";

function directive(csp: string, name: string): string {
  return csp.split("; ").find((part) => part.startsWith(`${name} `)) ?? "";
}

describe("contentSecurityPolicy", () => {
  it("lets scripts run by nonce only, never inline or by eval", () => {
    const scripts = directive(contentSecurityPolicy("abc"), "script-src");
    expect(scripts).toContain("'nonce-abc'");
    expect(scripts).toContain("'strict-dynamic'");
    expect(scripts).not.toContain("'unsafe-inline'");
    expect(scripts).not.toContain("'unsafe-eval'");
  });

  it("keeps a nonce out of style-src, where it would switch off every style attribute", () => {
    const styles = directive(contentSecurityPolicy("abc"), "style-src");
    expect(styles).toBe("style-src 'self' 'unsafe-inline'");
  });

  it("loosens only what the dev server needs, and only in dev", () => {
    const csp = contentSecurityPolicy("abc", { dev: true });
    expect(directive(csp, "script-src")).toContain("'unsafe-eval'");
    expect(directive(csp, "connect-src")).toBe("connect-src 'self' ws:");
    expect(directive(contentSecurityPolicy("abc"), "connect-src")).toBe("connect-src 'self'");
  });

  it("still refuses framing, plugins and a rebased document", () => {
    const csp = contentSecurityPolicy("abc");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).toContain("object-src 'none'");
    expect(csp).toContain("base-uri 'self'");
  });

  it("names the report endpoint both ways, so no browser stays silent", () => {
    const csp = contentSecurityPolicy("abc");
    // report-uri is deprecated but is what Safari implements; report-to is the
    // Reporting API's, and `proxy.ts` declares the group it names
    expect(directive(csp, "report-uri")).toBe(`report-uri ${REPORT_ENDPOINT}`);
    expect(directive(csp, "report-to")).toBe(`report-to ${REPORT_GROUP}`);
  });
});

describe("makeNonce", () => {
  it("is different every time and safe to drop into a header", () => {
    const seen = new Set(Array.from({ length: 50 }, makeNonce));
    expect(seen.size).toBe(50);
    for (const nonce of seen) expect(nonce).toMatch(/^[A-Za-z0-9+/]+=*$/);
  });
});

const INTERNAL = "http://localhost:3000";

function headers(values: Record<string, string>): Headers {
  return new Headers(values);
}

describe("publicOrigin", () => {
  it("is the internal origin when nothing is in front", () => {
    expect(publicOrigin(headers({}), INTERNAL)).toBe(INTERNAL);
  });

  it("is what the proxy forwarded, over https", () => {
    // the bug this exists for: without it the report endpoint was
    // `http://localhost:3000/api/csp-report` on every deploy
    expect(publicOrigin(headers({ "x-forwarded-host": "chummer.example" }), INTERNAL)).toBe(
      "https://chummer.example",
    );
  });

  it("keeps the port the proxy named", () => {
    expect(publicOrigin(headers({ "x-forwarded-host": "chummer.example:8443" }), INTERNAL)).toBe(
      "https://chummer.example:8443",
    );
  });

  it("stays on http when the forwarded host is this machine", () => {
    for (const host of ["localhost:8080", "127.0.0.1:8080", "app.localhost"]) {
      expect(publicOrigin(headers({ "x-forwarded-host": host }), INTERNAL)).toBe(`http://${host}`);
    }
  });

  it("reads only the first value when a second proxy appended its own", () => {
    expect(
      publicOrigin(headers({ "x-forwarded-host": "chummer.example, inner.invalid" }), INTERNAL),
    ).toBe("https://chummer.example");
  });

  it("refuses anything that is not a bare host rather than splicing it into a header", () => {
    for (const host of [
      'evil.test" , x="https://evil.test',
      "https://evil.test",
      "chummer.example/path",
      "user@evil.test",
      "chummer example",
      "",
      "chummer.example:99999999",
    ]) {
      expect(publicOrigin(headers({ "x-forwarded-host": host }), INTERNAL)).toBe(INTERNAL);
    }
  });

  it("ignores a forwarded scheme, because the host alone decides", () => {
    const downgraded = headers({
      "x-forwarded-host": "chummer.example",
      "x-forwarded-proto": "http",
    });
    expect(publicOrigin(downgraded, INTERNAL)).toBe("https://chummer.example");
  });

  it("lets a deploy state its own address and win", () => {
    const forwarded = headers({ "x-forwarded-host": "inner.invalid" });
    expect(publicOrigin(forwarded, INTERNAL, "https://chummer.example")).toBe(
      "https://chummer.example",
    );
    expect(publicOrigin(forwarded, INTERNAL, "https://chummer.example/ignored/path")).toBe(
      "https://chummer.example",
    );
  });

  it("falls back rather than throwing when PUBLIC_ORIGIN is malformed", () => {
    expect(publicOrigin(headers({}), INTERNAL, "not a url")).toBe(INTERNAL);
  });
});

describe("reportingEndpoints", () => {
  it("names the group the CSP's report-to names, with an absolute URL", () => {
    expect(reportingEndpoints("https://chummer.example")).toBe(
      `${REPORT_GROUP}="https://chummer.example${REPORT_ENDPOINT}"`,
    );
  });
});
