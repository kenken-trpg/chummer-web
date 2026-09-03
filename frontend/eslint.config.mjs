import next from "eslint-config-next/core-web-vitals";
import prettier from "eslint-config-prettier/flat";
import jsxA11y from "eslint-plugin-jsx-a11y";

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
  // `eslint-config-next` registers the jsx-a11y plugin but turns on only a
  // handful of its rules; the rest of the recommended set is what catches an
  // unlabelled control. Take the rules only — re-registering the plugin is a
  // config error.
  { rules: jsxA11y.flatConfigs.recommended.rules },
  prettier,
  {
    rules: {
      // Deliberate: portraits and gear thumbnails are user-supplied `data:` URIs,
      // which `next/image` cannot optimize anyway.
      "@next/next/no-img-element": "off",

      // Source is `any`-free (the last two holdouts, blocks.tsx and
      // text-sheet.ts, now use the derived-payload types); keep it that way.
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],

      // These were demoted while the codebase had violations; it's clean now,
      // so keep them blocking so regressions surface in `make check`.
      "react-hooks/exhaustive-deps": "error",
      "react-hooks/refs": "error",
      "@next/next/no-page-custom-font": "error",
      "@next/next/no-location-assign-relative-destination": "error",
    },
  },
  {
    // Tests still cast fixtures with `as any`; not worth the churn.
    files: ["**/*.test.ts", "**/*.test.tsx", "tests/**"],
    rules: { "@typescript-eslint/no-explicit-any": "warn" },
  },
];
