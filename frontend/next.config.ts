import type { NextConfig } from "next";

// The browser calls the API at a relative /api/*; Next proxies it to the
// FastAPI backend. Override the target for a split deploy (frontend and
// backend on different hosts) with BACKEND_ORIGIN.
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN ?? "http://127.0.0.1:8000";

// These mirror Caddy's set (deploy/Caddyfile) so a split deploy or a bare
// `next start` behind a plain proxy still gets clickjacking / MIME-sniff /
// referrer protection. The CSP is not here: it carries a per-request nonce, so
// `proxy.ts` sets it.
const securityHeaders = [
  { key: "X-Content-Type-Options", value: "nosniff" },
  { key: "X-Frame-Options", value: "DENY" },
  { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
  { key: "Cross-Origin-Opener-Policy", value: "same-origin" },
];

const nextConfig: NextConfig = {
  // self-contained server bundle for the container (`node server.js`)
  output: "standalone",
  // `next dev` only trusts the hostname it was started with plus `localhost`,
  // and it answers everything else with `Unauthorized` — including the HMR
  // websocket, without which the dev bundle never mounts the app, so the page
  // sits on "読み込み中…" with nothing in the console but a failed handshake.
  // `127.0.0.1` is a different hostname to `localhost`, and it is what
  // `scripts/dev.sh` and half the tooling print. Ignored outside development.
  allowedDevOrigins: ["127.0.0.1"],
  // There used to be an `eslint: { ignoreDuringBuilds: true }` here. Next 16
  // dropped the built-in lint pass from `next build` (and the `eslint` key
  // from NextConfig with it), so there is nothing left to opt out of.
  // Linting is unaffected: `npm run lint` / `npm run check` / the CI frontend
  // job all run `eslint .` directly, over more files than that pass covered.
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND_ORIGIN}/api/:path*` }];
  },
  async headers() {
    return [{ source: "/:path*", headers: securityHeaders }];
  },
};

export default nextConfig;
