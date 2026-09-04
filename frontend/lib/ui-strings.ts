import type { Catalog } from "@/lib/types";
import type { Locale } from "@/lib/i18n";

export type TFn = (key: string, fallback?: string) => string;

/**
 * UI-string lookup backed by the vendored Chummer lang files (ja-jp.xml,
 * en-us.xml) plus backend/data/ja_overrides/ui.json, exposed on the catalog as
 * `ui_strings` keyed by locale. Falls back to the supplied default, then the
 * key itself — so an unshipped key renders as `String_Foo`, not a crash. The
 * backend decides which keys ship; see loaders/translations.py.
 */
export function makeT(catalog?: Pick<Catalog, "ui_strings"> | null, locale: Locale = "ja"): TFn {
  const table = catalog?.ui_strings?.[locale];
  return (key, fallback) => table?.[key] || fallback || key;
}

/**
 * Catalog name -> display name. The Chummer data files are English, so the
 * translation table maps English -> Japanese and `en` is the identity: there is
 * no en-us_data.xml upstream because there is nothing to translate.
 */
export function makeTr(
  catalog?: Pick<Catalog, "translations"> | null,
  locale: Locale = "ja",
): (name: string) => string {
  if (locale === "en") return (name) => name;
  return (name) => catalog?.translations?.[name] || name;
}

/** Short attribute label, e.g. "強靱" — from String_Attribute<KEY>Short. */
export function attrShort(key: string, t: TFn): string {
  return t(`String_Attribute${key}Short`, key);
}

/** Long attribute name, e.g. "強靱力" — from String_Attribute<KEY>Long. */
export function attrName(key: string, t: TFn): string {
  return t(`String_Attribute${key}Long`, key);
}

/** Attribute label with the code prefix, e.g. "BOD 強靱力". */
export function attrLabel(key: string, t: TFn): string {
  return `${key} ${attrName(key, t)}`;
}
