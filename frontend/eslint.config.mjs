import next from "eslint-config-next/core-web-vitals";
import prettier from "eslint-config-prettier/flat";

/** @type {import("eslint").Linter.Config[]} */
export default [
  {
    ignores: [
      ".next/**",
      "out/**",
      "coverage/**",
      "node_modules/**",
      "next-env.d.ts",
      "*.config.mjs",
      "*.config.mts",
    ],
  },
  ...next,
  prettier,
  {
    rules: {
      // Deliberate: portraits and gear thumbnails are user-supplied `data:` URIs,
      // which `next/image` cannot optimize anyway.
      "@next/next/no-img-element": "off",

      // `any` and unused-vars debt is fenced off with file-level disables
      // (blocks.tsx, the sheet helpers); keep them visible but not blocking.
      "@typescript-eslint/no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/no-explicit-any": "warn",

      // These were demoted while the codebase had violations; it's clean now,
      // so keep them blocking so regressions surface in `make check`.
      "react-hooks/exhaustive-deps": "error",
      "react-hooks/refs": "error",
      "@next/next/no-page-custom-font": "error",
      "@next/next/no-location-assign-relative-destination": "error",
    },
  },
];
