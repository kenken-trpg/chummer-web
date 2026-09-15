import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { EN } from "./locales/en";
import { JA } from "./locales/ja";

const HERE = join(__dirname, "locales");

/** Every `"key":` at the top level of one of a locale's part files. */
function keysByFile(locale: "ja" | "en"): Map<string, string[]> {
  const dir = join(HERE, locale);
  const out = new Map<string, string[]>();
  for (const name of readdirSync(dir).filter((f) => f.endsWith(".ts"))) {
    const text = readFileSync(join(dir, name), "utf-8");
    out.set(
      name,
      [...text.matchAll(/^ {2}"([^"]+)":/gm)].map((m) => m[1]),
    );
  }
  return out;
}

describe.each(["ja", "en"] as const)("the %s dictionary", (locale) => {
  /**
   * `ja.ts` / `en.ts` spread their part files into one object, and a spread
   * has no duplicate-key error: a key defined in two files would silently
   * take whichever value came last, with nothing to see in a diff. Inside
   * one file TypeScript catches it (TS1117), so this is the only gap.
   */
  it("defines every key in exactly one file", () => {
    const seen = new Map<string, string>();
    const clashes: string[] = [];
    for (const [file, keys] of keysByFile(locale)) {
      for (const key of keys) {
        const first = seen.get(key);
        if (first) clashes.push(`${key}: ${first} and ${file}`);
        else seen.set(key, file);
      }
    }
    expect(clashes).toEqual([]);
  });

  it("loses nothing on the way into the spread", () => {
    const declared = new Set([...keysByFile(locale).values()].flat());
    const built = new Set(Object.keys(locale === "ja" ? JA : EN));
    expect([...declared].filter((k) => !built.has(k))).toEqual([]);
    expect([...built].filter((k) => !declared.has(k))).toEqual([]);
  });
});
