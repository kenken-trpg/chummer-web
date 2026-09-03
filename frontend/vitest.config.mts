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

    // Measurement only — no `thresholds`. The point is to see which modules
    // the 249 tests never touch; pick a floor once the numbers are known,
    // rather than enshrining whatever today's percentage happens to be.
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
    },
  },
});
