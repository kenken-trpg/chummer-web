import type { Catalog, Character } from "@/lib/types";
import { makeT, type TFn } from "@/lib/ui-strings";
import { translate, type Locale, type UiFn } from "@/lib/i18n";
import { specialArmorBits } from "@/lib/character/format";

export type SheetLayout = "standard" | "compact" | "text" | "print";

type Derived = Character["derived"];
type List<K extends keyof Derived> = NonNullable<Derived[K]>;

/** Everything the sheet header + every `<*Section>` (and the text sheet) reads.
 * Computed once by {@link buildSheetData} so the section components stay pure
 * `(s: SheetData) => JSX` renderers. */
export type SheetData = {
  character: Character;
  catalog: Catalog;
  layout: SheetLayout;
  tr: (n: string) => string;
  t: TFn;
  /** Bound to `locale`, for the pure formatters that cannot call the hook. */
  ui: UiFn;
  d: Character["derived"];
  totals: Record<string, number>;
  enabled: Set<string>;
  activeSkills: {
    name: string;
    attribute: string;
    rating: number;
    pool: number;
    soft: number;
    spec?: string;
  }[];
  groups: { name: string; rating: number; bonus: number }[];
  exotic: List<"exotic_skills">;
  knowledge: List<"knowledge_skills">;
  qualities: List<"qualities">;
  weapons: List<"weapons">;
  armors: List<"armor_items">;
  cyber: List<"cyberware">;
  bio: List<"bioware">;
  gearMisc: List<"gear">;
  drugs: List<"gear">;
  sins: List<"gear">;
  gearChildren: (parentId: string) => List<"gear">;
  drugChildren: (parentId: string) => List<"gear">;
  specialArmor: { label: string; value: string }[];
};

export function buildSheetData({
  character,
  catalog,
  tr,
  layout,
  locale = "ja",
}: {
  character: Character;
  catalog: Catalog;
  tr: (n: string) => string;
  layout: SheetLayout;
  locale?: Locale;
}): SheetData {
  const d = character.derived;
  const t = makeT(catalog, locale);
  // the pure formatters take the dictionary rather than the hook
  const ui: UiFn = (key, vars) => translate(locale, key, vars);
  const totals = d.totals || {};
  const enabled = new Set(d.enabled_tabs || []);

  const activeSkills = (catalog.skills.skills || [])
    .filter((s) => s.source === "SR5" && !s.exotic && !s.name.includes("Exotic"))
    .map((s) => {
      const rating = d.skill_totals?.[s.name] || 0;
      const soft = d.skillsoft?.[s.name] || 0;
      const effective = Math.max(rating, soft);
      const attr = totals[s.attribute] || 0;
      const spec = d.skill_specializations?.[s.name];
      return {
        name: s.name,
        attribute: s.attribute,
        rating: effective,
        pool: effective + attr,
        soft: soft > rating ? soft : 0,
        spec,
      };
    })
    .filter((row) => row.rating > 0)
    .sort((a, b) => tr(a.name).localeCompare(tr(b.name), "ja"));

  const groups = (catalog.skills.groups || [])
    .map((g) => ({
      name: g,
      rating: character.skill_groups?.[g] || 0,
      bonus: d.skill_group_bonus?.[g] || 0,
    }))
    .filter((row) => row.rating > 0 || row.bonus > 0);

  const exotic = (d.exotic_skills || []).filter((row) => row.rating > 0);
  const knowledge = (d.knowledge_skills || []).filter(
    (row) => row.rating > 0 || row.native || (row.skillsoft || 0) > 0,
  );
  const qualities = d.qualities || [];
  const weapons = d.weapons || [];
  const armors = (d.armor_items || []).filter((item) => item.equipped || item.contributes);
  const cyber = (d.cyberware || []).filter((item) => !item.parent_id);
  const bio = (d.bioware || []).filter((item) => !item.parent_id);
  const isDrug = (item: { category?: string }) =>
    item.category === "Drugs" || item.category === "Toxins" || item.category === "Chemicals";
  const isSin = (item: { category?: string }) => item.category === "ID/Credsticks";
  const gearMisc = (d.gear || []).filter(
    (item) => !item.parent_id && !isDrug(item) && !isSin(item),
  );
  const drugs = (d.gear || []).filter((item) => !item.parent_id && isDrug(item));
  const sins = (d.gear || []).filter((item) => !item.parent_id && isSin(item));
  const gearChildren = (parentId: string) =>
    (d.gear || []).filter((item) => item.parent_id === parentId);
  const drugChildren = gearChildren;
  const specialArmor = specialArmorBits(d.special_armor, ui);

  return {
    character,
    catalog,
    layout,
    tr,
    t,
    ui,
    d,
    totals,
    enabled,
    activeSkills,
    groups,
    exotic,
    knowledge,
    qualities,
    weapons,
    armors,
    cyber,
    bio,
    gearMisc,
    drugs,
    sins,
    gearChildren,
    drugChildren,
    specialArmor,
  };
}
