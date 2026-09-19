import { describe, expect, it } from "vitest";
import { REPORT_ENDPOINT, REPORT_GROUP, contentSecurityPolicy, makeNonce } from "./csp";

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
