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
    // --- i18n: stop the leak, then drain it ------------------------------
    //
    // The app chrome is written as Japanese string literals in the components
    // (~1,200 of them), while `lib/i18n` holds 60 keys. That is why switching
    // the locale to `en` changes almost nothing on screen.
    //
    // Extracting all of it at once is not worth a single commit, so this rule
    // draws the line instead: every *new* piece of user-visible Japanese has
    // to go through `useUiText()` / `MsgKey`. The ~1,200 that are already here
    // are recorded in `eslint-suppressions.json` (`npm run lint:suppress`), so
    // they do not fail the build — and `npm run lint:prune` shrinks that file
    // as each batch is extracted, which makes it the burn-down counter.
    //
    // Scoped to `app/` and `components/` — the layers the user reads. `lib/`
    // holds Japanese *data* maps (game-term labels, cocofolia palettes) that
    // are a separate question, and `lib/i18n/messages.ts` is the catalog
    // itself. See docs/i18n.md.
    files: ["app/**/*.tsx", "app/**/*.ts", "components/**/*.tsx", "components/**/*.ts"],
    ignores: ["**/*.test.ts", "**/*.test.tsx"],
    rules: {
      "no-restricted-syntax": [
        "error",
        {
          selector: "JSXText[value=/[\\u3040-\\u30ff\\u4e00-\\u9fff]/]",
          message:
            "Japanese text in JSX. Add a key to lib/i18n/messages.ts and render it with ui(). See docs/i18n.md.",
        },
        {
          selector: "JSXAttribute Literal[value=/[\\u3040-\\u30ff\\u4e00-\\u9fff]/]",
          message:
            "Japanese in a JSX attribute (title / aria-label / placeholder). Use ui() — a label a screen reader announces is UI text like any other.",
        },
        {
          selector: "TemplateElement[value.cooked=/[\\u3040-\\u30ff\\u4e00-\\u9fff]/]",
          message:
            "Japanese in a template literal. Use ui() with a {placeholder} — see formatMessage in lib/i18n.",
        },
        {
          selector:
            ":matches(VariableDeclarator, Property, ReturnStatement, ArrowFunctionExpression, ConditionalExpression) > Literal[value=/[\\u3040-\\u30ff\\u4e00-\\u9fff]/]",
          message:
            "Japanese string literal. Add a key to lib/i18n/messages.ts and render it with ui().",
        },
      ],
    },
  },
  {
    // Tests still cast fixtures with `as any`; not worth the churn.
    files: ["**/*.test.ts", "**/*.test.tsx", "tests/**"],
    rules: { "@typescript-eslint/no-explicit-any": "warn" },
  },
];
