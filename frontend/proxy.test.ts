import { NextRequest } from "next/server";
import { afterEach, describe, expect, it, vi } from "vitest";
import { REPORT_GROUP } from "@/lib/csp";
import { proxy } from "./proxy";

function request(url: string, headers: Record<string, string> = {}): NextRequest {
  return new NextRequest(new Request(url, { headers }));
}

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("proxy", () => {
  it("puts the same policy on the request and the response", () => {
    // the request copy is what Next reads the nonce back out of while it
    // renders; the response copy is what the browser enforces
    const response = proxy(request("http://127.0.0.1:3000/"));
    const csp = response.headers.get("Content-Security-Policy");
    expect(csp).toContain("'strict-dynamic'");
    expect(response.headers.get("x-middleware-override-headers")).toContain(
      "content-security-policy",
    );
  });

  it("mints a different nonce for every request", () => {
    const nonce = (res: Response) =>
      /'nonce-([^']+)'/.exec(res.headers.get("Content-Security-Policy") ?? "")?.[1];
    expect(nonce(proxy(request("http://127.0.0.1:3000/")))).not.toBe(
      nonce(proxy(request("http://127.0.0.1:3000/"))),
    );
  });

  it("points violation reports at the address the visitor used, not the proxy's", () => {
    const response = proxy(
      request("http://127.0.0.1:3000/", { "x-forwarded-host": "chummer.example" }),
    );
    expect(response.headers.get("Reporting-Endpoints")).toBe(
      `${REPORT_GROUP}="https://chummer.example/api/csp-report"`,
    );
  });

  it("falls back to its own origin when nothing is in front of it", () => {
    // `nextUrl` normalises the loopback address to `localhost`, which is how
    // the broken header read in production: that origin is the one Next can
    // see from inside the container, and it is not reachable from a browser
    const response = proxy(request("http://127.0.0.1:3000/"));
    expect(response.headers.get("Reporting-Endpoints")).toBe(
      `${REPORT_GROUP}="http://localhost:3000/api/csp-report"`,
    );
  });

  it("lets PUBLIC_ORIGIN override what the proxy claims", () => {
    vi.stubEnv("PUBLIC_ORIGIN", "https://stated.example");
    const response = proxy(
      request("http://127.0.0.1:3000/", { "x-forwarded-host": "inner.invalid" }),
    );
    expect(response.headers.get("Reporting-Endpoints")).toBe(
      `${REPORT_GROUP}="https://stated.example/api/csp-report"`,
    );
  });

  it("loosens the policy only when NODE_ENV says development", () => {
    vi.stubEnv("NODE_ENV", "development");
    expect(
      proxy(request("http://127.0.0.1:3000/")).headers.get("Content-Security-Policy"),
    ).toContain("'unsafe-eval'");
    vi.stubEnv("NODE_ENV", "production");
    expect(
      proxy(request("http://127.0.0.1:3000/")).headers.get("Content-Security-Policy"),
    ).not.toContain("'unsafe-eval'");
  });
});
