import type { NextConfig } from "next";

// The browser calls the API at a relative /api/*; Next proxies it to the
// FastAPI backend. Override the target for a split deploy (frontend and
// backend on different hosts) with BACKEND_ORIGIN.
const BACKEND_ORIGIN = process.env.BACKEND_ORIGIN ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // self-contained server bundle for the container (`node server.js`)
  output: "standalone",
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${BACKEND_ORIGIN}/api/:path*` }];
  },
};

export default nextConfig;
