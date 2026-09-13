import { EN } from "./locales/en";
import { JA, type Catalog, type MsgKey } from "./locales/ja";

export type { MsgKey };

export type Locale = "ja" | "en";

export const LOCALES: readonly Locale[] = ["ja", "en"];

export const MESSAGES: Record<Locale, Catalog> = {
  ja: JA,
  en: EN,
};

/** Substitute `{name}` placeholders; unknown placeholders are left as-is. */
export function formatMessage(template: string, vars: Record<string, string | number>): string {
  return template.replace(/\{(\w+)\}/g, (whole, key: string) =>
    key in vars ? String(vars[key]) : whole,
  );
}

/**
 * Pure lookup, then interpolate. Every catalog is complete by construction, so
 * neither fallback below should ever fire from typed code; they are there for
 * values that arrive from outside the type system — a stale locale in
 * localStorage, or a key reaching `ui()` through a cast.
 */
export function translate(
  locale: Locale,
  key: MsgKey,
  vars?: Record<string, string | number>,
): string {
  const template = (MESSAGES[locale] ?? MESSAGES.ja)[key] ?? key;
  return vars ? formatMessage(template, vars) : template;
}
