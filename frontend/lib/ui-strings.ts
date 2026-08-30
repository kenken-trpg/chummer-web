import type { Catalog } from "@/lib/types";

export type TFn = (key: string, fallback?: string) => string;

/**
 * UI-string lookup backed by ja-jp.xml + backend/data/ja_overrides/ui.json
 * (exposed on the catalog as `ui_strings`). Falls back to the supplied default,
 * then the key itself.
 */
export function makeT(catalog?: Pick<Catalog, "ui_strings"> | null): TFn {
  return (key, fallback) => catalog?.ui_strings?.[key] || fallback || key;
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
