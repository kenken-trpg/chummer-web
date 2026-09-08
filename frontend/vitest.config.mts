import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL(".", import.meta.url)),
    },
  },
  test: {
    globals: true,
    environment: "jsdom",
    include: ["**/*.test.{ts,tsx}"],
    // `e2e/` is Playwright's (`*.spec.ts`); vitest must not try to run it
    exclude: ["node_modules", ".next", "e2e"],
    // jsdom env spin-up + the render-heavy tab tests can blow past the 5s
    // default when the machine / CI runner is under load.
    testTimeout: 15000,

    coverage: {
      provider: "v8",
      reporter: ["text-summary", "html", "lcov"],
      reportsDirectory: "coverage",
      include: ["app/**", "components/**", "lib/**"],
      exclude: [
        "**/*.test.{ts,tsx}",
        "tests/**",
        // types-only modules compile away to nothing executable
        "lib/types/**",
        "**/*.d.ts",
      ],

      // A ratchet, not a target. It sits a couple of points under where the
      // suite actually is, so an ordinary refactor that shifts a branch or two
      // does not turn CI red — what it catches is a *drop*: a feature landing
      // with no tests, or tests deleted to make a change go through.
      //
      // Raise these when the real numbers move up; never lower them to make a
      // build pass. `npm run test:coverage` prints the current figures.
      //
      // Not `perFile`: the floor is for the suite as a whole. Several files are
      // still well under it (`SheetDescEditor`, `MentorPicker`, `Toolbar`), and
      // per-file thresholds would fail today and say nothing new — the gaps are
      // already visible in the report.
      thresholds: {
        statements: 78,
        branches: 59,
        functions: 68,
        lines: 80,
      },
    },
  },
});
