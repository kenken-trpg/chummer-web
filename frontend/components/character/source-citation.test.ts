import { readdirSync, readFileSync } from "node:fs";
import { join, posix, resolve as resolvePath } from "node:path";
import { describe, expect, it } from "vitest";

/**
 * What keeps a rulebook citation complete.
 *
 * `sourceBit` is how a book and its page reach the UI. Nothing forces a new
 * row to call it: interpolating `item.source` on its own compiles, renders,
 * and silently drops the page number — which is how the citations drifted
 * into "SR5" with no page at most of their fifty-odd call sites. So this is a
 * source-level check rather than a render assertion: a row only shows up in a
 * rendered tab when some fixture character happens to have that item, and the
 * sites that lost their page were exactly the rarely-exercised ones.
 */
const ROOT = resolvePath(__dirname, "..", "..");

function sourceFiles(dir: string): string[] {
  const out: string[] = [];
  const walk = (rel: string) => {
    for (const entry of readdirSync(join(ROOT, rel), { withFileTypes: true })) {
      const child = posix.join(rel, entry.name);
      if (entry.isDirectory()) walk(child);
      else if (entry.name.endsWith(".tsx") && !entry.name.includes(".test.")) out.push(child);
    }
  };
  walk(dir);
  return out;
}

/** A `.source` that is not a book, and why. These are interpolated the plain
 *  way on purpose; everything else must go through `sourceBit`. */
const NOT_A_BOOK: Record<string, string> = {
  "components/character/SettingsPicker.tsx": "a skipped settings key, not a rulebook",
};

/** `{item.source}` or `${item.source}` — the spelling that drops the page. */
const BARE = /(\{|\$\{)\s*[A-Za-z_][A-Za-z0-9_.]*\.source\s*\}/;

describe("rulebook citations", () => {
  const files = sourceFiles("components");

  it("found the components", () => {
    // the walk above is this file's whole subject; a move that empties it
    // would make the assertion below vacuous
    expect(files.length).toBeGreaterThanOrEqual(50);
  });

  it("renders no book name without its page", () => {
    const offenders = files.filter((f) => BARE.test(readFileSync(join(ROOT, f), "utf-8")));
    expect(offenders).toEqual(Object.keys(NOT_A_BOOK).filter((f) => files.includes(f)));
  });
});
