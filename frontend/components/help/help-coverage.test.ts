import { readdirSync, readFileSync, statSync } from "node:fs";
import { join, posix, resolve as resolvePath } from "node:path";
import { describe, expect, it } from "vitest";
import { JA_HELP } from "@/lib/i18n/locales/ja/help";

/**
 * What stops a new field from shipping without a tooltip.
 *
 * `HelpTip` is the only way help reaches the UI, and nothing forces a new row
 * to use it: a tab added without one simply shows no "?" and no test notices.
 * These are source-level invariants rather than render assertions on purpose —
 * a rendered tab only shows the rows its fixture character happens to have, so
 * a tip missing from a branch nobody's fixture takes would still pass.
 *
 * The frontend root, from `components/help/`.
 */
const ROOT = resolvePath(__dirname, "..", "..");

/** Every non-test source file under `dirs`, as paths relative to `ROOT`. */
function sourceFiles(dirs: string[]): string[] {
  const out: string[] = [];
  const walk = (rel: string) => {
    for (const entry of readdirSync(join(ROOT, rel), { withFileTypes: true })) {
      const child = posix.join(rel, entry.name);
      if (entry.isDirectory()) walk(child);
      else if (/\.tsx?$/.test(entry.name) && !/\.test\./.test(entry.name)) out.push(child);
    }
  };
  dirs.forEach(walk);
  return out;
}

/** The dictionaries are left out: they *define* the keys, so counting them as
 *  uses would make the usage check below pass on anything. */
const SOURCES = sourceFiles(["app", "components", "lib"]).filter(
  (f) => !f.startsWith("lib/i18n/locales/"),
);
const read = (rel: string) => readFileSync(join(ROOT, rel), "utf-8");

/** The file an import specifier names, or null for anything outside the app
 *  (`react`) and for `@/lib/…`, which holds no components. */
function importedFile(spec: string, from: string): string | null {
  const base = spec.startsWith("@/")
    ? spec.slice(2)
    : spec.startsWith(".")
      ? posix.normalize(posix.join(posix.dirname(from), spec))
      : null;
  if (base === null || !base.startsWith("components")) return null;
  for (const candidate of [base, `${base}.tsx`, `${base}.ts`, `${base}/index.tsx`]) {
    try {
      if (statSync(join(ROOT, candidate)).isFile()) return candidate;
    } catch {
      // not that spelling; try the next
    }
  }
  return null;
}

/**
 * Whether this component renders help — itself, or through a component it
 * imports. A tab is usually a thin shell over per-section components
 * (`SkillsTab` is seven of them, `BioTab` delegates to `WareRow`), so the help
 * lives a level or two down. Type-only imports do not count: they carry
 * `HelpLine`, not a tooltip.
 */
function rendersHelp(rel: string, seen = new Set<string>()): boolean {
  if (seen.has(rel)) return false;
  seen.add(rel);
  const text = read(rel);
  if (/\bHelpTip\b/.test(text)) return true;
  for (const m of text.matchAll(/^import (?!type )[^;]*?from "([^"]+)";/gm)) {
    const child = importedFile(m[1], rel);
    if (child && rendersHelp(child, seen)) return true;
  }
  return false;
}

/** A surface with no explained value on it, and why. Empty on purpose: every
 *  tab and sidebar section explains something today. An entry here is a
 *  deliberate exception, not a backlog item to be left alone. */
const WITHOUT_HELP: Record<string, string> = {};

describe("tooltip help", () => {
  const surfaces = SOURCES.filter((f) =>
    /^components\/character\/(tabs\/\w+Tab|sidebar\/Sidebar\w+)\.tsx$/.test(f),
  );

  it("found the tabs and the sidebar sections", () => {
    // the regex above is the whole subject of this file; a rename that stops
    // matching would make every assertion below vacuous
    expect(surfaces.length).toBeGreaterThanOrEqual(25);
  });

  it.each(surfaces)("%s explains its values", (surface) => {
    const reason = WITHOUT_HELP[surface];
    expect(rendersHelp(surface), reason ? `exempt: ${reason}` : "renders no HelpTip").toBe(!reason);
  });

  it("names every '?' button through help.open", () => {
    // `help.open` is "{label} の説明"; a label written by hand reads differently
    // to a screen reader for no reason, and 80 call sites all use the key.
    const offenders: string[] = [];
    for (const file of SOURCES) {
      for (const m of read(file).matchAll(/<HelpTip\b[\s\S]{0,400}?label=\{([^\n]*)/g)) {
        if (!m[1].includes('"help.open"')) offenders.push(`${file}: ${m[1].trim()}`);
      }
    }
    expect(offenders).toEqual([]);
  });

  it("uses every help string it defines", () => {
    // Unused help text is help somebody wrote for a row that has since moved
    // or lost its tip. The type system catches the other direction (a key that
    // does not exist), but only for a literal: keys built as `help.attr.${k}`
    // are matched here by their prefix.
    const literals = new Set<string>();
    const prefixes: string[] = [];
    for (const file of SOURCES) {
      const text = read(file);
      for (const m of text.matchAll(/"(help\.[A-Za-z0-9_.]+)"/g)) literals.add(m[1]);
      for (const m of text.matchAll(/`(help\.[A-Za-z0-9_.]*)\$\{/g)) prefixes.push(m[1]);
    }
    const unused = Object.keys(JA_HELP).filter(
      (key) => !literals.has(key) && !prefixes.some((p) => key.startsWith(p)),
    );
    expect(unused).toEqual([]);
  });
});
