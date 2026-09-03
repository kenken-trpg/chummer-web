import type { NextConfig } from "next";

// The browser calls the API at a relative /api/*; Next proxies it to the
// FastAPI backend. Override the target for a split deploy (frontend and
// backend on different hosts) with BACKEND_ORIGIN.
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN ?? "http://127.0.0.1:8000";

// In the bundled container the security headers come from Caddy (deploy/
// Caddyfile). These mirror that set so a split deploy or a bare `next start`
// behind a plain proxy still gets clickjacking / MIME-sniff / referrer
// protection. The CSP is production-only: `next dev` needs 'unsafe-eval' for
// HMR, and it must stay in sync with the Caddyfile.
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
];

if (process.env.NODE_ENV === "production") {
  securityHeaders.push({
    key: "Content-Security-Policy",
    value: [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'",
      "style-src 'self' 'unsafe-inline'",
      "img-src 'self' data: blob:",
      "font-src 'self' data:",
      "connect-src 'self'",
      "object-src 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "frame-ancestors 'none'",
    ].join("; "),
  });
}

const nextConfig: NextConfig = {
  // self-contained server bundle for the container (`node server.js`)
  output: "standalone",
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND_ORIGIN}/api/:path*` }];
  },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
