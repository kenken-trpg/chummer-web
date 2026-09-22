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

/** The kinds `translations_by_kind` is keyed by. */
export type TranslationKind =
  "armor" | "critter_power" | "cyberware" | "gear" | "knowledge_skill" | "power" | "skill";

/** A name translator. `makeTr`'s carries the per-kind tables so a screen can
 *  narrow it with `scopeTr`; a plain function (a test's identity) has none. */
export type TrFn = ((name: string) => string) & {
  byKind?: Partial<Record<string, Record<string, string>>>;
  base?: (name: string) => string;
  kinds?: readonly TranslationKind[];
};

/**
 * Catalog name -> display name. The Chummer data files are English, so the
 * translation table maps English -> Japanese and `en` is the identity: there is
 * no en-us_data.xml upstream because there is nothing to translate.
 */
export function makeTr(
  catalog?: Pick<Catalog, "translations" | "translations_by_kind"> | null,
  locale: Locale = "ja",
): TrFn {
  if (locale === "en") return (name) => name;
  const tr: TrFn = (name) => catalog?.translations?.[name] || name;
  tr.byKind = catalog?.translations_by_kind;
  return tr;
}

/**
 * `tr` for a screen that shows one kind of thing. The flat table is keyed by
 * English name alone, so "Binding" reads as the critter power's 接着 even on
 * the skills tab; the per-kind table corrects the handful of names where that
 * lands on a different thing. Only those names are listed, so scoping a whole
 * tab is safe — anything else falls through to the flat table.
 *
 * Kinds are tried in order, and a nested scope's kinds before its parent's.
 */
export function scopeTr(tr: TrFn, ...kinds: TranslationKind[]): TrFn {
  const byKind = tr.byKind;
  if (!byKind) return tr;
  const base = tr.base || tr;
  const all = [...kinds, ...(tr.kinds || [])];
  const scoped: TrFn = (name) => {
    for (const kind of all) {
      const hit = byKind[kind]?.[name];
      if (hit) return hit;
    }
    return base(name);
  };
  scoped.byKind = byKind;
  scoped.base = base;
  scoped.kinds = all;
  return scoped;
}

/**
 * `name` translated as `kind` alone, ignoring the scope `tr` carries. A gear
 * pick is a skill's name, not gear: under the gear tab's scope Knowsoft
 * (History) took the gear History's English. `kind` "" (or absent) means the
 * flat table — a tradition, a weapon, a list that mixes both skill kinds.
 */
export function trAs(tr: TrFn, kind: TranslationKind | "" | undefined, name: string): string {
  if (!tr.byKind) return tr(name);
  const base = tr.base || tr;
  return (kind && tr.byKind[kind]?.[name]) || base(name);
}

/**
 * Skill-group name -> display name. Backed by `skills.group_names`, not the
 * flat `translations` table: there, "Influence" and "Stealth" are also spells
 * and "Firearms" and "Engineering" are also knowledge skills, so the group
 * rendered with the other entity's reading (the Influence group showed the
 * spell's 感化 instead of 対人) or was left untranslated entirely. Falls back
 * to `tr` and then the English name, so an unmapped group still renders.
 */
export function makeTrSkillGroup(
  catalog?: Pick<Catalog, "skills" | "translations"> | null,
  locale: Locale = "ja",
): (group: string) => string {
  if (locale === "en") return (group) => group;
  const groupNames = catalog?.skills?.group_names;
  const tr = makeTr(catalog, locale);
  return (group) => groupNames?.[group] || tr(group);
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
