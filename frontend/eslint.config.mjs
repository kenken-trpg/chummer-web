import next from "eslint-config-next/core-web-vitals";
import prettier from "eslint-config-prettier/flat";

/** @type {import("eslint").Linter.Config[]} */
export default [
  {
    ignores: [".next/**", "out/**", "node_modules/**", "next-env.d.ts", "*.config.mjs"],
  },
  ...next,
  prettier,
  {
    rules: {
      // Deliberate: portraits and gear thumbnails are user-supplied `data:` URIs,
      // which `next/image` cannot optimize anyway.
      "@next/next/no-img-element": "off",

      // Pre-existing debt we want visible but not blocking. Driving these to
      // zero is a good first contribution — see CONTRIBUTING.md.
      "@typescript-eslint/no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/no-explicit-any": "warn",
      "react-hooks/exhaustive-deps": "warn",
      "react-hooks/refs": "warn",
      "@next/next/no-page-custom-font": "warn",
      "@next/next/no-location-assign-relative-destination": "warn",
    },
  },
];
