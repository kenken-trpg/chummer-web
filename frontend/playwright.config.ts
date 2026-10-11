import { existsSync } from "node:fs";
import { defineConfig, devices } from "@playwright/test";

// A virtualenv puts its entry points in `bin/` on POSIX and in `Scripts/` on
// Windows. The `Makefile` and `scripts/*.sh` work this out too; this config is
// spawned by playwright rather than by them, so it has to do it itself.
const UVICORN = existsSync("../backend/.venv/Scripts/uvicorn.exe")
  ? "../backend/.venv/Scripts/uvicorn"
  : "../backend/.venv/bin/uvicorn";

/**
 * One browser, only what the unit suite cannot reach. The vitest suite covers
 * the logic; what it cannot cover is the seam this app is built on —
 * the character lives in IndexedDB in the browser and the rules engine lives in
 * a Python process, and nothing but a real browser exercises both at once.
 *
 * `webServer` starts both halves. The backend needs `backend/vendor` (see
 * `make data`); without it `/api/catalog` 503s and the app never loads.
 */
export default defineConfig({
  testDir: "./e2e",
  // a real browser round-tripping through uvicorn is slower than jsdom
  timeout: 60_000,
  expect: { timeout: 10_000 },
  // Every test gets its own browser context, so its own IndexedDB and
  // localStorage: nothing is shared, and the servers are started once for all
  // workers. CI runners have 4 cores; the build is the slow part, not this.
  // The workers do share 127.0.0.1, so they share the backend's per-IP import
  // limit; `webServer` below raises it for this run rather than capping how
  // many tests may touch an import route.
  fullyParallel: true,
  workers: process.env.CI ? 4 : undefined,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? "github" : "list",

  use: {
    baseURL: "http://127.0.0.1:3100",
    trace: "retain-on-failure",
    // a failed E2E is usually a layout/state question, not a stack trace
    screenshot: "only-on-failure",
  },

  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],

  webServer: [
    {
      command: `${UVICORN} app.main:app --host 127.0.0.1 --port 8100`,
      cwd: "../backend",
      // `IMPORT_RATE_LIMIT` defaults to 20/minute per client IP, which exists
      // to bound what one caller can aim at the XML-handling routes. All four
      // workers look like one caller here, and `/share` previews go through
      // `/api/characters/import` too, so the suite as a whole can outrun it in
      // a single minute — and the test that gets the 429 is whichever one
      // happened to be running, not the one that used the budget. The limit's
      // own value is asserted in `backend/tests/test_api.py`, and production
      // sets it in the Worker (`deploy/cloudflare/src/index.ts`), so raising
      // it for a trusted single-client run costs no coverage.
      env: { IMPORT_RATE_LIMIT: "200/minute" },
      url: "http://127.0.0.1:8100/api/health",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      // `next build && next start`, not `next dev`: the dev server's on-demand
      // compilation makes the first navigation of each route take tens of
      // seconds, which reads as a flaky timeout rather than a slow build.
      //
      // Next prints "next start does not work with output: standalone" and then
      // serves the build anyway, rewrites included. The container runs the
      // standalone `server.js` (see Dockerfile); replicating that here means
      // hand-copying `.next/static`, which is more setup than this buys.
      command: "npm run build && npm run start -- --port 3100",
      cwd: ".",
      url: "http://127.0.0.1:3100",
      // ports off the dev defaults (8000/3000) so a `make dev` already running
      // is not what the test ends up driving
      env: { BACKEND_ORIGIN: "http://127.0.0.1:8100" },
      reuseExistingServer: !process.env.CI,
      timeout: 180_000,
    },
  ],
});
