import { JA, type Catalog, type MsgKey } from "./locales/ja";

export type { Catalog, MsgKey };

export type Locale = "ja" | "en";

export const LOCALES: readonly Locale[] = ["ja", "en"];

/**
 * The catalogs this browser has.
 *
 * `ja` is the reference locale: the `Catalog` type is derived from it, every
 * other locale is checked against it, and it is what the server renders and
 * the first client render shows. So it is in the first bundle and always
 * present — `MESSAGES.ja` needs no guard.
 *
 * Every other locale is fetched when something asks to be shown in it. The
 * catalogs are the largest single thing the client used to download (both of
 * them, ~83 KiB gzipped, for one UI), and nobody reads two languages at once.
 */
type Loaded = { ja: Catalog } & Partial<Record<Locale, Catalog>>;

export const MESSAGES: Loaded = { ja: JA };

/** Each non-reference locale and how to fetch it. The dynamic `import()` is
 *  what puts the catalog in its own chunk, so these stay inline rather than
 *  going through a helper. */
const LOADERS: Record<Exclude<Locale, "ja">, () => Promise<Catalog>> = {
  en: () => import("./locales/en").then((m) => m.EN),
};

const inFlight = new Map<Locale, Promise<Catalog>>();

/** Whether {@link translate} can answer in this locale right now. */
export function catalogLoaded(locale: Locale): boolean {
  return Boolean(MESSAGES[locale]);
}

/**
 * Fetch a locale's catalog, once. Resolves immediately for one already here.
 *
 * Callers are expected to re-render on resolution: until then `translate`
 * answers in `ja`, which is a fallback rather than a wrong answer, and
 * `useLocale` does not report a locale whose catalog has not arrived.
 */
export function loadLocale(locale: Locale): Promise<Catalog> {
  const have = MESSAGES[locale];
  if (have) return Promise.resolve(have);
  let pending = inFlight.get(locale);
  if (!pending) {
    pending = LOADERS[locale as Exclude<Locale, "ja">]().then((catalog) => {
      MESSAGES[locale] = catalog;
      return catalog;
    });
    inFlight.set(locale, pending);
  }
  return pending;
}

/** Substitute `{name}` placeholders; unknown placeholders are left as-is. */
export function formatMessage(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (whole, key: string) =>
    key in vars ? String(vars[key]) : whole,
  );
}

/**
 * Pure lookup, then interpolate. Every catalog is complete by construction, so
 * the key fallback below should never fire from typed code; it is there for
 * values that arrive from outside the type system — a stale locale in
 * localStorage, or a key reaching `ui()` through a cast.
 *
 * The locale fallback is load-ordering rather than a missing string: a catalog
 * still in flight reads as `ja` for that render.
 */
export function translate(
  locale: Locale,
  key: MsgKey,
  vars?: Record<string, string | number>,
): string {
  const template = (MESSAGES[locale] ?? MESSAGES.ja)[key] ?? key;
  return vars ? formatMessage(template, vars) : template;
}
