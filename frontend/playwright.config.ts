import { defineConfig, devices } from "@playwright/test";

/**
 * One browser, one worker, one flow. The unit suite (249 vitest tests) already
 * covers the logic; what it cannot cover is the seam this app is built on —
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
  fullyParallel: false,
  workers: 1,
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
      command: "../backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8100",
      cwd: "../backend",
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
