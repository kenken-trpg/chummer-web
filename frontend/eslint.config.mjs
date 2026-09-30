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
    // The app chrome used to be ~1,200 Japanese string literals sitting in the
    // components, against 60 keys in `lib/i18n` — which is why switching the
    // locale to `en` once changed almost nothing on screen. Extracting them was
    // done in batches, held to a count by a bulk-suppression file that shrank
    // as each batch landed.
    //
    // That count reached zero: the file is gone, and so are the
    // `lint:suppress` / `lint:prune` scripts that kept it. What is left is the
    // line itself, which is the part that has to stay — every *new* piece of
    // user-visible Japanese goes through `useUiText()` / `MsgKey`, and this
    // rule is what says so. A violation is now simply an error, with nothing
    // to record it in.
    //
    // The class is kana *letters* and kanji, deliberately excluding `・`
    // (U+30FB) and `ー` (U+30FC): those are punctuation that shows up alone as
    // a separator, and a real Japanese word always brings a letter with it.
    //
    // `lib/` is in scope too: it renders as much user-visible text as
    // `components/` does (the text sheet, the formatters, the small JSX bits),
    // and leaving it out is how `bits.tsx` kept two literals nobody noticed.
    //
    // The dictionaries are exempt: `lib/i18n/locales/**` *are* the text — the
    // barrels and the per-area files they spread together alike. The
    // Cocofolia export used to be exempt as well; it now takes a locale and
    // reads its labels out of the dictionary like everything else.
    files: [
      "app/**/*.tsx",
      "app/**/*.ts",
      "components/**/*.tsx",
      "components/**/*.ts",
      "lib/**/*.tsx",
      "lib/**/*.ts",
    ],
    ignores: ["**/*.test.ts", "**/*.test.tsx", "lib/i18n/locales/**/*.ts"],
    rules: {
      "no-restricted-syntax": [
        "error",
        {
          selector: "JSXText[value=/[\\u3041-\\u3096\\u30a1-\\u30fa\\u4e00-\\u9fff]/]",
          message:
            "Japanese text in JSX. Add a key to lib/i18n/locales/ja.ts (and en.ts) and render it with ui(). See docs/i18n.md.",
        },
        {
          selector: "JSXAttribute Literal[value=/[\\u3041-\\u3096\\u30a1-\\u30fa\\u4e00-\\u9fff]/]",
          message:
            "Japanese in a JSX attribute (title / aria-label / placeholder). Use ui() — a label a screen reader announces is UI text like any other.",
        },
        {
          selector:
            "TemplateElement[value.cooked=/[\\u3041-\\u3096\\u30a1-\\u30fa\\u4e00-\\u9fff]/]",
          message:
            "Japanese in a template literal. Use ui() with a {placeholder} — see formatMessage in lib/i18n.",
        },
        {
          selector:
            ":matches(VariableDeclarator, Property, ReturnStatement, ArrowFunctionExpression, ConditionalExpression) > Literal[value=/[\\u3041-\\u3096\\u30a1-\\u30fa\\u4e00-\\u9fff]/]",
          message:
            "Japanese string literal. Add a key to lib/i18n/locales/ja.ts (and en.ts) and render it with ui().",
        },
      ],
    },
  },
];
