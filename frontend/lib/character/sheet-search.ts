import type { UiFn, MsgKey } from "@/lib/i18n";
import type { Catalog, Character } from "@/lib/types";
import type { Tab, GearKind } from "./constants";
import { isDrugCategory } from "./constants";
import { qualityDisplayRows } from "./quality";
import { scopeTr } from "@/lib/ui-strings";

export type SheetSearchTarget = { key: string; tab: Tab; gearKind?: GearKind };
export type SheetSearchRequest = { target: SheetSearchTarget; characterId: string; serial: number };
export type SheetSearchEntry = {
  key: string;
  name: string;
  originalName: string;
  nickname: string;
  notes: string;
  path: string[];
  target: SheetSearchTarget;
};
type Row = Record<string, unknown>;
const rows = (value: unknown): Row[] =>
  Array.isArray(value)
    ? value.filter((r): r is Row => !!r && typeof r === "object" && !Array.isArray(r))
    : [];
const text = (value: unknown): string => (typeof value === "string" ? value : "");
export const sheetSearchKey = (bucket: string, id: string) => `${bucket}/${id}`;

const SOURCES: Array<[keyof Character, Tab, GearKind?]> = [
  ["cyberware", "cyber"],
  ["bioware", "bio"],
  ["armor", "gear", "armor"],
  ["armor_mods", "gear", "armor"],
  ["weapons", "gear", "weapon"],
  ["weapon_accessories", "gear", "weapon"],
  ["commlinks", "gear", "commlink"],
  ["cyberdecks", "gear", "cyberdeck"],
  ["rccs", "gear", "rcc"],
  ["optics", "gear", "optics"],
  ["sensors", "gear", "sensor"],
  ["vehicles", "gear", "vehicle"],
  ["drones", "gear", "drone"],
  ["gear", "gear", "misc"],
  ["programs", "gear", "cyberdeck"],
  ["apps", "gear", "commlink"],
  ["lifestyles", "gear", "lifestyle"],
  ["adept_powers", "adept"],
  ["qi_foci", "adept"],
  ["spells", "spells"],
  ["spirits", "spirits"],
  ["sprites", "sprites"],
  ["foci", "foci"],
  ["contacts", "contacts"],
  ["complex_forms", "complexforms"],
  ["ai_programs", "aiprograms"],
];
const CATALOG_ID_FIELDS = [
  "ware_id",
  "armor_id",
  "weapon_id",
  "accessory_id",
  "gear_id",
  "commlink_id",
  "lifestyle_id",
  "power_id",
  "spell_id",
  "spirit_id",
  "sprite_id",
  "focus_id",
  "form_id",
  "program_id",
  "mod_id",
];

/** Index owned state, never the catalogue's unowned shopping choices. */
export function buildSheetSearch(
  ch: Character,
  catalog: Catalog,
  tr: (name: string) => string,
  ui?: UiFn,
): SheetSearchEntry[] {
  const names = new Map<string, Row>();
  for (const row of [
    ...Object.values(catalog).flatMap(rows),
    ...(catalog.cyberware?.items ?? []),
    ...(catalog.bioware?.items ?? []),
  ]) {
    if (typeof row.id === "string") names.set(row.id, row as unknown as Row);
  }
  const entries: SheetSearchEntry[] = [];
  const byId = new Map<string, { entry: SheetSearchEntry; row: Row; bucket: string }>();
  const owned: Array<{ entry: SheetSearchEntry; row: Row; bucket: string }> = [];
  const gated: Partial<Record<Tab, string>> = {
    adept: "adept",
    spells: "spells",
    spirits: "spirits",
    sprites: "sprites",
    foci: "foci",
    complexforms: "complexforms",
    aiprograms: "advanced programs",
  };
  for (const [bucket, tab, gearKind] of SOURCES) {
    if (gated[tab] && !ch.derived.enabled_tabs.includes(gated[tab]!)) continue;
    const computedRows = rows(
      ch.derived[(bucket === "armor" ? "armor_items" : bucket) as keyof typeof ch.derived],
    );
    const derived = new Map(computedRows.map((r) => [text(r.id), r]));
    const rawRows = rows(ch[bucket]);
    const rawIds = new Set(rawRows.map((row) => text(row.id)));
    const ownedRows = [...rawRows, ...computedRows.filter((row) => !rawIds.has(text(row.id)))];
    for (const original of ownedRows) {
      const row = { ...derived.get(text(original.id)), ...original };
      const id = text(row.id);
      if (!id) continue;
      const key = sheetSearchKey(bucket, id);
      const computed = derived.get(id);
      const reference = CATALOG_ID_FIELDS.map((field) => text(row[field])).find((value) =>
        names.has(value),
      );
      const spec = reference ? names.get(reference) : undefined;
      const originalName =
        text(computed?.name) ||
        text(spec?.name) ||
        text(row.name) ||
        text(row.label) ||
        (bucket === "contacts" ? "Contact" : "");
      if (!originalName) continue;
      const translator = scopeTr(
        tr,
        bucket === "cyberware" || bucket === "bioware"
          ? "cyberware"
          : bucket === "armor" || bucket === "armor_mods"
            ? "armor"
            : tab === "gear"
              ? "gear"
              : bucket === "adept_powers"
                ? "power"
                : "contact",
      );
      const target: SheetSearchTarget = { key, tab, gearKind };
      if (
        bucket === "programs" &&
        (computed?.program_host === "rccs" ||
          text(computed?.category || spec?.category).includes("Autosoft"))
      )
        target.gearKind = "rcc";
      if (
        bucket === "gear" &&
        isDrugCategory({ category: text(computed?.category) || text(spec?.category) })
      )
        target.gearKind = "drugs";
      const entry: SheetSearchEntry = {
        key,
        name:
          tab === "gear" ||
          tab === "cyber" ||
          tab === "bio" ||
          tab === "adept" ||
          tab === "contacts"
            ? translator(originalName)
            : tr(originalName),
        originalName,
        nickname: text(row.nickname),
        notes: [row.notes, row.extra, row.role, row.hobbies_vice, row.personal_life]
          .map(text)
          .filter(Boolean)
          .join("\n"),
        path: [],
        target,
      };
      const location = [...(ch.gear_locations ?? []), ...(ch.armor_locations ?? [])].find(
        (place) => place.id === row.location,
      );
      if (location?.name) entry.path.push(location.name);
      else if (bucket === "contacts" && text(row.location)) entry.path.push(text(row.location));
      entries.push(entry);
      const ownedRow = { entry, row, bucket };
      owned.push(ownedRow);
      byId.set(id, ownedRow);
    }
  }
  // Nested items inherit the host's editor, except devices with their own setup page.
  const independent = new Set(["commlinks", "cyberdecks", "rccs", "weapons"]);
  for (const item of owned) {
    const visited = new Set([item.entry.key]);
    let parent = byId.get(text(item.row.parent_id));
    const ancestors: typeof owned = [];
    while (parent && !visited.has(parent.entry.key)) {
      visited.add(parent.entry.key);
      ancestors.unshift(parent);
      parent = byId.get(text(parent.row.parent_id));
    }
    const rootLocation = ancestors.length
      ? [...(ch.gear_locations ?? []), ...(ch.armor_locations ?? [])].find(
          (place) => place.id === ancestors[0].row.location,
        )?.name
      : undefined;
    item.entry.path = [
      ...(rootLocation ? [rootLocation] : []),
      ...ancestors.map((p) => p.entry.nickname || p.entry.name),
      ...item.entry.path,
    ];
    if (ancestors.length && !independent.has(item.bucket)) {
      const owner =
        [...ancestors].reverse().find((parent) => independent.has(parent.bucket)) ?? ancestors[0];
      const root = owner.entry.target;
      item.entry.target = { ...root, key: item.entry.key };
    }
  }
  for (const quality of qualityDisplayRows(ch.derived.qualities ?? [], catalog.qualities ?? [])) {
    const id = quality.extra_key || quality.id;
    const key = sheetSearchKey("qualities", id);
    entries.push({
      key,
      name: tr(quality.name),
      originalName: quality.name,
      nickname: "",
      notes: ch.quality_notes?.[id] ?? "",
      path: [],
      target: { key, tab: "qualities" },
    });
  }
  const skillTr = scopeTr(tr, "skill");
  for (const skill of catalog.skills?.skills ?? []) {
    if (
      Math.max(
        ch.skills[skill.name] ?? 0,
        ch.derived.skill_totals[skill.name] ?? 0,
        ch.derived.skillsoft?.[skill.name] ?? 0,
      ) <= 0
    )
      continue;
    const key = sheetSearchKey("skills", skill.name);
    entries.push({
      key,
      name: skillTr(skill.name),
      originalName: skill.name,
      nickname: "",
      notes: ch.skill_specializations?.[skill.name] ?? "",
      path: [],
      target: { key, tab: "skills" },
    });
  }
  for (const row of ch.derived.knowledge_skills ?? []) {
    const key = sheetSearchKey("knowledge_skills", row.name);
    entries.push({
      key,
      name: tr(row.name),
      originalName: row.name,
      nickname: "",
      notes: ch.skill_specializations?.[row.name] || row.spec || "",
      path: [],
      target: { key, tab: "skills" },
    });
  }
  const descriptions: Array<[keyof Character, MsgKey]> = [
    ["notes", "desc.notes"],
    ["background", "desc.background"],
    ["appearance", "desc.appearance"],
    ["game_notes", "desc.gameNotes"],
    ["concept", "desc.concept"],
    ["player_name", "desc.playerName"],
    ["age", "desc.age"],
    ["sex", "desc.sex"],
    ["height", "desc.height"],
    ["weight", "desc.weight"],
    ["eyes", "desc.eyes"],
    ["hair", "desc.hair"],
    ["skin", "desc.skin"],
  ];
  for (const [field, label] of descriptions) {
    const value = text(ch[field]);
    if (!value.trim()) continue;
    const key = sheetSearchKey("description", field);
    entries.push({
      key,
      name: ui?.(label) ?? field,
      originalName: ui?.(label) ?? field,
      nickname: "",
      notes: value,
      path: [],
      target: { key, tab: "sheet" },
    });
  }
  return entries;
}

export function searchSheet(
  entries: SheetSearchEntry[],
  query: string,
  locale: string,
): SheetSearchEntry[] {
  const normalize = (value: string) => value.normalize("NFKC").toLocaleLowerCase(locale);
  const terms = normalize(query.trim()).split(/\s+/).filter(Boolean);
  if (!terms.length) return [];
  return entries.filter((entry) => {
    const haystack = normalize(
      [entry.name, entry.originalName, entry.nickname, entry.notes, ...entry.path].join(" "),
    );
    return terms.every((term) => haystack.includes(term));
  });
}
