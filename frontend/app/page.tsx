"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "@/lib/api";
import type { Catalog, Character, InstalledAdeptPower, InstalledWare, LimitModifier, MagicTestInfo, MentorInfo, PriorityCategory, PriorityLetter, QualityReqNode, SkillPickSlot, SpecialArmor, WareCatalogItem, WareInstall } from "@/lib/types";

const CATS: { key: PriorityCategory; label: string }[] = [
  { key: "Heritage", label: "メタタイプ" },
  { key: "Attributes", label: "属性" },
  { key: "Talent", label: "魔法/レゾナンス" },
  { key: "Skills", label: "スキル" },
  { key: "Resources", label: "資金" },
];
const LETTERS: PriorityLetter[] = ["A", "B", "C", "D", "E"];
const SUM_TO_TEN_COST: Record<PriorityLetter, number> = { A: 4, B: 3, C: 2, D: 1, E: 0 };
const DEFAULT_PRIORITIES: Record<PriorityCategory, PriorityLetter> = {
  Heritage: "C",
  Attributes: "A",
  Talent: "E",
  Skills: "B",
  Resources: "D",
};
const ATTRS = ["BOD", "AGI", "REA", "STR", "WIL", "LOG", "INT", "CHA", "EDG", "MAG", "RES"] as const;
const ATTR_JA: Record<string, string> = {
  BOD: "BOD 体",
  AGI: "AGI 敏",
  REA: "REA 反",
  STR: "STR 力",
  WIL: "WIL 意",
  LOG: "LOG 論",
  INT: "INT 直",
  CHA: "CHA 魅",
  EDG: "EDG 縁",
  MAG: "MAG 魔力",
  RES: "RES 共振力",
};
const KNOW_CATS = ["Academic", "Interest", "Language", "Professional", "Street"] as const;
const KNOW_CAT_JA: Record<string, string> = {
  Academic: "学術",
  Interest: "趣味",
  Language: "言語",
  Professional: "職業",
  Street: "街",
};

const CONTACT_ROLES = ["Fixer", "Street Doc", "Talismonger", "Mechanic", "Fence", "Mr. Johnson", "Bartender", "Cop", "Deckmeister"];
const MATRIX_ATTRS = [
  ["attack", "ATK"],
  ["sleaze", "SLZ"],
  ["dataprocessing", "DP"],
  ["firewall", "FW"],
] as const;
const DEFAULT_ARRAY_ORDER = ["attack", "sleaze", "dataprocessing", "firewall"];

function swapMatrixOrder(order: string[] | undefined, fromKey: string, toPos: number): string[] {
  const next = [...(order && order.length === 4 ? order : DEFAULT_ARRAY_ORDER)];
  const fromPos = next.indexOf(fromKey);
  if (fromPos < 0 || toPos < 0 || toPos >= next.length || fromPos === toPos) return next;
  [next[fromPos], next[toPos]] = [next[toPos], next[fromPos]];
  return next;
}

function vehicleFits(
  cons: {
    names?: string[];
    category_contains?: string[];
    category_equals?: string[];
    body_lte?: number | null;
    body_gte?: number | null;
  } | undefined,
  vehicle: { name: string; category?: string; body?: string },
) {
  if (!cons) return true;
  const names = cons.names || [];
  const contains = cons.category_contains || [];
  const equals = cons.category_equals || [];
  if (!names.length && !contains.length && !equals.length && cons.body_lte == null && cons.body_gte == null) return true;
  if (names.length && !names.includes(vehicle.name)) return false;
  const category = vehicle.category || "";
  if (contains.length && !contains.some((part) => category.includes(part))) return false;
  if (equals.length && !equals.includes(category)) return false;
  const body = Number(String(vehicle.body || "0").split("/")[0]) || 0;
  if (cons.body_lte != null && body > cons.body_lte) return false;
  if (cons.body_gte != null && body < cons.body_gte) return false;
  return true;
}

function vehicleForbidden(
  cons: {
    names?: string[];
    category_contains?: string[];
    category_equals?: string[];
    body_lte?: number | null;
    body_gte?: number | null;
  } | undefined,
  vehicle: { name: string; category?: string; body?: string },
) {
  if (!cons) return false;
  const has = Boolean(
    (cons.names || []).length
    || (cons.category_contains || []).length
    || (cons.category_equals || []).length
    || cons.body_lte != null
    || cons.body_gte != null,
  );
  return has && vehicleFits(cons, vehicle);
}

function dropDrone(ch: {
  drones?: { id?: string }[];
  vehicles?: { id?: string }[];
  vehicle_mods?: { id?: string; parent_id?: string | null }[];
  weapon_mounts?: { parent_id?: string | null; weapon_install_id?: string | null }[];
  sensors?: { id?: string; parent_id?: string | null }[];
  gear?: { id?: string; parent_id?: string | null }[];
  cyberware?: WareInstall[];
}, id: string, listKey: "drones" | "vehicles" = "drones") {
  let sensors = ch.sensors || [];
  const roots = sensors.filter((row) => row.parent_id === id && row.id).map((row) => row.id as string);
  for (const sid of roots) sensors = dropTree(sensors, sid);
  sensors = sensors.filter((row) => row.parent_id !== id);
  const removedModIds = (ch.vehicle_mods || [])
    .filter((row) => row.parent_id === id && row.id)
    .map((row) => row.id as string);
  let cyberware = ch.cyberware || [];
  for (const mid of removedModIds) cyberware = removeWareTree(cyberware, mid);
  return {
    drones: listKey === "drones" ? (ch.drones || []).filter((row) => row.id !== id) : ch.drones,
    vehicles: listKey === "vehicles" ? (ch.vehicles || []).filter((row) => row.id !== id) : ch.vehicles,
    vehicle_mods: (ch.vehicle_mods || []).filter((row) => row.parent_id !== id),
    weapon_mounts: (ch.weapon_mounts || []).filter((row) => row.parent_id !== id),
    sensors,
    gear: dropTree(ch.gear || [], id),
    cyberware,
  };
}

function dropTree<T extends { id?: string; parent_id?: string | null }>(rows: T[], id: string): T[] {
  const drop = new Set<string>([id]);
  let grew = true;
  while (grew) {
    grew = false;
    for (const row of rows) {
      if (row.parent_id && drop.has(row.parent_id) && row.id && !drop.has(row.id)) {
        drop.add(row.id);
        grew = true;
      }
    }
  }
  return rows.filter((row) => !row.id || !drop.has(row.id));
}

function vehicleInteriorFits(
  mod: { category: string; required_categories?: string[] },
) {
  if (VEHICLE_INTERIOR_CATS.has(mod.category)) return true;
  return (mod.required_categories || []).some((cat) => cat && cat !== "Custom" && cat === "Commlinks");
}

function miscFits(
  parent: { name: string; category: string; addoncategories?: string[] },
  child: { category: string; requireparent?: boolean; required_names?: string[]; required_categories?: string[] },
) {
  const allowed = (parent.addoncategories || []).filter((c) => c && c !== "Custom");
  const reqNames = child.required_names || [];
  const reqCats = (child.required_categories || []).filter((c) => c !== "Custom");
  if (reqNames.length || reqCats.length) {
    return reqNames.includes(parent.name) || reqCats.includes(parent.category);
  }
  if (allowed.length) return allowed.includes(child.category);
  if (child.requireparent) return child.category === parent.category;
  return false;
}

function wareFitsVehicleMod(
  ware: WareCatalogItem,
  mod: { name: string; subsystems?: string[] },
) {
  const slots = mod.subsystems || [];
  if (!slots.includes(ware.category)) return false;
  if (!(ware.plugin || ware.requireparent)) return false;
  const names = ware.required_parent_names || [];
  if (!names.length) return true;
  return names.some((name) => mod.name.includes(name));
}

type Tab = "priority" | "meta" | "attrs" | "skills" | "qualities" | "cyber" | "bio" | "gear" | "contacts" | "martial" | "initiation" | "submersion" | "adept" | "spells" | "spirits" | "foci" | "complexforms" | "sprites";
type GearKind = "armor" | "weapon" | "commlink" | "cyberdeck" | "rcc" | "optics" | "sensor" | "drone" | "vehicle" | "misc" | "lifestyle";
const OPTICS_DEVICE_CATS = new Set(["Vision Devices", "Audio Devices"]);
const SENSOR_DEVICE_CATS = new Set(["Sensors", "Sensor Housings"]);
const VEHICLE_INTERIOR_CATS = new Set([
  "Commlink Accessories",
  "Electronics Accessories",
  "Communications and Countermeasures",
]);
const R5_SLOT_LABELS: Record<string, string> = {
  Powertrain: "パワートレイン",
  Protection: "防護",
  Weapons: "武器",
  Body: "ボディ",
  Electromagnetic: "電磁",
  Cosmetic: "外装",
};

const CORE_LIFESTYLES = new Set(["Street", "Squatter", "Low", "Medium", "High", "Luxury"]);

const SPIRIT_ROLE_JA: Record<string, string> = {
  combat: "戦闘",
  detection: "探知",
  health: "健康",
  illusion: "幻影",
  manipulation: "操作",
};

function formatPoints(value: number) {
  const rounded = Math.round(value * 100) / 100;
  return String(rounded);
}

function kindLabel(kind?: string) {
  if (kind === "ritual") return "儀式";
  if (kind === "enchantment") return "エンチャント";
  return "呪文";
}

function optionalNumber(value: string): number | null {
  if (value === "") return null;
  const n = Number(value);
  return Number.isFinite(n) ? n : null;
}

function testLine(test?: MagicTestInfo | null, drainLabel = "ドレイン") {
  if (!test) return "";
  const drain = test.drain == null ? `2×相手ヒット（最低2）` : `${test.drain}${test.drain_code || ""}`;
  const net = test.net == null ? "" : ` ・ 正味 ${test.net}`;
  const miss = test.missing ? " ・ 技能なし" : "";
  const days = test.days ? ` ・ ${test.days}日` : "";
  const vs = test.vs ? ` vs ${test.vs}` : "";
  return `${test.skill} ${test.pool} [${test.limit}]${vs} → ${drainLabel} ${drain}${net}${days}${miss}`;
}

function cfDuration(value?: string) {
  if (value === "P") return "永続";
  if (value === "S") return "維持";
  if (value === "I") return "瞬間";
  if (value === "E") return "永続";
  return value || "";
}

function lifeIncrement(inc?: string) {
  return inc === "day" ? "日" : "ヶ月";
}

function formatAccessoryCost(cost: string, parentCost?: string) {
  const raw = String(cost || "0").trim();
  const parent = Number(parentCost || 0);
  if (raw === "Weapon Cost" || raw === "Armor Cost") {
    return `${parent.toLocaleString()}¥`;
  }
  const numeric = Number(raw);
  if (Number.isFinite(numeric)) return `${numeric.toLocaleString()}¥`;
  return `${raw}¥`;
}

function formatAmmoCost(cost: string, costfor?: number) {
  const numeric = Number(cost);
  const yen = Number.isFinite(numeric) ? `${numeric.toLocaleString()}¥` : `${cost}¥`;
  if (costfor && costfor > 1) return `${yen} / ${costfor}発`;
  return yen;
}

function weaponDetailsMatch(
  weapon: { name: string; ammo?: string },
  expr: string,
) {
  const ammo = weapon.ammo || "";
  const name = weapon.name || "";
  let text = expr;
  text = text.replace(/contains\(\s*ammo\s*,\s*'([^']*)'\s*\)/g, (_, needle: string) => (ammo.includes(needle) ? "true" : "false"));
  text = text.replace(/contains\(\s*ammo\s*,\s*"([^"]*)"\s*\)/g, (_, needle: string) => (ammo.includes(needle) ? "true" : "false"));
  text = text.replace(/name\s*!=\s*'([^']*)'/g, (_, value: string) => (name !== value ? "true" : "false"));
  text = text.replace(/name\s*=\s*'([^']*)'/g, (_, value: string) => (name === value ? "true" : "false"));
  if (!/^(true|false|and|or|\(|\)|\s)+$/i.test(text)) return false;
  try {
    return Function(`"use strict"; return (${text.replace(/\band\b/g, "&&").replace(/\bor\b/g, "||")});`)();
  } catch {
    return false;
  }
}

function ammoFits(
  ammo: { category?: string; ammo_weapon_types?: string[]; weapon_details?: string },
  weapon: { name: string; ammo?: string; weapon_type?: string },
) {
  if (ammo.category !== "Ammunition") return false;
  if (ammo.weapon_details) return weaponDetailsMatch(weapon, ammo.weapon_details);
  const types = ammo.ammo_weapon_types || [];
  if (!types.length) return false;
  return types.includes(weapon.weapon_type || "");
}

function weaponLine(item: { type?: string; accuracy?: string; damage?: string; ap?: string; mode?: string; ammo?: string; reach?: string; rc?: string }) {
  const bits: string[] = [];
  if (item.type) bits.push(item.type === "Melee" ? "近接" : "遠隔");
  if (item.accuracy && item.accuracy !== "0") bits.push(`Acc ${item.accuracy}`);
  if (item.damage) bits.push(item.damage);
  if (item.ap && item.ap !== "-" && item.ap !== "0") bits.push(`AP ${item.ap}`);
  if (item.rc && item.rc !== "0") bits.push(`RC ${item.rc}`);
  if (item.mode && item.mode !== "0") bits.push(item.mode);
  if (item.ammo && item.ammo !== "0") bits.push(item.ammo);
  if (item.reach && item.reach !== "0") bits.push(`Reach ${item.reach}`);
  return bits.join(" / ");
}

function specialArmorBits(sa?: SpecialArmor | null): { label: string; value: string }[] {
  if (!sa) return [];
  const rows: { label: string; value: string }[] = [];
  if (sa.fire) rows.push({ label: "耐火", value: `+${sa.fire}` });
  if (sa.cold) rows.push({ label: "断熱", value: `+${sa.cold}` });
  if (sa.electricity) rows.push({ label: "絶縁", value: `+${sa.electricity}` });
  if (sa.radiation) rows.push({ label: "放射線", value: `+${sa.radiation}` });
  const toxin = sa.toxin_contact || 0;
  const pathogen = sa.pathogen_contact || 0;
  if (toxin && toxin === pathogen) rows.push({ label: "化学防護", value: `+${toxin}` });
  else {
    if (toxin) rows.push({ label: "毒素接触", value: `+${toxin}` });
    if (pathogen) rows.push({ label: "病原接触", value: `+${pathogen}` });
  }
  const immunities = sa.immunities || {};
  const contact = Boolean(immunities.toxin_contact && immunities.pathogen_contact);
  const inhale = Boolean(immunities.toxin_inhalation && immunities.pathogen_inhalation);
  if (contact && inhale) rows.push({ label: "化学密閉", value: "免疫" });
  else {
    if (contact) rows.push({ label: "接触免疫", value: "免疫" });
    if (inhale) rows.push({ label: "吸入免疫", value: "免疫" });
  }
  return rows;
}

function specialArmorLine(sa?: SpecialArmor | null): string {
  return specialArmorBits(sa)
    .map((row) => (row.value === "免疫" ? row.label : `${row.label} ${row.value}`))
    .join(" / ");
}

function limitModifierLine(mods?: LimitModifier[] | null): string {
  if (!mods?.length) return "";
  const names: Record<string, string> = { physical: "物理", mental: "精神", social: "社会" };
  return mods.map((mod) => {
    const sign = mod.value > 0 ? `+${mod.value}` : `${mod.value}`;
    const base = `${names[mod.limit] || mod.limit}リミット ${sign}`;
    return mod.condition_label ? `${base}（${mod.condition_label}）` : base;
  }).join(" / ");
}

function deviceRatingBit(item?: { device_rating?: number } | null): string {
  if (!item || !(item.device_rating || 0)) return "";
  return ` / DR ${item.device_rating}`;
}

function wareAttrLine(bonus?: Record<string, number> | null): string {
  return ATTRS
    .filter((key) => (bonus?.[key] || 0) !== 0)
    .map((key) => `${key} +${bonus![key]}`)
    .join(" / ");
}

function availBit(item?: { avail?: string; avail_value?: number } | null): string {
  if (!item) return "";
  if ((item.avail_value || 0) <= 0 && (!item.avail || item.avail === "0")) return "";
  if (!item.avail) return "";
  return ` / 入手 ${item.avail}`;
}

function mergeSpecialArmor(mods?: { special_armor?: SpecialArmor }[]): SpecialArmor | undefined {
  let out: SpecialArmor | undefined;
  for (const mod of mods || []) {
    const sa = mod.special_armor;
    if (!sa) continue;
    out = out || { immunities: {} };
    out.fire = (out.fire || 0) + (sa.fire || 0);
    out.cold = (out.cold || 0) + (sa.cold || 0);
    out.electricity = (out.electricity || 0) + (sa.electricity || 0);
    out.radiation = (out.radiation || 0) + (sa.radiation || 0);
    out.toxin_contact = (out.toxin_contact || 0) + (sa.toxin_contact || 0);
    out.pathogen_contact = (out.pathogen_contact || 0) + (sa.pathogen_contact || 0);
    out.immunities = {
      toxin_contact: Boolean(out.immunities?.toxin_contact || sa.immunities?.toxin_contact),
      toxin_inhalation: Boolean(out.immunities?.toxin_inhalation || sa.immunities?.toxin_inhalation),
      pathogen_contact: Boolean(out.immunities?.pathogen_contact || sa.immunities?.pathogen_contact),
      pathogen_inhalation: Boolean(out.immunities?.pathogen_inhalation || sa.immunities?.pathogen_inhalation),
    };
  }
  return out;
}

function accessoryFits(
  acc: {
    mounts?: string[];
    purchasable?: boolean;
    required?: { names?: string[]; categories?: string[]; types?: string[]; conceal_lte?: number | null; accessories?: string[] };
    forbidden?: { names?: string[]; categories?: string[]; types?: string[]; conceal_lte?: number | null; accessories?: string[] };
  },
  weapon: { name: string; category?: string; type?: string; conceal?: string; mounts?: string[] },
  installedNames: string[],
) {
  if (acc.purchasable === false) return false;
  const mounts = acc.mounts || [];
  const weaponMounts = new Set(weapon.mounts || []);
  if (mounts.length && !mounts.some((mount) => weaponMounts.has(mount) || mount === "Internal")) return false;
  const installed = new Set(installedNames);
  if (acc.forbidden?.accessories?.some((name) => installed.has(name))) return false;
  const matchOr = (cons?: { names?: string[]; categories?: string[]; types?: string[]; conceal_lte?: number | null }) => {
    if (!cons) return false;
    const has = Boolean(cons.names?.length || cons.categories?.length || cons.types?.length || cons.conceal_lte != null);
    if (!has) return false;
    if (cons.names?.includes(weapon.name)) return true;
    if (cons.categories?.includes(weapon.category || "")) return true;
    if (cons.types?.includes(weapon.type || "")) return true;
    const conceal = Number(weapon.conceal || 0);
    if (cons.conceal_lte != null && Number.isFinite(conceal) && conceal <= cons.conceal_lte) return true;
    return false;
  };
  const required = acc.required;
  const hasRequired = Boolean(required && (required.names?.length || required.categories?.length || required.types?.length || required.conceal_lte != null));
  if (hasRequired && !matchOr(required)) return false;
  if (matchOr(acc.forbidden)) return false;
  return true;
}

function armorModFits(
  mod: {
    purchasable?: boolean;
    category?: string;
    unique?: string;
    required_names?: string[];
    required_mods?: string[];
  },
  armor: { name: string; category?: string; addmodcategories?: string[] },
  installedNames: string[],
) {
  if (mod.purchasable === false) return false;
  const requiredNames = mod.required_names || [];
  if (requiredNames.length && !requiredNames.includes(armor.name)) return false;
  const requiredMods = mod.required_mods || [];
  if (requiredMods.some((name) => !installedNames.includes(name))) return false;
  const category = mod.category || "General";
  const allowed = new Set(armor.addmodcategories || []);
  if (category === "General") return true;
  if (allowed.has(category)) return true;
  return category === (armor.category || "");
}

function removeWareTree(items: WareInstall[], id: string): WareInstall[] {
  const drop = new Set<string>([id]);
  let grew = true;
  while (grew) {
    grew = false;
    for (const row of items) {
      if (row.parent_id && drop.has(row.parent_id) && !drop.has(row.id)) {
        drop.add(row.id);
        grew = true;
      }
    }
  }
  return items.filter((row) => !drop.has(row.id));
}

function wareBounds(item: WareCatalogItem, ranges?: Record<string, { min: number; max: number }>) {
  return ranges?.[item.id] || { min: item.minrating, max: item.maxrating };
}

function hideFromWareCatalog(item: WareCatalogItem, kind: "cyberware" | "bioware") {
  if (item.requireparent || item.formula_rating) return true;
  const same = item.required?.[kind] || [];
  const other = item.required?.[kind === "bioware" ? "cyberware" : "bioware"] || [];
  return same.length > 0 && other.length === 0;
}

const SIDE_JA: Record<string, string> = { Left: "左", Right: "右" };

function sideSlotKey(item: WareCatalogItem) {
  return (item.limbslot || item.id || "").toLowerCase();
}

function nextFreeSide(items: WareInstall[], catalogItems: WareCatalogItem[], ware: WareCatalogItem) {
  if (!ware.selectside) return undefined;
  const slot = sideSlotKey(ware);
  const used = new Set(
    items
      .filter((row) => !row.parent_id && row.side)
      .filter((row) => {
        const spec = catalogItems.find((w) => w.id === row.ware_id);
        return spec?.selectside && sideSlotKey(spec) === slot;
      })
      .map((row) => row.side),
  );
  return used.has("Left") && !used.has("Right") ? "Right" : "Left";
}

const REDLINER_SLOT_JA: Record<string, string> = { arm: "腕", leg: "脚", torso: "胴", skull: "頭蓋" };

function skillDice(rating: number, bonus?: number) {
  if (!bonus) return String(rating);
  const sign = bonus > 0 ? "+" : "";
  return `${rating} ${sign}${bonus}`;
}

function mergeRatings(base?: Record<string, number> | null, extra?: Record<string, number> | null) {
  const out: Record<string, number> = { ...(base || {}) };
  for (const [name, rating] of Object.entries(extra || {})) {
    out[name] = Math.max(out[name] || 0, rating || 0);
  }
  return out;
}

function poolRating(pool: Record<string, number>, name: string) {
  let best = pool[name] || 0;
  const prefix = `${name} (`;
  for (const [key, value] of Object.entries(pool)) {
    if (key.startsWith(prefix)) best = Math.max(best, value || 0);
  }
  return best;
}

function skillsoftBit(rating?: number) {
  if (!rating) return null;
  return <span className="muted"> ソフトR{rating}</span>;
}

function specBit(spec?: string | null, label?: string) {
  if (!spec) return null;
  return <span className="muted" title={label || spec}> 専門+2</span>;
}

function SpecPicker({
  options,
  value,
  disabled,
  emptyLabel = "専門なし",
  placeholder = "専門化",
  tr,
  onDraft,
  onCommit,
}: {
  options: string[];
  value: string;
  disabled?: boolean;
  emptyLabel?: string;
  placeholder?: string;
  tr: (name: string) => string;
  onDraft: (next: string) => void;
  onCommit: (next: string) => void;
}) {
  const [customMode, setCustomMode] = useState(() => Boolean(value && !options.includes(value)));
  const selectValue = !value && !customMode ? "" : customMode || (value && !options.includes(value)) ? "__custom__" : value;
  return (
    <span className="spec-pick">
      <select
        disabled={disabled}
        value={selectValue}
        title={value ? tr(value) : emptyLabel}
        onChange={(e) => {
          const next = e.target.value;
          if (next === "__custom__") {
            setCustomMode(true);
            return;
          }
          setCustomMode(false);
          onCommit(next);
        }}
      >
        <option value="">{emptyLabel}</option>
        {options.map((spec) => (
          <option key={spec} value={spec}>{tr(spec)}</option>
        ))}
        <option value="__custom__">自由入力</option>
      </select>
      {(customMode || (value && !options.includes(value))) && !disabled ? (
        <input
          value={value}
          placeholder={placeholder}
          onChange={(e) => onDraft(e.target.value)}
          onBlur={(e) => onCommit(e.target.value.trim())}
        />
      ) : null}
    </span>
  );
}

type QualityReqCtx = {
  qualities: Set<string>;
  metatypes: Set<string>;
  magenabled: boolean;
  resenabled: boolean;
  skills: Record<string, number>;
  knowledge: Record<string, number>;
  powers: Set<string>;
  spells: Set<string>;
  cyberware: Set<string>;
  bioware: Set<string>;
  tradition: string;
  essence: number;
  essLost: number;
};

function reqNodeMet(node: QualityReqNode, ctx: QualityReqCtx): boolean {
  const tag = node.tag;
  const children = node.children || [];
  if (tag === "oneof") return children.length ? children.some((child) => reqNodeMet(child, ctx)) : true;
  if (tag === "allof" || tag === "group") return children.length ? children.every((child) => reqNodeMet(child, ctx)) : true;
  const name = node.name || "";
  if (tag === "quality") return ctx.qualities.has(name);
  if (tag === "metatype") return ctx.metatypes.has(name);
  if (tag === "magenabled") return ctx.magenabled;
  if (tag === "resenabled") return ctx.resenabled;
  if (tag === "power") return ctx.powers.has(name);
  if (tag === "cyberware") return ctx.cyberware.has(name);
  if (tag === "bioware") return ctx.bioware.has(name);
  if (tag === "spell") return ctx.spells.has(name);
  if (tag === "tradition") return ctx.tradition === name;
  if (tag === "skill") {
    const rating = node.val || 1;
    const pool = (node.type || "").toLowerCase() === "knowledge" ? ctx.knowledge : ctx.skills;
    return poolRating(pool, name) >= rating;
  }
  if (tag === "ess") {
    const value = node.value || 0;
    return value < 0 ? ctx.essLost + 1e-9 >= Math.abs(value) : ctx.essence + 1e-9 >= value;
  }
  return false;
}

function qualityTreeMet(tree: QualityReqNode[] | undefined, ctx: QualityReqCtx) {
  const nodes = tree || [];
  if (!nodes.length) return true;
  return nodes.every((node) => reqNodeMet(node, ctx));
}

function qualityBlockReason(item: Catalog["qualities"][number], ctx: QualityReqCtx) {
  if ((item.required_tree || []).length && !qualityTreeMet(item.required_tree, ctx)) return "前提を満たしていません";
  if ((item.forbidden_tree || []).length && qualityTreeMet(item.forbidden_tree, ctx)) return "現在のキャラクターでは取れません";
  return "";
}

function dropSkillPicksForPrefix(picks: Record<string, string> | undefined, prefixes: string[]) {
  const next = { ...(picks || {}) };
  for (const key of Object.keys(next)) {
    if (prefixes.some((prefix) => key.startsWith(prefix))) delete next[key];
  }
  return next;
}

function dropRemovedWarePicks(picks: Record<string, string> | undefined, remaining: WareInstall[]) {
  const keep = new Set(remaining.map((row) => row.id));
  const next = { ...(picks || {}) };
  for (const key of Object.keys(next)) {
    const match = key.match(/^ware:([^:]+):/);
    if (match && !keep.has(match[1])) delete next[key];
  }
  return next;
}

function SkillPickSelects(props: {
  slots: SkillPickSlot[];
  tr: (name: string) => string;
  onPick: (key: string, skill: string) => void;
}) {
  if (!props.slots.length) return null;
  return (
    <div className="skill-picks">
      {props.slots.map((slot) => (
        <label key={slot.key}>
          {props.tr(slot.source)} のスキル
          {slot.bonus ? ` ${slot.bonus > 0 ? "+" : ""}${slot.bonus}` : ""}
          {slot.max ? ` 上限+${slot.max}` : ""}
          <select value={slot.picked} onChange={(e) => props.onPick(slot.key, e.target.value)}>
            <option value="">選択してください</option>
            {slot.options.map((name) => (
              <option key={name} value={name}>{props.tr(name)}</option>
            ))}
          </select>
        </label>
      ))}
    </div>
  );
}

function limbQualityLine(q: NonNullable<Character["derived"]["limb_quality"]>) {
  const bits: string[] = [];
  if (q.limb_bonus) bits.push(`肢 STR/AGI +${q.limb_bonus}`);
  for (const [key, value] of Object.entries(q.attribute_bonus || {})) {
    if (key === "STR" || key === "AGI" || !value) continue;
    bits.push(`${key} +${value}`);
  }
  if (q.cm_physical) bits.push(`物理CM ${q.cm_physical}`);
  const effect = bits.length ? bits.join(" ・ ") : "ボーナスなし";
  const parts = (q.include || ["arm", "leg"]).map((slot) => REDLINER_SLOT_JA[slot] || slot).join("・");
  return `リム本数 Quality ${q.count}本（${q.pairs}組 / ${parts}） ・ ${effect}`;
}

function WareRow(props: {
  item: InstalledWare;
  childrenItems: InstalledWare[];
  catalogItems: WareCatalogItem[];
  grades: { name: string; ess: number; cost: number }[];
  kind: "cyberware" | "bioware";
  tr: (name: string) => string;
  slotValue: string;
  wareRanges?: Record<string, { min: number; max: number }>;
  onSlotChange: (wareId: string) => void;
  onPatchRow: (id: string, next: Partial<WareInstall>) => void;
  onRemove: (id: string) => void;
  onAddChild: (wareId: string) => void;
  pickSlots?: SkillPickSlot[];
  onSkillPick?: (key: string, skill: string) => void;
  nested?: boolean;
}) {
  const { item, childrenItems, catalogItems, grades, kind, tr, slotValue, wareRanges, onSlotChange, onPatchRow, onRemove, onAddChild, pickSlots, onSkillPick, nested } = props;
  const spec = catalogItems.find((w) => w.id === item.ware_id);
  const slots = (spec?.allow_subsystems || []).filter(Boolean);
  const slotOptions = catalogItems.filter((w) => {
    if (w.id === item.ware_id) return false;
    if ((w.required?.[kind] || []).includes(item.name)) return true;
    return slots.includes(w.category) && Boolean(w.plugin || w.requireparent);
  });
  const rowGrades = grades.filter((g) => !(spec?.bannedgrades || []).includes(g.name));
  const chosen = slotValue || slotOptions[0]?.id || "";
  const capMax = item.capacity_max || 0;
  const ratingMin = item.rating_min ?? spec?.minrating ?? 1;
  const ratingMax = item.rating_max ?? spec?.maxrating ?? 1;
  return (
    <div className={`cyber-item${nested ? " nested" : ""}`}>
      <div>
        <b>{tr(item.name)}{item.side ? `（${SIDE_JA[item.side] || item.side}）` : ""}{item.included ? "（同梱）" : ""}</b>
        <div className="muted">
          {item.name} / {item.category} / ESS −{item.essence} / {item.nuyen.toLocaleString()}¥{availBit(item)} / {item.source}
          {capMax > 0 ? <span className="cap"> ・ 容量 {item.capacity_used ?? 0}/{capMax}</span> : null}
          {item.limb_str != null ? <span className="cap"> ・ 肢 STR {item.limb_str} / AGI {item.limb_agi}</span> : null}
        </div>
        <div className="cyber-controls">
          {spec?.selectside && !item.parent_id && !item.included ? (
            <label>
              左右
              <select value={item.side || "Left"} onChange={(e) => onPatchRow(item.id, { side: e.target.value })}>
                <option value="Left">左</option>
                <option value="Right">右</option>
              </select>
            </label>
          ) : null}
          {spec && ratingMax > ratingMin && !item.included ? (
            <label>
              レーティング
              <input
                type="number"
                min={ratingMin}
                max={ratingMax}
                value={item.rating}
                onChange={(e) => onPatchRow(item.id, { rating: Number(e.target.value) })}
              />
            </label>
          ) : null}
          {!item.included && !spec?.forcegrade ? (
            <label>
              グレード
              <select value={item.grade} onChange={(e) => onPatchRow(item.id, { grade: e.target.value })}>
                {rowGrades.map((g) => (
                  <option key={g.name} value={g.name}>{g.name} (ESS×{g.ess} / ¥×{g.cost})</option>
                ))}
              </select>
            </label>
          ) : null}
          {spec?.has_wireless ? (
            <label>
              <input
                type="checkbox"
                checked={item.wireless}
                onChange={(e) => onPatchRow(item.id, { wireless: e.target.checked })}
              />
              ワイヤレス
            </label>
          ) : null}
        </div>
        {onSkillPick ? (
          <SkillPickSelects
            slots={(pickSlots || []).filter((slot) => slot.source_id === item.id)}
            tr={tr}
            onPick={onSkillPick}
          />
        ) : null}
        {childrenItems.map((child) => (
          <WareRow
            key={child.id}
            item={child}
            childrenItems={[]}
            catalogItems={catalogItems}
            grades={grades}
            kind={kind}
            tr={tr}
            slotValue=""
            wareRanges={wareRanges}
            onSlotChange={() => undefined}
            onPatchRow={onPatchRow}
            onRemove={onRemove}
            onAddChild={() => undefined}
            pickSlots={pickSlots}
            onSkillPick={onSkillPick}
            nested
          />
        ))}
        {slotOptions.length > 0 ? (
          <div className="slot-picker">
            <select value={chosen} onChange={(e) => onSlotChange(e.target.value)}>
              {slotOptions.map((w) => {
                const range = wareBounds(w, wareRanges);
                const showRange = range.max > range.min || range.max > 1;
                return (
                  <option key={w.id} value={w.id}>
                    {tr(w.name)} / {w.capacity ? `[${w.capacity}]` : w.category}{showRange ? ` R${range.min}-${range.max}` : ""}
                  </option>
                );
              })}
            </select>
            <button className="btn primary" disabled={!chosen} onClick={() => chosen && onAddChild(chosen)}>スロットに追加</button>
          </div>
        ) : null}
      </div>
      {item.included ? <span className="muted">同梱</span> : <button className="btn danger" onClick={() => onRemove(item.id)}>削除</button>}
    </div>
  );
}

function selectLabel(kind?: string | null) {
  if (kind === "skill") return "スキル";
  if (kind === "attribute") return "属性";
  if (kind === "spell") return "呪文";
  return "対象";
}

function MentorPicker({
  catalog,
  mentor,
  ch,
  tr,
  onPatch,
}: {
  catalog: Catalog;
  mentor?: MentorInfo | null;
  ch: Character;
  tr: (name: string) => string;
  onPatch: (body: Record<string, unknown>) => void;
}) {
  return (
    <div className="cyber-item">
      <div>
        <b>メンタースピリット</b>
        <div className="muted">{mentor ? `${tr(mentor.name)} / ${mentor.source}` : "未選択"}</div>
        <div className="cyber-controls">
          <label>
            メンター
            <select value={ch.mentor_id || ""} onChange={(e) => onPatch({ mentor_id: e.target.value, mentor_choices: [], mentor_extras: {} })}>
              <option value="">選択してください</option>
              {(catalog.mentors || []).map((item) => (
                <option key={item.id} value={item.id}>{tr(item.name)}</option>
              ))}
            </select>
          </label>
        </div>
        {mentor?.advantage ? <p className="muted">{mentor.advantage}</p> : null}
        {(mentor?.choices || []).map((choice) => (
          <label key={choice.name} className="skill-row">
            <input
              type="checkbox"
              checked={choice.selected}
              onChange={() => {
                const current = new Set(ch.mentor_choices || mentor.choices.filter((row) => row.selected).map((row) => row.name));
                if (choice.selected) current.delete(choice.name);
                else {
                  if (choice.set) {
                    mentor.choices.filter((row) => row.set === choice.set).forEach((row) => current.delete(row.name));
                  }
                  current.add(choice.name);
                }
                onPatch({ mentor_choices: [...current] });
              }}
            />
            <span>{choice.name}</span>
            {choice.extra_options.length ? (
              <select
                value={choice.extra || ""}
                onChange={(e) => onPatch({ mentor_extras: { ...(ch.mentor_extras || {}), [choice.name]: e.target.value } })}
              >
                <option value="">対象を選択</option>
                {choice.extra_options.map((name) => (
                  <option key={name} value={name}>{tr(name)}</option>
                ))}
              </select>
            ) : null}
          </label>
        ))}
      </div>
    </div>
  );
}

function ExtraSelect({
  item,
  tr,
  onChange,
}: {
  item: InstalledAdeptPower;
  tr: (name: string) => string;
  onChange: (extra: string) => void;
}) {
  if (!item.select) return null;
  return (
    <label>
      {selectLabel(item.select)}
      <select value={item.extra || ""} onChange={(e) => onChange(e.target.value)}>
        <option value="">選択してください</option>
        {item.options.map((name) => (
          <option key={name} value={name}>{item.select === "attribute" ? (ATTR_JA[name] || name) : tr(name)}</option>
        ))}
      </select>
    </label>
  );
}

export default function Page() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [ch, setCh] = useState<Character | null>(null);
  const [tab, setTab] = useState<Tab>("priority");
  const [qSearch, setQSearch] = useState("");
  const [qCat, setQCat] = useState<"all" | "Positive" | "Negative">("all");
  const [cySearch, setCySearch] = useState("");
  const [cyCat, setCyCat] = useState("all");
  const [addGrade, setAddGrade] = useState("Standard");
  const [bioSearch, setBioSearch] = useState("");
  const [bioCat, setBioCat] = useState("all");
  const [bioGrade, setBioGrade] = useState("Standard");
  const [powerSearch, setPowerSearch] = useState("");
  const [enhSearch, setEnhSearch] = useState("");
  const [qiSearch, setQiSearch] = useState("");
  const [spellSearch, setSpellSearch] = useState("");
  const [spellKind, setSpellKind] = useState<"all" | "spell" | "ritual" | "enchantment">("all");
  const [knowSearch, setKnowSearch] = useState("");
  const [knowCat, setKnowCat] = useState("all");
  const [customKnow, setCustomKnow] = useState("");
  const [customKnowCat, setCustomKnowCat] = useState("Street");
  const [focusSearch, setFocusSearch] = useState("");
  const [martialSearch, setMartialSearch] = useState("");
  const [cfSearch, setCfSearch] = useState("");
  const [spriteSearch, setSpriteSearch] = useState("");
  const [gearKind, setGearKind] = useState<GearKind>("armor");
  const [gearSearch, setGearSearch] = useState("");
  const [gearCat, setGearCat] = useState("all");
  const [contactName, setContactName] = useState("");
  const [contactRole, setContactRole] = useState("");
  const [slotPick, setSlotPick] = useState<Record<string, string>>({});
  const [extraPick, setExtraPick] = useState<Record<string, string>>({});
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const busy = useRef(false);

  useEffect(() => {
    (async () => {
      try {
        const [cat, created] = await Promise.all([api.catalog(), api.create("Runner")]);
        setCatalog(cat);
        setCh(created);
      } catch (e) {
        setError(e instanceof Error ? e.message : "起動に失敗しました");
      }
    })();
  }, []);

  async function patch(body: Record<string, unknown>) {
    if (!ch || busy.current) return;
    busy.current = true;
    try {
      setCh(await api.patch(ch.id, body));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "更新に失敗しました");
    } finally {
      busy.current = false;
    }
  }

  const tr = (name: string) => catalog?.translations[name] || name;

  const filteredQualities = useMemo(() => {
    if (!catalog) return [];
    const q = qSearch.trim().toLowerCase();
    return catalog.qualities
      .filter((item) => qCat === "all" || item.category === qCat)
      .filter((item) => {
        if (!q) return !item.source || item.source === "SR5";
        return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
      })
      .slice(0, 80);
  }, [catalog, qSearch, qCat]);

  const cyberCats = useMemo(() => {
    if (!catalog) return [];
    return [...new Set(catalog.cyberware.items.filter((w) => !hideFromWareCatalog(w, "cyberware")).map((w) => w.category))].sort();
  }, [catalog]);

  const filteredCyber = useMemo(() => {
    if (!catalog) return [];
    const q = cySearch.trim().toLowerCase();
    return catalog.cyberware.items
      .filter((w) => !hideFromWareCatalog(w, "cyberware"))
      .filter((w) => cyCat === "all" || w.category === cyCat)
      .filter((w) => !q || w.name.toLowerCase().includes(q) || tr(w.name).includes(cySearch))
      .slice(0, 80);
  }, [catalog, cySearch, cyCat]);

  const bioCats = useMemo(() => {
    if (!catalog) return [];
    return [...new Set((catalog.bioware?.items || []).filter((w) => !hideFromWareCatalog(w, "bioware")).map((w) => w.category))].sort();
  }, [catalog]);

  const filteredBio = useMemo(() => {
    if (!catalog) return [];
    const q = bioSearch.trim().toLowerCase();
    return (catalog.bioware?.items || [])
      .filter((w) => !hideFromWareCatalog(w, "bioware"))
      .filter((w) => bioCat === "all" || w.category === bioCat)
      .filter((w) => !q || w.name.toLowerCase().includes(q) || tr(w.name).includes(bioSearch))
      .slice(0, 80);
  }, [catalog, bioSearch, bioCat]);

  const filteredPowers = useMemo(() => {
    if (!catalog) return [];
    const q = powerSearch.trim().toLowerCase();
    return (catalog.powers || [])
      .filter((item) => !q ? item.source === "SR5" : item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q))
      .slice(0, 80);
  }, [catalog, powerSearch]);

  const filteredKnowledge = useMemo(() => {
    if (!catalog) return [];
    const q = knowSearch.trim().toLowerCase();
    return (catalog.skills.knowledge || [])
      .filter((item) => knowCat === "all" || item.category === knowCat)
      .filter((item) => {
        if (!q) return !item.source || item.source === "SR5";
        return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
      })
      .slice(0, 40);
  }, [catalog, knowSearch, knowCat]);

  function download() {
    if (!ch) return;
    const blob = new Blob([JSON.stringify(ch, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${ch.name || "character"}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  async function onImport(file: File) {
    const payload = JSON.parse(await file.text());
    setCh(await api.import(payload));
  }

  if (error && !ch) {
    return <div className="main"><p className="errors">{error}</p></div>;
  }
  if (!catalog || !ch) {
    return <div className="main">読み込み中…</div>;
  }

  const d = ch.derived;
  const spec = d.metatype_info.attributes;
  const table = catalog.priority_table;
  const ownedKnowledge = new Set((d.knowledge_skills || []).map((row) => row.name));
  const catalogKnowledge = new Set((catalog.skills.knowledge || []).map((item) => item.name));
  const qualityCtx: QualityReqCtx = {
    qualities: new Set((d.qualities || []).map((item) => item.name)),
    metatypes: new Set([ch.metatype, ch.metavariant || ""].filter(Boolean)),
    magenabled: d.enabled_tabs.includes("MAG"),
    resenabled: d.enabled_tabs.includes("RES"),
    skills: mergeRatings(d.skill_totals, d.skillsoft),
    knowledge: mergeRatings(ch.knowledge_skills, d.skillsoft),
    powers: new Set((d.adept_powers || []).map((item) => item.name)),
    spells: new Set((d.spells || []).map((item) => item.name)),
    cyberware: new Set((d.cyberware || []).map((item) => item.name)),
    bioware: new Set((d.bioware || []).map((item) => item.name)),
    tradition: d.tradition?.name || "",
    essence: d.essence,
    essLost: (d.essence_lost_cyber || 0) + (d.essence_lost_bio || 0),
  };
  const ownedQualitySpecs = (catalog.qualities || []).filter((item) => ch.quality_ids.includes(item.id));

  function patchKnowledge(next: {
    knowledge_skills?: Record<string, number>;
    native_languages?: string[];
    knowledge_categories?: Record<string, string>;
  }) {
    patch({
      knowledge_skills: next.knowledge_skills ?? ch.knowledge_skills,
      native_languages: next.native_languages ?? ch.native_languages ?? [],
      knowledge_categories: next.knowledge_categories ?? ch.knowledge_categories ?? {},
    });
  }

  function addKnowledge(name: string, category?: string) {
    const trimmed = name.trim();
    if (!trimmed || ownedKnowledge.has(trimmed)) return;
    const ratings = { ...ch.knowledge_skills, [trimmed]: 1 };
    const cats = { ...(ch.knowledge_categories || {}) };
    const specItem = catalog.skills.knowledge.find((item) => item.name === trimmed);
    if (!specItem && category) cats[trimmed] = category;
    patchKnowledge({ knowledge_skills: ratings, knowledge_categories: cats });
    setCustomKnow("");
  }

  function setKnowledgeNative(name: string, on: boolean) {
    const ratings = { ...ch.knowledge_skills };
    const prev = (ch.native_languages || [])[0];
    if (on) {
      delete ratings[name];
      if (prev && prev !== name) ratings[prev] = ratings[prev] || 1;
      patchKnowledge({ knowledge_skills: ratings, native_languages: [name] });
      return;
    }
    ratings[name] = ratings[name] || 1;
    patchKnowledge({ knowledge_skills: ratings, native_languages: [] });
  }

  function removeKnowledge(name: string) {
    const ratings = { ...ch.knowledge_skills };
    delete ratings[name];
    const cats = { ...(ch.knowledge_categories || {}) };
    delete cats[name];
    const specs = { ...(ch.skill_specializations || {}) };
    delete specs[name];
    patch({
      knowledge_skills: ratings,
      native_languages: (ch.native_languages || []).filter((item) => item !== name),
      knowledge_categories: cats,
      skill_specializations: specs,
    });
  }

  function draftSpec(name: string, value: string) {
    const next = { ...(ch.skill_specializations || {}) };
    if (value) next[name] = value;
    else delete next[name];
    setCh({ ...ch, skill_specializations: next });
  }

  function commitSpec(name: string, value: string) {
    const next = { ...(ch.skill_specializations || {}) };
    const trimmed = value.trim();
    if (trimmed) next[name] = trimmed;
    else delete next[name];
    setCh({ ...ch, skill_specializations: next });
    patch({ skill_specializations: next });
  }

  function patchExotic(next: { id?: string; skill_name: string; extra?: string; rating?: number }[]) {
    patch({ exotic_skills: next });
  }

  function draftExotic(id: string, next: { extra?: string; rating?: number }) {
    setCh({
      ...ch,
      exotic_skills: (ch.exotic_skills || []).map((row) => (row.id === id ? { ...row, ...next } : row)),
    });
  }

  return (
    <div className="app">
      <div className="main">
        <h1>CHUMMER WEB</h1>
        <p className="sub">非公式 Shadowrun 5e キャラクター作成。Catalyst / Topps 非提携。データは Chummer5a (GPL-3.0)。</p>

        <div className="toolbar">
          <input value={ch.name} onChange={(e) => setCh({ ...ch, name: e.target.value })} onBlur={(e) => patch({ name: e.target.value })} />
          <button className="btn primary" onClick={download}>JSON保存</button>
          <button className="btn" onClick={() => fileRef.current?.click()}>JSON読込</button>
          <input ref={fileRef} type="file" accept="application/json" hidden onChange={(e) => e.target.files && onImport(e.target.files[0])} />
        </div>

        <div className="tabs">
          {([
            ["priority", "優先度"],
            ["meta", "メタタイプ"],
            ["attrs", "属性"],
            ["skills", "スキル"],
            ["qualities", "クオリティ"],
            ["cyber", "サイバー"],
            ["bio", "バイオ"],
            ["gear", "ギア"],
            ["contacts", "コネクト"],
            ["martial", "武道"],
            ...(d.enabled_tabs.includes("initiation") ? [["initiation", "イニシエーション"] as const] : []),
            ...(d.enabled_tabs.includes("submersion") ? [["submersion", "サブマージョン"] as const] : []),
            ...(d.enabled_tabs.includes("adept") ? [["adept", "アデプト"] as const] : []),
            ...(d.enabled_tabs.includes("spells") ? [["spells", "術式"] as const] : []),
            ...(d.enabled_tabs.includes("spirits") ? [["spirits", "精霊"] as const] : []),
            ...(d.enabled_tabs.includes("foci") ? [["foci", "フォーカス"] as const] : []),
            ...(d.enabled_tabs.includes("complexforms") ? [["complexforms", "複合体"] as const] : []),
            ...(d.enabled_tabs.includes("sprites") ? [["sprites", "スプライト"] as const] : []),
          ] as const).map(([k, label]) => (
            <button key={k} className={`tab ${tab === k ? "active" : ""}`} onClick={() => setTab(k)}>{label}</button>
          ))}
        </div>

        {tab === "priority" && (
          <div className="card">
            <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap", alignItems: "center" }}>
              <button
                className={`choice ${(ch.build_method || "Priority") === "Priority" ? "selected" : ""}`}
                onClick={() => {
                  const letters = CATS.map((c) => ch.priorities[c.key]);
                  const unique = [...letters].sort().join("") === "ABCDE";
                  patch({
                    build_method: "Priority",
                    ...(unique
                      ? {}
                      : {
                          priorities: { ...DEFAULT_PRIORITIES },
                          talent: "Mundane",
                        }),
                  });
                }}
              >
                Priority
              </button>
              <button
                className={`choice ${(ch.build_method || "Priority") === "SumToTen" ? "selected" : ""}`}
                onClick={() => patch({ build_method: "SumToTen" })}
              >
                Sum to Ten
              </button>
              <button
                className={`choice ${(ch.build_method || "Priority") === "Karma" ? "selected" : ""}`}
                onClick={() => patch({ build_method: "Karma", talent: ch.talent || "Mundane" })}
              >
                Karma
              </button>
              {(ch.build_method || "Priority") === "SumToTen" ? (
                <span className="muted">
                  合計 {d.sum_to_ten?.used ?? 0}/{d.sum_to_ten?.max ?? 10}
                  {" ・ "}A4 / B3 / C2 / D1 / E0
                </span>
              ) : null}
              {(ch.build_method || "Priority") === "Karma" ? (
                <span className="muted">
                  カルマ {d.karma.remaining} / {d.karma.pool}
                  {" ・ "}1K={d.karma_chargen?.nuyen_per_karma ?? 2000}¥（最大 {d.karma_chargen?.nuyen_karma_max ?? 235}K）
                </span>
              ) : null}
            </div>
            {(ch.build_method || "Priority") === "Karma" ? (
              <div style={{ display: "grid", gap: 12 }}>
                <p className="muted">
                  優先度表は使いません。メタタイプ／属性／スキル／術式などをカルマで購入します（開始 {d.karma.pool}）。
                  MAG／RES はタレント選択で解禁され、最低1から買い上げます。無料の術式枠はありません。
                </p>
                <label>
                  タレント
                  <select value={ch.talent} onChange={(e) => patch({ talent: e.target.value })}>
                    {(catalog.karma_talents || []).map((t) => (
                      <option key={t.name} value={t.name}>
                        {t.label || t.name}
                        {t.magic ? ` / MAG` : ""}
                        {t.resonance ? ` / RES` : ""}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  カルマ→ニューエン（{ch.karma_nuyen || 0}K = {((ch.karma_nuyen || 0) * (d.karma_chargen?.nuyen_per_karma || 2000)).toLocaleString()}¥）
                  <input
                    type="range"
                    min={0}
                    max={d.karma_chargen?.nuyen_karma_max ?? 235}
                    value={ch.karma_nuyen || 0}
                    onChange={(e) => setCh({ ...ch, karma_nuyen: Number(e.target.value) })}
                    onMouseUp={(e) => patch({ karma_nuyen: Number((e.target as HTMLInputElement).value) })}
                    onTouchEnd={(e) => patch({ karma_nuyen: Number((e.target as HTMLInputElement).value) })}
                    onBlur={(e) => patch({ karma_nuyen: Number(e.target.value) })}
                  />
                </label>
                {d.karma_chargen ? (
                  <div className="muted" style={{ display: "grid", gap: 4 }}>
                    <div>内訳: メタタイプ {d.karma_chargen.metatype} / 属性 {d.karma_chargen.attributes} / スキル {d.karma_chargen.skills} / 知識 {d.karma_chargen.knowledge} / 専門化 {d.karma_chargen.specializations}</div>
                    <div>クオリティ {d.karma_chargen.qualities} / ニューエン交換 {d.karma_chargen.nuyen_karma} / その他 {d.karma_chargen.other}</div>
                  </div>
                ) : null}
              </div>
            ) : (
            <table>
              <thead>
                <tr>
                  <th></th>
                  {LETTERS.map((l) => (
                    <th key={l}>
                      {l}
                      {(ch.build_method || "Priority") === "SumToTen" ? ` (${d.sum_to_ten?.costs?.[l] ?? SUM_TO_TEN_COST[l]})` : ""}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {CATS.map((cat) => (
                  <tr key={cat.key}>
                    <td className="rowhead">{cat.label}</td>
                    {LETTERS.map((letter) => {
                      const cell = table[cat.key][letter];
                      const sumMode = (ch.build_method || "Priority") === "SumToTen";
                      const takenBy = sumMode ? undefined : CATS.find((c) => ch.priorities[c.key] === letter && c.key !== cat.key);
                      return (
                        <td key={letter}>
                          <button
                            className={`choice ${ch.priorities[cat.key] === letter ? "selected" : ""}`}
                            onClick={() => {
                              const next = { ...ch.priorities };
                              if (!sumMode && takenBy) next[takenBy.key] = next[cat.key];
                              next[cat.key] = letter;
                              const extra: Record<string, unknown> = { priorities: next };
                              if (cat.key === "Talent") {
                                const options = table.Talent[letter].talents.filter((t) => t.name !== "Mundane");
                                extra.talent =
                                  letter === "E"
                                    ? "Mundane"
                                    : options.some((t) => t.name === ch.talent)
                                      ? ch.talent
                                      : options[0]?.name || "Magician";
                              }
                              patch(extra);
                            }}
                          >
                            {cell?.name?.replace(/^[A-E]\s*-\s*/, "") || letter}
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="muted">
              {(ch.build_method || "Priority") === "SumToTen"
                ? "同じ優先度を複数カテゴリに割り当てできます。合計がちょうど 10 になるようにしてください。"
                : "A〜E は各1回。クリックで入れ替えます。"}
            </p>
            )}
          </div>
        )}

        {tab === "meta" && (
          <div className="card">
            <div className="grid">
              {((ch.build_method || "Priority") === "Karma"
                ? catalog.metatypes.map((m) => ({
                    name: m.name,
                    special: 0,
                    karma: m.karma ?? 0,
                  }))
                : table.Heritage[ch.priorities.Heritage].metatypes
              ).map((m) => (
                <button key={m.name} className={`choice ${ch.metatype === m.name ? "selected" : ""}`} onClick={() => patch({ metatype: m.name, metavariant: null })}>
                  <b>{tr(m.name)}</b>
                  <div className="muted">
                    {m.name}
                    {(ch.build_method || "Priority") === "Karma"
                      ? ` / ${("karma" in m ? Number(m.karma) : 0) || 0}カルマ`
                      : ` / 特殊点 ${m.special}`}
                  </div>
                </button>
              ))}
            </div>
            {catalog.metatypes.find((m) => m.name === ch.metatype)?.metavariants?.length ? (
              <div style={{ marginTop: 12 }}>
                <label className="muted">メタバリアント</label>
                <select
                  value={ch.metavariant || ""}
                  onChange={(e) => patch({ metavariant: e.target.value || null })}
                >
                  <option value="">なし（{tr(ch.metatype)}）</option>
                  {catalog.metatypes.find((m) => m.name === ch.metatype)?.metavariants.map((v) => (
                    <option key={v.name} value={v.name}>{tr(v.name)} ({v.name})</option>
                  ))}
                </select>
              </div>
            ) : null}
            <div style={{ marginTop: 12 }}>
              <label className="muted">タレント</label>
              <select value={ch.talent} onChange={(e) => patch({ talent: e.target.value })}>
                {((ch.build_method || "Priority") === "Karma"
                  ? (catalog.karma_talents || []).map((t) => ({ name: t.name, label: t.label || t.name }))
                  : table.Talent[ch.priorities.Talent].talents
                ).map((t) => (
                  <option key={t.name} value={t.name}>{t.label || t.name}</option>
                ))}
              </select>
            </div>
          </div>
        )}

        {tab === "attrs" && (
          <div className="card">
            {ATTRS.map((key) => {
              const hidden = (key === "MAG" && !d.enabled_tabs.includes("MAG")) || (key === "RES" && !d.enabled_tabs.includes("RES"));
              if (hidden) return null;
              const range = spec[key] || { min: 1, max: 6, aug: 6 };
              return (
                <div className="attr-row" key={key}>
                  <span>{ATTR_JA[key]}</span>
                  <input
                    type="range"
                    min={range.min}
                    max={range.max}
                    value={ch.attributes[key] ?? range.min}
                    onChange={(e) => {
                      const attributes = { ...ch.attributes, [key]: Number(e.target.value) };
                      setCh({ ...ch, attributes });
                    }}
                    onMouseUp={(e) => {
                      const value = Number((e.target as HTMLInputElement).value);
                      patch({ attributes: { ...ch.attributes, [key]: value } });
                    }}
                    onTouchEnd={(e) => {
                      const value = Number((e.target as HTMLInputElement).value);
                      patch({ attributes: { ...ch.attributes, [key]: value } });
                    }}
                    onBlur={(e) => {
                      const value = Number((e.target as HTMLInputElement).value);
                      patch({ attributes: { ...ch.attributes, [key]: value } });
                    }}
                  />
                  <b>
                    {d.totals[key]} <span className="muted">/{range.max}</span>
                    {(d.ware_attr_bonus?.[key] || 0) !== 0 ? (
                      <span className="muted"> ウェア+{d.ware_attr_bonus![key]}</span>
                    ) : null}
                    {d.limb_replace && (key === "STR" || key === "AGI") ? (
                      <span className="muted"> 肉{key === "STR" ? d.limb_replace.meat_str : d.limb_replace.meat_agi}</span>
                    ) : null}
                  </b>
                </div>
              );
            })}
            <p className="muted">属性点 {d.points.attributes.used}/{d.points.attributes.max} ・ 特殊点 {d.points.special.used}/{d.points.special.max}</p>
          </div>
        )}

        {tab === "skills" && (
          <div className="card">
            <p className="muted">スキル {d.points.skills.used}/{d.points.skills.max} ・ グループ {d.points.skill_groups.used}/{d.points.skill_groups.max} ・ 知識 {d.points.knowledge.used}/{d.points.knowledge.max} ・ 専門化は1点</p>
            <h3>スキルグループ</h3>
            {catalog.skills.groups.map((g) => (
              <div className="skill-row" key={g}>
                <span>{tr(g)}</span>
                <input
                  type="range"
                  min={0}
                  max={6}
                  value={ch.skill_groups[g] || 0}
                  onChange={(e) => setCh({ ...ch, skill_groups: { ...ch.skill_groups, [g]: Number(e.target.value) } })}
                  onMouseUp={(e) => {
                    const value = Number((e.target as HTMLInputElement).value);
                    patch({ skill_groups: { ...ch.skill_groups, [g]: value } });
                  }}
                  onBlur={(e) => {
                    const value = Number((e.target as HTMLInputElement).value);
                    patch({ skill_groups: { ...ch.skill_groups, [g]: value } });
                  }}
                />
                <b>{skillDice(ch.skill_groups[g] || 0, d.skill_group_bonus?.[g])}</b>
              </div>
            ))}
            <h3>アクティブスキル</h3>
            {catalog.skills.skills.filter((s) => s.source === "SR5" && !s.name.includes("Exotic")).map((s) => {
              const specValue = ch.skill_specializations?.[s.name] || "";
              const hasSkill = (ch.skills[s.name] || 0) > 0 || (d.skill_totals[s.name] || 0) > 0 || (d.skillsoft?.[s.name] || 0) > 0;
              return (
              <div className="skill-row has-spec" key={s.id}>
                <span title={[s.attribute, ...(d.skill_bonus_notes?.[s.name] || [])].join(" / ")}>{tr(s.name)}</span>
                <input
                  type="range"
                  min={0}
                  max={6 + (d.skill_max_bonus?.[s.name] || 0)}
                  value={ch.skills[s.name] || d.skill_totals[s.name] || 0}
                  onChange={(e) => setCh({ ...ch, skills: { ...ch.skills, [s.name]: Number(e.target.value) } })}
                  onMouseUp={(e) => {
                    const value = Number((e.target as HTMLInputElement).value);
                    patch({ skills: { ...ch.skills, [s.name]: value } });
                  }}
                  onBlur={(e) => {
                    const value = Number((e.target as HTMLInputElement).value);
                    patch({ skills: { ...ch.skills, [s.name]: value } });
                  }}
                />
                <SpecPicker
                  options={[...(s.specs || []), ...(d.martial_spec_options?.[s.name] || [])]}
                  value={specValue}
                  disabled={!hasSkill}
                  tr={tr}
                  onDraft={(next) => draftSpec(s.name, next)}
                  onCommit={(next) => commitSpec(s.name, next)}
                />
                <b>
                  {skillDice(Math.max(d.skill_totals[s.name] || 0, d.skillsoft?.[s.name] || 0), d.skill_bonus?.[s.name])}
                  {skillsoftBit(d.skillsoft?.[s.name])}
                  {specBit(specValue, tr(specValue))}
                </b>
              </div>
              );
            })}
            <h3>Exoticスキル</h3>
            <p className="muted">対象の指定が技能そのものです。同じ Exotic を別対象で複数持てます。専門化の追加点は不要です。</p>
            {(d.exotic_skills || []).length ? (d.exotic_skills || []).map((row) => {
              const local = (ch.exotic_skills || []).find((item) => item.id === row.id);
              const extra = local?.extra ?? row.extra ?? "";
              const rating = local?.rating ?? row.rating;
              const bonus = d.skill_bonus?.[row.label] || d.skill_bonus?.[row.skill_name];
              return (
                <div className="skill-row has-spec can-delete" key={row.id}>
                  <span title={[row.attribute, ...(d.skill_bonus_notes?.[row.label] || d.skill_bonus_notes?.[row.skill_name] || [])].join(" / ")}>
                    {tr(row.skill_name)}
                  </span>
                  <input
                    type="range"
                    min={1}
                    max={row.rating_max}
                    value={rating}
                    onChange={(e) => draftExotic(row.id, { rating: Number(e.target.value) })}
                    onMouseUp={(e) => {
                      const value = Number((e.target as HTMLInputElement).value);
                      patchExotic((ch.exotic_skills || []).map((item) => (
                        item.id === row.id ? { ...item, rating: value } : item
                      )));
                    }}
                    onBlur={(e) => {
                      const value = Number((e.target as HTMLInputElement).value);
                      patchExotic((ch.exotic_skills || []).map((item) => (
                        item.id === row.id ? { ...item, rating: value } : item
                      )));
                    }}
                  />
                  <SpecPicker
                    options={row.options || []}
                    value={extra}
                    emptyLabel="対象"
                    placeholder="対象"
                    tr={tr}
                    onDraft={(next) => draftExotic(row.id, { extra: next })}
                    onCommit={(next) => {
                      patchExotic((ch.exotic_skills || []).map((item) => (
                        item.id === row.id ? { ...item, extra: next } : item
                      )));
                    }}
                  />
                  <b>{skillDice(rating, bonus)}</b>
                  <button
                    className="btn danger"
                    onClick={() => patchExotic((ch.exotic_skills || []).filter((item) => item.id !== row.id))}
                  >
                    削除
                  </button>
                </div>
              );
            }) : (
              <p className="muted">まだありません。下のボタンから追加します。</p>
            )}
            <div className="option-row">
              {catalog.skills.skills.filter((s) => s.exotic || s.name.includes("Exotic")).map((s) => (
                <button
                  key={s.id}
                  className="btn"
                  onClick={() => patchExotic([...(ch.exotic_skills || []), { skill_name: s.name, extra: "", rating: 1 }])}
                >
                  {tr(s.name)} を追加
                </button>
              ))}
            </div>
            <h3>知識スキル</h3>
            <p className="muted">無料枠は (INT + LOG) × 2 ・ 母語は1つ無料。作成時のレーティングは1〜6です。専門化は知識点1です。</p>
            {Object.keys(d.skill_category_bonus || {}).length ? (
              <p className="muted">
                {Object.entries(d.skill_category_bonus || {})
                  .filter(([, bonus]) => bonus)
                  .map(([name, bonus]) => `${KNOW_CAT_JA[name] || tr(name)} ${bonus > 0 ? "+" : ""}${bonus}`)
                  .join(" ・ ")}
              </p>
            ) : null}
            {(d.knowledge_skills || []).length ? (d.knowledge_skills || []).map((row) => {
              const custom = !catalogKnowledge.has(row.name);
              const specValue = ch.skill_specializations?.[row.name] || row.spec || "";
              const knowSpec = (catalog.skills.knowledge || []).find((item) => item.name === row.name);
              return (
                <div className="know-row" key={row.name}>
                  <span title={[row.attribute, ...(d.skill_bonus_notes?.[row.name] || [])].join(" / ")}>
                    {tr(row.name)}
                    {custom ? " （カスタム）" : ""}
                  </span>
                  {custom ? (
                    <select
                      value={row.category}
                      onChange={(e) => patchKnowledge({
                        knowledge_categories: { ...(ch.knowledge_categories || {}), [row.name]: e.target.value },
                      })}
                    >
                      {KNOW_CATS.map((cat) => (
                        <option key={cat} value={cat}>{KNOW_CAT_JA[cat]}</option>
                      ))}
                    </select>
                  ) : (
                    <span className="muted">{KNOW_CAT_JA[row.category] || row.category}</span>
                  )}
                  {row.native ? (
                    <span className="muted">無料</span>
                  ) : (
                    <input
                      type="range"
                      min={1}
                      max={6}
                      value={ch.knowledge_skills[row.name] || row.rating}
                      onChange={(e) => setCh({
                        ...ch,
                        knowledge_skills: { ...ch.knowledge_skills, [row.name]: Number(e.target.value) },
                      })}
                      onMouseUp={(e) => {
                        const value = Number((e.target as HTMLInputElement).value);
                        patchKnowledge({ knowledge_skills: { ...ch.knowledge_skills, [row.name]: value } });
                      }}
                      onBlur={(e) => {
                        const value = Number((e.target as HTMLInputElement).value);
                        patchKnowledge({ knowledge_skills: { ...ch.knowledge_skills, [row.name]: value } });
                      }}
                    />
                  )}
                  <SpecPicker
                    options={knowSpec?.specs || []}
                    value={specValue}
                    tr={tr}
                    onDraft={(next) => draftSpec(row.name, next)}
                    onCommit={(next) => commitSpec(row.name, next)}
                  />
                  <b>
                    {row.native ? "母語" : skillDice(Math.max(row.rating, row.skillsoft || 0), d.skill_bonus?.[row.name])}
                    {row.native ? null : skillsoftBit(row.skillsoft)}
                    {specBit(specValue, tr(specValue))}
                  </b>
                  <span className="option-row" style={{ margin: 0, gap: 6 }}>
                    {row.category === "Language" ? (
                      <label className="native">
                        <input
                          type="checkbox"
                          checked={row.native}
                          onChange={(e) => setKnowledgeNative(row.name, e.target.checked)}
                        />
                        母語
                      </label>
                    ) : null}
                    <button className="btn danger" onClick={() => removeKnowledge(row.name)}>削除</button>
                  </span>
                </div>
              );
            }) : (
              <p className="muted">まだありません。カタログから追加するか、カスタム名で作れます。</p>
            )}
            <div className="option-row">
              <button className={`tab ${knowCat === "all" ? "active" : ""}`} onClick={() => setKnowCat("all")}>すべて</button>
              {KNOW_CATS.map((cat) => (
                <button key={cat} className={`tab ${knowCat === cat ? "active" : ""}`} onClick={() => setKnowCat(cat)}>
                  {KNOW_CAT_JA[cat]}
                </button>
              ))}
            </div>
            <input type="search" placeholder="知識スキルを検索" value={knowSearch} onChange={(e) => setKnowSearch(e.target.value)} />
            <div className="cyber-toolbar">
              <input
                type="text"
                placeholder="カスタム知識名"
                value={customKnow}
                onChange={(e) => setCustomKnow(e.target.value)}
              />
              <select value={customKnowCat} onChange={(e) => setCustomKnowCat(e.target.value)}>
                {KNOW_CATS.map((cat) => (
                  <option key={cat} value={cat}>{KNOW_CAT_JA[cat]}</option>
                ))}
              </select>
              <button className="btn primary" onClick={() => addKnowledge(customKnow, customKnowCat)}>カスタム追加</button>
            </div>
            <div className="quality-list">
              {filteredKnowledge.filter((item) => !ownedKnowledge.has(item.name)).map((item) => (
                <div className="quality-item" key={`${item.category}:${item.name}`}>
                  <div>
                    <b>{tr(item.name)}</b>
                    <div className="muted">{item.name} / {KNOW_CAT_JA[item.category] || item.category} / {item.attribute}</div>
                  </div>
                  <button className="btn primary" onClick={() => addKnowledge(item.name, item.category)}>追加</button>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === "qualities" && (
          <div className="card">
            {d.needs_mentor ? (
              <MentorPicker catalog={catalog} mentor={d.mentor} ch={ch} tr={tr} onPatch={patch} />
            ) : null}
            <SkillPickSelects
              slots={(d.skill_pick_slots || []).filter((slot) => slot.source_kind === "quality")}
              tr={tr}
              onPick={(key, skill) => patch({ skill_picks: { ...(ch.skill_picks || {}), [key]: skill } })}
            />
            <p className="muted">
              カルマ {d.karma.remaining} / {d.karma.pool}
              {" ・ "}不利から得られるカルマ {d.karma.negative?.used || 0}/{d.karma.negative?.max || 25}
            </p>
            {ownedQualitySpecs.length ? (
              <>
                <h3>取得済み</h3>
                {ownedQualitySpecs.map((q) => (
                  <div className="quality-item" key={`owned-${q.id}`}>
                    <div>
                      <b>{tr(q.name)}</b>
                      <div className="muted">{q.name} / {q.category === "Negative" ? "不利" : "有利"} / カルマ {q.karma}</div>
                      {q.needs_extra ? (
                        <input
                          type="text"
                          placeholder="対象（花粉、日光など）"
                          value={ch.quality_extras?.[q.id] || ""}
                          onChange={(e) => setCh({
                            ...ch,
                            quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
                          })}
                          onBlur={(e) => patch({
                            quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
                          })}
                        />
                      ) : null}
                    </div>
                    <button
                      className="btn danger"
                      onClick={() => {
                        const extras = { ...(ch.quality_extras || {}) };
                        delete extras[q.id];
                        patch({
                          quality_ids: ch.quality_ids.filter((id) => id !== q.id),
                          quality_extras: extras,
                          skill_picks: dropSkillPicksForPrefix(ch.skill_picks, [`quality:${q.id}:`]),
                        });
                      }}
                    >
                      削除
                    </button>
                  </div>
                ))}
              </>
            ) : (
              <p className="muted">まだありません。有利／不利で絞り込んで追加できます。</p>
            )}
            <div className="option-row">
              <button className={`tab ${qCat === "all" ? "active" : ""}`} onClick={() => setQCat("all")}>すべて</button>
              <button className={`tab ${qCat === "Positive" ? "active" : ""}`} onClick={() => setQCat("Positive")}>有利</button>
              <button className={`tab ${qCat === "Negative" ? "active" : ""}`} onClick={() => setQCat("Negative")}>不利</button>
            </div>
            <input type="search" placeholder="クオリティを検索" value={qSearch} onChange={(e) => setQSearch(e.target.value)} />
            <div className="quality-list">
              {filteredQualities.map((q) => {
                const added = ch.quality_ids.includes(q.id);
                const ownedWays = new Set(
                  (catalog.qualities || [])
                    .filter((item) => item.is_way && ch.quality_ids.includes(item.id))
                    .map((item) => item.name),
                );
                const replaces = !added && !!q.is_way && (q.forbidden_qualities || []).some((name) => ownedWays.has(name));
                const blocked = added ? "" : qualityBlockReason(q, qualityCtx);
                return (
                  <div className="quality-item" key={q.id}>
                    <div>
                      <b>{tr(q.name)}</b>
                      <div className="muted">
                        {q.name} / {q.category === "Negative" ? "不利" : "有利"} / カルマ {q.karma} / {q.source}
                        {q.needs_extra ? " / 対象が必要" : ""}
                        {q.is_way ? " / 他の Way と排他" : ""}
                        {replaces ? " / 追加すると両立しないクオリティを外します" : ""}
                        {blocked ? ` / ${blocked}` : ""}
                      </div>
                    </div>
                    <button
                      className={`btn ${added ? "danger" : "primary"}`}
                      disabled={!added && !!blocked}
                      onClick={() => {
                        if (added) {
                          const extras = { ...(ch.quality_extras || {}) };
                          delete extras[q.id];
                          patch({
                            quality_ids: ch.quality_ids.filter((id) => id !== q.id),
                            quality_extras: extras,
                            skill_picks: dropSkillPicksForPrefix(ch.skill_picks, [`quality:${q.id}:`]),
                          });
                          return;
                        }
                        patch({
                          quality_ids: [...ch.quality_ids, q.id],
                          skill_picks: ch.skill_picks || {},
                        });
                      }}
                    >
                      {added ? "削除" : replaces ? "入れ替え" : "追加"}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {tab === "cyber" && (
          <div className="card">
            <p className="muted">装着中 {d.cyberware?.length || 0} ・ Essence {d.essence}（サイバー −{d.essence_lost_cyber ?? 0}） ・ 消費 {((d.nuyen_spent ?? 0)).toLocaleString()}¥</p>
            {d.limb_replace ? (
              <p className="muted">
                本体 STR {d.limb_replace.str} / AGI {d.limb_replace.agi}
                （リム平均 {d.limb_replace.count}/{d.limb_replace.parts} ・ 肉 STR {d.limb_replace.meat_str} / AGI {d.limb_replace.meat_agi}）
              </p>
            ) : null}
            {d.limb_quality ? <p className="muted">{limbQualityLine(d.limb_quality)}</p> : null}
            <div className="option-row">
              <span>Redliner に含める</span>
              <label>
                <input
                  type="checkbox"
                  checked={Boolean(ch.options?.redliner_torso)}
                  onChange={(e) => patch({
                    options: {
                      redliner_torso: e.target.checked,
                      redliner_skull: Boolean(ch.options?.redliner_skull),
                    },
                  })}
                />
                胴
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={Boolean(ch.options?.redliner_skull)}
                  onChange={(e) => patch({
                    options: {
                      redliner_torso: Boolean(ch.options?.redliner_torso),
                      redliner_skull: e.target.checked,
                    },
                  })}
                />
                頭蓋
              </label>
            </div>
            {(d.cyberware || []).filter((item) => !item.parent_id).map((item) => (
              <WareRow
                key={item.id}
                item={item}
                childrenItems={(d.cyberware || []).filter((child) => child.parent_id === item.id)}
                catalogItems={catalog.cyberware.items}
                grades={catalog.cyberware.grades}
                kind="cyberware"
                tr={tr}
                slotValue={slotPick[item.id] || ""}
                wareRanges={d.ware_ranges}
                pickSlots={(d.skill_pick_slots || []).filter((slot) => slot.source_kind === "cyberware")}
                onSkillPick={(key, skill) => patch({ skill_picks: { ...(ch.skill_picks || {}), [key]: skill } })}
                onSlotChange={(wareId) => setSlotPick((cur) => ({ ...cur, [item.id]: wareId }))}
                onPatchRow={(id, next) => patch({
                  cyberware: (ch.cyberware || []).map((row) => {
                    if (row.id === id) return { ...row, ...next };
                    if (next.side && row.parent_id === id) return { ...row, side: next.side };
                    return row;
                  }),
                })}
                onRemove={(id) => {
                  const keptIds = new Set(removeWareTree(ch.cyberware || [], id).map((row) => row.id));
                  const cyberware = removeWareTree(ch.cyberware || [], id);
                  patch({
                    cyberware,
                    weapon_accessories: (ch.weapon_accessories || []).filter((row) => !row.parent_id || keptIds.has(row.parent_id)),
                    gear: (ch.gear || []).filter((row) => !row.parent_id || keptIds.has(row.parent_id)),
                    skill_picks: dropRemovedWarePicks(ch.skill_picks, [...cyberware, ...(ch.bioware || [])]),
                  });
                }}
                onAddChild={(wareId) => {
                  const spec = catalog.cyberware.items.find((w) => w.id === wareId);
                  if (!spec) return;
                  const range = wareBounds(spec, d.ware_ranges);
                  patch({
                    cyberware: [
                      ...(ch.cyberware || []),
                      { ware_id: spec.id, rating: range.min, grade: item.grade, wireless: true, parent_id: item.id },
                    ],
                  });
                }}
              />
            ))}
            <div className="cyber-toolbar">
              <input type="search" placeholder="サイバーウェアを検索" value={cySearch} onChange={(e) => setCySearch(e.target.value)} />
              <select value={cyCat} onChange={(e) => setCyCat(e.target.value)}>
                <option value="all">すべての分類</option>
                {cyberCats.map((c) => <option key={c} value={c}>{tr(c)}</option>)}
              </select>
              <select value={addGrade} onChange={(e) => setAddGrade(e.target.value)}>
                {catalog.cyberware.grades.map((g) => (
                  <option key={g.name} value={g.name}>追加時 {g.name}</option>
                ))}
              </select>
            </div>
            <div className="quality-list">
              {filteredCyber.map((w) => (
                <div className="quality-item" key={w.id}>
                  <div>
                    <b>{tr(w.name)}</b>
                    <div className="muted">{w.name} / {w.category} / ESS {w.ess}{w.plugin ? "（単独時）" : ""} / {w.cost}¥ / {w.source}{w.maxrating > 1 ? ` / 最大R${w.maxrating}` : ""}{w.plugin ? " / スロット可" : ""}</div>
                  </div>
                  <button
                    className="btn primary"
                    onClick={() => patch({
                      cyberware: [
                        ...(ch.cyberware || []),
                        {
                          ware_id: w.id,
                          rating: w.minrating || 1,
                          grade: addGrade,
                          wireless: true,
                          side: nextFreeSide(ch.cyberware || [], catalog.cyberware.items, w),
                        },
                      ],
                    })}
                  >
                    追加
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === "bio" && (
          <div className="card">
            <p className="muted">装着中 {d.bioware?.length || 0} ・ Essence {d.essence}（バイオ −{d.essence_lost_bio ?? 0}） ・ 消費 {((d.nuyen_spent ?? 0)).toLocaleString()}¥</p>
            {(d.bioware || []).filter((item) => !item.parent_id).map((item) => (
              <WareRow
                key={item.id}
                item={item}
                childrenItems={(d.bioware || []).filter((child) => child.parent_id === item.id)}
                catalogItems={catalog.bioware.items}
                grades={catalog.bioware.grades}
                kind="bioware"
                tr={tr}
                slotValue={slotPick[item.id] || ""}
                wareRanges={d.ware_ranges}
                pickSlots={(d.skill_pick_slots || []).filter((slot) => slot.source_kind === "bioware")}
                onSkillPick={(key, skill) => patch({ skill_picks: { ...(ch.skill_picks || {}), [key]: skill } })}
                onSlotChange={(wareId) => setSlotPick((cur) => ({ ...cur, [item.id]: wareId }))}
                onPatchRow={(id, next) => patch({
                  bioware: (ch.bioware || []).map((row) => {
                    if (row.id === id) return { ...row, ...next };
                    if (next.side && row.parent_id === id) return { ...row, side: next.side };
                    return row;
                  }),
                })}
                onRemove={(id) => {
                  const bioware = removeWareTree(ch.bioware || [], id);
                  patch({ bioware, skill_picks: dropRemovedWarePicks(ch.skill_picks, [...(ch.cyberware || []), ...bioware]) });
                }}
                onAddChild={(wareId) => {
                  const spec = catalog.bioware.items.find((w) => w.id === wareId);
                  if (!spec) return;
                  const range = wareBounds(spec, d.ware_ranges);
                  patch({
                    bioware: [
                      ...(ch.bioware || []),
                      { ware_id: spec.id, rating: range.min, grade: item.grade, wireless: true, parent_id: item.id },
                    ],
                  });
                }}
              />
            ))}
            <div className="cyber-toolbar">
              <input type="search" placeholder="バイオウェアを検索" value={bioSearch} onChange={(e) => setBioSearch(e.target.value)} />
              <select value={bioCat} onChange={(e) => setBioCat(e.target.value)}>
                <option value="all">すべての分類</option>
                {bioCats.map((c) => <option key={c} value={c}>{tr(c)}</option>)}
              </select>
              <select value={bioGrade} onChange={(e) => setBioGrade(e.target.value)}>
                {catalog.bioware.grades.map((g) => (
                  <option key={g.name} value={g.name}>追加時 {g.name}</option>
                ))}
              </select>
            </div>
            <div className="quality-list">
              {filteredBio.map((w) => (
                <div className="quality-item" key={w.id}>
                  <div>
                    <b>{tr(w.name)}</b>
                    <div className="muted">{w.name} / {w.category} / ESS {w.ess} / {w.cost}¥ / {w.source}{w.maxrating > 1 ? ` / 最大R${w.maxrating}` : ""}{w.allow_subsystems?.length ? " / スロット可" : ""}</div>
                  </div>
                  <button
                    className="btn primary"
                    onClick={() => {
                      const range = wareBounds(w, d.ware_ranges);
                      patch({
                        bioware: [
                          ...(ch.bioware || []),
                          {
                            ware_id: w.id,
                            rating: range.min,
                            grade: w.forcegrade || bioGrade,
                            wireless: true,
                            side: nextFreeSide(ch.bioware || [], catalog.bioware.items, w),
                          },
                        ],
                      });
                    }}
                  >
                    追加
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {tab === "gear" && (
          <div className="card">
            <p className="muted">
              作成時の購入。防具は装備中の本体1着＋ヘルメット等の加算、ウェア装甲と合算。消費 {(d.nuyen_spent ?? 0).toLocaleString()}¥
              {d.worn_armor ? ` ・ 装備 ${tr(d.worn_armor)}` : ""}
              {d.lifestyle ? ` ・ ${tr(d.lifestyle.name)} ${d.lifestyle.months}${lifeIncrement(d.lifestyle.increment)}` : ""}
              {d.commlink ? ` ・ ${tr(d.commlink.name)} DR${d.commlink.device_rating}` : ""}
              {d.cyberdeck ? ` ・ ${tr(d.cyberdeck.name)} DR${d.cyberdeck.device_rating}` : ""}
              {d.rcc ? ` ・ ${tr(d.rcc.name)} DR${d.rcc.device_rating}` : ""}
            </p>
            <div className="option-row">
              {([
                ["armor", "防具"],
                ["weapon", "武器"],
                ["commlink", "通信機"],
                ["cyberdeck", "サイバーデッキ"],
                ["rcc", "RCC"],
                ["optics", "視覚／聴覚"],
                ["sensor", "センサー"],
                ["vehicle", "車両"],
                ["drone", "ドローン"],
                ["misc", "ギア"],
                ["lifestyle", "ライフスタイル"],
              ] as const).map(([kind, label]) => (
                <button
                  key={kind}
                  className={`tab ${gearKind === kind ? "active" : ""}`}
                  onClick={() => { setGearKind(kind); setGearCat("all"); setGearSearch(""); }}
                >
                  {label}
                </button>
              ))}
            </div>

            {gearKind === "armor" && (
              <>
                {(d.armor_items || []).map((item) => {
                  const installedNames = (item.mods || []).map((mod) => mod.name);
                  const parentCost = (catalog.armor || []).find((row) => row.id === item.armor_id)?.cost;
                  const addons = (catalog.armor_mods || []).filter((mod) => (
                    armorModFits(mod, item, installedNames)
                    && !(item.mods || []).some((row) => row.mod_id === mod.id || (mod.unique && row.unique === mod.unique))
                  ));
                  const specialLine = specialArmorLine(mergeSpecialArmor(item.mods));
                  return (
                  <div className="cyber-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / 装甲 {item.armor_value}
                        {item.equipped ? ` ・ 加算 ${item.contributes}` : " ・ 未装備"}
                        {specialLine ? ` / ${specialLine}` : ""}
                        {availBit(item)}
                        {item.capacity_max ? ` / 容量 ${item.capacity_used}/${item.capacity_max}` : ""}
                        {" / "}{item.nuyen.toLocaleString()}¥ / {item.source}
                      </div>
                      <div className="cyber-controls">
                        <label>
                          <input
                            type="checkbox"
                            checked={item.equipped}
                            onChange={(e) => patch({
                              armor: (ch.armor || []).map((row) => (
                                row.id === item.id ? { ...row, equipped: e.target.checked } : row
                              )),
                            })}
                          />
                          装備
                        </label>
                        {item.rating_max > 0 ? (
                          <label>
                            Rating
                            <input
                              type="number"
                              min={1}
                              max={item.rating_max}
                              value={item.rating}
                              onChange={(e) => patch({
                                armor: (ch.armor || []).map((row) => (
                                  row.id === item.id ? { ...row, rating: Number(e.target.value) } : row
                                )),
                              })}
                            />
                          </label>
                        ) : null}
                      </div>
                      {(item.mods || []).map((mod) => (
                        <div className="muted" key={mod.id} style={{ marginTop: 6 }}>
                          {tr(mod.name)}
                          {mod.rating_max > 1 ? ` R${mod.rating}` : ""}
                          {mod.included ? " / 付属" : ` / ${mod.nuyen.toLocaleString()}¥`}
                          {mod.capacity_cost ? ` / 容量 ${mod.capacity_cost < 0 ? `+${-mod.capacity_cost}` : mod.capacity_cost}` : ""}
                          {specialArmorLine(mod.special_armor) ? ` / ${specialArmorLine(mod.special_armor)}` : ""}
                          {limitModifierLine(mod.limit_modifiers) ? ` / ${limitModifierLine(mod.limit_modifiers)}` : ""}
                          {availBit(mod)}
                          {mod.included ? null : (
                            <>
                              {" "}
                              <button className="btn danger" onClick={() => patch({
                                armor_mods: (ch.armor_mods || []).filter((row) => row.id !== mod.id),
                              })}>外す</button>
                            </>
                          )}
                          {mod.rating_max > 1 && !mod.included ? (
                            <label>
                              Rating
                              <input
                                type="number"
                                min={1}
                                max={mod.rating_max}
                                value={mod.rating}
                                onChange={(e) => patch({
                                  armor_mods: (ch.armor_mods || []).map((row) => (
                                    row.id === mod.id ? { ...row, rating: Number(e.target.value) } : row
                                  )),
                                })}
                              />
                            </label>
                          ) : null}
                        </div>
                      ))}
                      {addons.length ? (
                        <div className="cyber-controls">
                          <select
                            value={slotPick[item.id] || ""}
                            onChange={(e) => setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
                          >
                            <option value="">改造を追加</option>
                            {addons
                              .filter((mod) => gearSearch.trim() || mod.source === "SR5")
                              .map((mod) => (
                                <option key={mod.id} value={mod.id}>{tr(mod.name)} ({formatAccessoryCost(mod.cost, parentCost)})</option>
                              ))}
                          </select>
                          <button
                            className="btn"
                            disabled={!slotPick[item.id]}
                            onClick={() => {
                              const wareId = slotPick[item.id];
                              const spec = addons.find((mod) => mod.id === wareId);
                              if (!spec) return;
                              patch({
                                armor_mods: [...(ch.armor_mods || []), {
                                  mod_id: spec.id,
                                  parent_id: item.id,
                                  rating: Math.max(1, spec.minrating || 1),
                                }],
                              });
                              setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
                            }}
                          >
                            装着
                          </button>
                        </div>
                      ) : null}
                    </div>
                    <button className="btn danger" onClick={() => patch({
                      armor: (ch.armor || []).filter((row) => row.id !== item.id),
                      armor_mods: (ch.armor_mods || []).filter((row) => row.parent_id !== item.id),
                    })}>削除</button>
                  </div>
                  );
                })}
              </>
            )}

            {gearKind === "weapon" && (
              <>
                {(d.weapons || []).map((item) => {
                  const installedNames = (item.accessories || []).map((acc) => acc.name);
                  const parentCost = (catalog.weapons || []).find((row) => row.id === item.weapon_id)?.cost;
                  const addons = (catalog.weapon_accessories || []).filter((mod) => (
                    accessoryFits(mod, item, installedNames)
                    && !(item.accessories || []).some((acc) => acc.accessory_id === mod.id)
                  ));
                  const ammoKey = `${item.id}-ammo`;
                  const ammoAddons = (catalog.gear || []).filter((mod) => (
                    ammoFits(mod, item)
                    && !(item.ammo_gear || []).some((row) => row.gear_id === mod.id)
                  ));
                  const fromGear = Boolean(item.from_gear && item.source_gear_id);
                  const fromWare = Boolean(item.from_ware && item.source_ware_id);
                  return (
                  <div className="cyber-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / {weaponLine(item)} / {item.nuyen.toLocaleString()}¥{availBit(item)} / {item.source}
                        {fromGear ? " / ギア連動" : ""}
                        {fromWare ? " / ウェア連動" : ""}
                        {item.limb_str != null ? ` / 肢 STR ${item.limb_str}` : ""}
                        {item.useskill ? ` / ${item.useskill}` : ""}
                        {item.focus_dice ? ` / フォーカス+${item.focus_dice}` : ""}
                        {item.mounted_label ? ` / 搭載 ${tr(item.mounted_label)}` : ""}
                      </div>
                      {fromWare ? null : (
                      <div className="cyber-controls">
                        <label>
                          数量
                          <input
                            type="number"
                            min={1}
                            value={item.qty}
                            onChange={(e) => {
                              const qty = Number(e.target.value);
                              if (fromGear) {
                                patch({
                                  gear: (ch.gear || []).map((row) => (
                                    row.id === item.source_gear_id ? { ...row, qty } : row
                                  )),
                                });
                                return;
                              }
                              patch({
                                weapons: (ch.weapons || []).map((row) => (
                                  row.id === item.id ? { ...row, qty } : row
                                )),
                              });
                            }}
                          />
                        </label>
                      </div>
                      )}
                      {(item.accessories || []).map((acc) => (
                        <div className="muted" key={acc.id} style={{ marginTop: 6 }}>
                          {tr(acc.name)}
                          {acc.mount ? ` / ${acc.mount}` : ""}
                          {acc.included ? " / 付属" : ` / ${acc.nuyen.toLocaleString()}¥`}
                          {availBit(acc)}
                          {availBit(acc)}
                          {acc.included ? null : (
                            <>
                              {" "}
                              <button className="btn danger" onClick={() => patch({
                                weapon_accessories: (ch.weapon_accessories || []).filter((row) => row.id !== acc.id),
                              })}>外す</button>
                            </>
                          )}
                        </div>
                      ))}
                      {!fromGear && addons.length ? (
                        <div className="cyber-controls">
                          <select
                            value={slotPick[item.id] || ""}
                            onChange={(e) => setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
                          >
                            <option value="">アクセサリを追加</option>
                            {addons
                              .filter((mod) => mod.source === "SR5")
                              .map((mod) => (
                                <option key={mod.id} value={mod.id}>{tr(mod.name)} ({formatAccessoryCost(mod.cost, parentCost)})</option>
                              ))}
                          </select>
                          <button
                            className="btn"
                            disabled={!slotPick[item.id]}
                            onClick={() => {
                              const wareId = slotPick[item.id];
                              const spec = addons.find((mod) => mod.id === wareId);
                              if (!spec) return;
                              patch({
                                weapon_accessories: [...(ch.weapon_accessories || []), { accessory_id: spec.id, parent_id: item.id }],
                              });
                              setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
                            }}
                          >
                            装着
                          </button>
                        </div>
                      ) : null}
                      {(item.ammo_gear || []).map((ammo) => (
                        <div className="muted" key={ammo.id} style={{ marginTop: 6 }}>
                          {tr(ammo.label || ammo.name)}
                          {ammo.loaded ? " / 装填中" : ""}
                          {ammo.qty > 1 ? ` ×${ammo.qty}` : ""}
                          {ammo.costfor ? ` / ${(ammo.costfor * ammo.qty).toLocaleString()}発` : ""}
                          {` / ${ammo.nuyen.toLocaleString()}¥`}
                          {" "}
                          {(ammo.ammo_weapon_types || []).length > 0 && !ammo.loaded ? (
                            <button className="btn" onClick={() => patch({
                              weapons: (ch.weapons || []).map((row) => (
                                row.id === item.id ? { ...row, loaded_ammo_id: ammo.id } : row
                              )),
                            })}>装填</button>
                          ) : null}
                          <button className="btn danger" onClick={() => patch({
                            gear: dropTree(ch.gear || [], ammo.id),
                            weapons: (ch.weapons || []).map((row) => (
                              row.id === item.id && row.loaded_ammo_id === ammo.id
                                ? { ...row, loaded_ammo_id: undefined }
                                : row
                            )),
                          })}>外す</button>
                          <label>
                            数量
                            <input
                              type="number"
                              min={1}
                              max={99}
                              value={ammo.qty}
                              onChange={(e) => patch({
                                gear: (ch.gear || []).map((row) => (
                                  row.id === ammo.id ? { ...row, qty: Number(e.target.value) } : row
                                )),
                              })}
                            />
                          </label>
                        </div>
                      ))}
                      {!fromGear && ammoAddons.length ? (
                        <div className="cyber-controls">
                          <select
                            value={slotPick[ammoKey] || ""}
                            onChange={(e) => setSlotPick((cur) => ({ ...cur, [ammoKey]: e.target.value }))}
                          >
                            <option value="">弾薬を追加</option>
                            {ammoAddons
                              .filter((mod) => mod.source === "SR5")
                              .map((mod) => (
                                <option key={mod.id} value={mod.id}>{tr(mod.name)} ({formatAmmoCost(mod.cost, mod.costfor)})</option>
                              ))}
                          </select>
                          <button
                            className="btn"
                            disabled={!slotPick[ammoKey]}
                            onClick={() => {
                              const wareId = slotPick[ammoKey];
                              const spec = ammoAddons.find((mod) => mod.id === wareId);
                              if (!spec) return;
                              patch({
                                gear: [...(ch.gear || []), {
                                  gear_id: spec.id,
                                  rating: Math.max(1, spec.minrating || 1),
                                  parent_id: item.id,
                                }],
                              });
                              setSlotPick((cur) => ({ ...cur, [ammoKey]: "" }));
                            }}
                          >
                            装着
                          </button>
                        </div>
                      ) : null}
                    </div>
                    <button className="btn danger" onClick={() => {
                      if (fromGear) {
                        patch({
                          gear: dropTree(ch.gear || [], item.source_gear_id || item.id),
                        });
                        return;
                      }
                      if (fromWare) {
                        patch({
                          cyberware: removeWareTree(ch.cyberware || [], item.source_ware_id || item.id),
                          weapon_accessories: (ch.weapon_accessories || []).filter((row) => row.parent_id !== item.id),
                          gear: (ch.gear || []).filter((row) => row.parent_id !== item.id),
                        });
                        return;
                      }
                      patch({
                        weapons: (ch.weapons || []).filter((row) => row.id !== item.id),
                        weapon_accessories: (ch.weapon_accessories || []).filter((row) => row.parent_id !== item.id),
                        gear: (ch.gear || []).filter((row) => row.parent_id !== item.id),
                      });
                    }}>削除</button>
                  </div>
                  );
                })}
              </>
            )}

            {gearKind === "commlink" && (
              <>
                {(d.commlinks || []).map((item) => (
                  <div className="cyber-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name}
                        {item.category && item.category !== "Commlinks" ? ` / ${tr(item.category)}` : ""}
                        {" / "}DR {item.device_rating} / DP {item.dataprocessing} / FW {item.firewall} / {item.nuyen.toLocaleString()}¥ / {item.source}
                      </div>
                      {item.rating_max > 0 ? (
                        <div className="cyber-controls">
                          <label>
                            Rating
                            <input
                              type="number"
                              min={1}
                              max={item.rating_max}
                              value={item.rating}
                              onChange={(e) => patch({
                                commlinks: (ch.commlinks || []).map((row) => (
                                  row.id === item.id ? { ...row, rating: Number(e.target.value) } : row
                                )),
                              })}
                            />
                          </label>
                        </div>
                      ) : null}
                      {(d.apps || []).filter((app) => app.parent_id === item.id).map((app) => (
                        <div className="muted" key={app.id} style={{ marginTop: 6 }}>
                          {tr(app.label || app.name)}
                          {app.nuyen ? ` / ${app.nuyen.toLocaleString()}¥` : ""}
                          {" "}
                          <button className="btn danger" onClick={() => patch({
                            apps: (ch.apps || []).filter((row) => row.id !== app.id),
                          })}>外す</button>
                          {app.rating_max > 0 ? (
                            <label>
                              Rating
                              <input
                                type="number"
                                min={1}
                                max={app.rating_max}
                                value={app.rating}
                                onChange={(e) => patch({
                                  apps: (ch.apps || []).map((row) => (
                                    row.id === app.id ? { ...row, rating: Number(e.target.value) } : row
                                  )),
                                })}
                              />
                            </label>
                          ) : null}
                          {app.extra_kind === "skill" ? (
                            <label>
                              スキル
                              <select
                                value={app.extra || ""}
                                onChange={(e) => patch({
                                  apps: (ch.apps || []).map((row) => (
                                    row.id === app.id ? { ...row, extra: e.target.value } : row
                                  )),
                                })}
                              >
                                <option value="">選択</option>
                                {(app.extra_options || []).map((name) => (
                                  <option key={name} value={name}>{tr(name)}</option>
                                ))}
                              </select>
                            </label>
                          ) : null}
                          {app.extra_kind === "text" ? (
                            <label>
                              対象
                              <input
                                value={app.extra || ""}
                                onChange={(e) => patch({
                                  apps: (ch.apps || []).map((row) => (
                                    row.id === app.id ? { ...row, extra: e.target.value } : row
                                  )),
                                })}
                              />
                            </label>
                          ) : null}
                        </div>
                      ))}
                      <div className="cyber-controls">
                        <select
                          value={slotPick[item.id] || ""}
                          onChange={(e) => setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
                        >
                          <option value="">アプリを追加</option>
                          {(catalog.apps || [])
                            .filter((app) => app.source === "SR5")
                            .filter((app) => app.needs_extra || !(d.apps || []).some((row) => row.parent_id === item.id && row.gear_id === app.id))
                            .map((app) => (
                              <option key={app.id} value={app.id}>{tr(app.name)} ({app.cost}¥)</option>
                            ))}
                        </select>
                        {(() => {
                          const spec = (catalog.apps || []).find((app) => app.id === slotPick[item.id]);
                          if (spec?.extra_kind !== "skill") return null;
                          return (
                            <select
                              value={extraPick[item.id] || ""}
                              onChange={(e) => setExtraPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
                            >
                              <option value="">スキル</option>
                              {(spec.extra_options || []).map((name) => (
                                <option key={name} value={name}>{tr(name)}</option>
                              ))}
                            </select>
                          );
                        })()}
                        <button
                          className="btn"
                          disabled={!slotPick[item.id]}
                          onClick={() => {
                            const wareId = slotPick[item.id];
                            const spec = (catalog.apps || []).find((app) => app.id === wareId);
                            if (!spec) return;
                            patch({
                              apps: [...(ch.apps || []), {
                                gear_id: spec.id,
                                rating: Math.max(1, spec.minrating || 1),
                                parent_id: item.id,
                                extra: extraPick[item.id] || undefined,
                              }],
                            });
                            setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
                            setExtraPick((cur) => ({ ...cur, [item.id]: "" }));
                          }}
                        >
                          装着
                        </button>
                      </div>
                      {(d.gear || []).filter((acc) => acc.parent_id === item.id).map((acc) => (
                        <div className="muted" key={acc.id} style={{ marginTop: 6 }}>
                          {tr(acc.label || acc.name)}
                          {acc.included ? " / 付属" : ` / ${acc.nuyen.toLocaleString()}¥`}
                          {" "}
                          <button className="btn danger" onClick={() => patch({
                            gear: dropTree(ch.gear || [], acc.id),
                          })}>外す</button>
                        </div>
                      ))}
                      <div className="cyber-controls">
                        <select
                          value={slotPick[`${item.id}-acc`] || ""}
                          onChange={(e) => setSlotPick((cur) => ({ ...cur, [`${item.id}-acc`]: e.target.value }))}
                        >
                          <option value="">アクセサリを追加</option>
                          {(catalog.gear || [])
                            .filter((mod) => (
                              mod.category === "Commlink Accessories"
                              || (mod.required_categories || []).includes("Commlinks")
                              || (item.category === "PI-Tac" && mod.category === "PI-Tac Programs")
                            ))
                            .filter((mod) => (
                              gearSearch.trim()
                              || mod.source === "SR5"
                              || (item.category === "PI-Tac" && mod.category === "PI-Tac Programs")
                            ))
                            .filter((mod) => !(d.gear || []).some((row) => row.parent_id === item.id && row.gear_id === mod.id))
                            .map((mod) => (
                              <option key={mod.id} value={mod.id}>{tr(mod.name)} ({mod.cost}¥)</option>
                            ))}
                        </select>
                        <button
                          className="btn"
                          disabled={!slotPick[`${item.id}-acc`]}
                          onClick={() => {
                            const wareId = slotPick[`${item.id}-acc`];
                            const spec = (catalog.gear || []).find((mod) => mod.id === wareId);
                            if (!spec) return;
                            patch({
                              gear: [...(ch.gear || []), {
                                gear_id: spec.id,
                                rating: Math.max(1, spec.minrating || 1),
                                parent_id: item.id,
                              }],
                            });
                            setSlotPick((cur) => ({ ...cur, [`${item.id}-acc`]: "" }));
                          }}
                        >
                          装着
                        </button>
                      </div>
                    </div>
                    <button className="btn danger" onClick={() => patch({
                      commlinks: (ch.commlinks || []).filter((row) => row.id !== item.id),
                      apps: (ch.apps || []).filter((row) => row.parent_id !== item.id),
                      gear: dropTree(ch.gear || [], item.id),
                    })}>削除</button>
                  </div>
                ))}
              </>
            )}

            {gearKind === "cyberdeck" && (
              <>
                {(d.cyberdecks || []).length ? (
                  <p className="muted">作成時に配列の4数を ATK / SLZ / DP / FW へ割り当てます。値を選ぶと、その数値を持っていた項目と入れ替わります。</p>
                ) : null}
                {(d.cyberdecks || []).map((item) => (
                  <div className="cyber-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / DR {item.device_rating} / ATK {item.attack} / SLZ {item.sleaze} / DP {item.dataprocessing} / FW {item.firewall} / プログラム {item.program_used ?? 0}/{item.program_max ?? item.programs ?? 0} / {item.nuyen.toLocaleString()}¥ / {item.source}
                      </div>
                      {item.rating_max > 0 ? (
                        <div className="cyber-controls">
                          <label>
                            Rating
                            <input
                              type="number"
                              min={1}
                              max={item.rating_max}
                              value={item.rating}
                              onChange={(e) => patch({
                                cyberdecks: (ch.cyberdecks || []).map((row) => (
                                  row.id === item.id ? { ...row, rating: Number(e.target.value) } : row
                                )),
                              })}
                            />
                          </label>
                        </div>
                      ) : null}
                      {item.can_reorder && (item.array || []).length === 4 ? (
                        <div className="matrix-array">
                          {MATRIX_ATTRS.map(([key, label]) => (
                            <label key={key}>
                              {label}
                              <select
                                value={String((item.array_order || DEFAULT_ARRAY_ORDER).indexOf(key))}
                                onChange={(e) => patch({
                                  cyberdecks: (ch.cyberdecks || []).map((row) => (
                                    row.id === item.id
                                      ? { ...row, array_order: swapMatrixOrder(item.array_order, key, Number(e.target.value)) }
                                      : row
                                  )),
                                })}
                              >
                                {(item.array || []).map((n, i) => (
                                  <option key={`${key}-${i}`} value={i}>{n}</option>
                                ))}
                              </select>
                            </label>
                          ))}
                        </div>
                      ) : null}
                      {(d.programs || []).filter((prog) => prog.parent_id === item.id).map((prog) => (
                        <div className="muted" key={prog.id} style={{ marginTop: 6 }}>
                          {tr(prog.name)}
                          {prog.rating_max > 0 ? ` R${prog.rating}` : ""}
                          {` / ${prog.nuyen.toLocaleString()}¥`}
                          {" "}
                          <button className="btn danger" onClick={() => patch({
                            programs: (ch.programs || []).filter((row) => row.id !== prog.id),
                          })}>外す</button>
                          {prog.rating_max > 0 ? (
                            <label>
                              Rating
                              <input
                                type="number"
                                min={1}
                                max={prog.rating_max}
                                value={prog.rating}
                                onChange={(e) => patch({
                                  programs: (ch.programs || []).map((row) => (
                                    row.id === prog.id ? { ...row, rating: Number(e.target.value) } : row
                                  )),
                                })}
                              />
                            </label>
                          ) : null}
                        </div>
                      ))}
                      <div className="cyber-controls">
                        <select
                          value={slotPick[item.id] || ""}
                          onChange={(e) => setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
                        >
                          <option value="">プログラムを追加</option>
                          {(catalog.programs || [])
                            .filter((prog) => prog.program_host === "cyberdecks")
                            .filter((prog) => !(d.programs || []).some((row) => row.parent_id === item.id && row.gear_id === prog.id))
                            .filter((prog) => prog.source === "SR5")
                            .map((prog) => (
                              <option key={prog.id} value={prog.id}>{tr(prog.name)} ({prog.cost}¥)</option>
                            ))}
                        </select>
                        <button
                          className="btn"
                          disabled={!slotPick[item.id]}
                          onClick={() => {
                            const wareId = slotPick[item.id];
                            const spec = (catalog.programs || []).find((prog) => prog.id === wareId);
                            if (!spec) return;
                            patch({
                              programs: [...(ch.programs || []), { gear_id: spec.id, rating: Math.max(1, spec.minrating || 1), parent_id: item.id }],
                            });
                            setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
                          }}
                        >
                          装着
                        </button>
                      </div>
                    </div>
                    <button className="btn danger" onClick={() => patch({
                      cyberdecks: (ch.cyberdecks || []).filter((row) => row.id !== item.id),
                      programs: (ch.programs || []).filter((row) => row.parent_id !== item.id),
                    })}>削除</button>
                  </div>
                ))}
              </>
            )}

            {gearKind === "rcc" && (
              <>
                {(d.rccs || []).map((item) => (
                  <div className="cyber-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / DR {item.device_rating} / DP {item.dataprocessing} / FW {item.firewall} / プログラム {item.program_used ?? 0}/{item.program_max ?? item.programs ?? 0} / {item.nuyen.toLocaleString()}¥ / {item.source}
                      </div>
                      {item.rating_max > 0 ? (
                        <div className="cyber-controls">
                          <label>
                            Rating
                            <input
                              type="number"
                              min={1}
                              max={item.rating_max}
                              value={item.rating}
                              onChange={(e) => patch({
                                rccs: (ch.rccs || []).map((row) => (
                                  row.id === item.id ? { ...row, rating: Number(e.target.value) } : row
                                )),
                              })}
                            />
                          </label>
                        </div>
                      ) : null}
                      {(d.programs || []).filter((prog) => prog.parent_id === item.id).map((prog) => (
                        <div className="muted" key={prog.id} style={{ marginTop: 6 }}>
                          {tr(prog.label || prog.name)}
                          {prog.rating_max > 0 ? ` R${prog.rating}` : ""}
                          {` / ${prog.nuyen.toLocaleString()}¥`}
                          {" "}
                          <button className="btn danger" onClick={() => patch({
                            programs: (ch.programs || []).filter((row) => row.id !== prog.id),
                          })}>外す</button>
                          {prog.rating_max > 0 ? (
                            <label>
                              Rating
                              <input
                                type="number"
                                min={1}
                                max={prog.rating_max}
                                value={prog.rating}
                                onChange={(e) => patch({
                                  programs: (ch.programs || []).map((row) => (
                                    row.id === prog.id ? { ...row, rating: Number(e.target.value) } : row
                                  )),
                                })}
                              />
                            </label>
                          ) : null}
                          {prog.extra_kind === "skill" ? (
                            <label>
                              スキル
                              <select
                                value={prog.extra || ""}
                                onChange={(e) => patch({
                                  programs: (ch.programs || []).map((row) => (
                                    row.id === prog.id ? { ...row, extra: e.target.value } : row
                                  )),
                                })}
                              >
                                <option value="">選択</option>
                                {(prog.extra_options || []).map((name) => (
                                  <option key={name} value={name}>{tr(name)}</option>
                                ))}
                              </select>
                            </label>
                          ) : null}
                          {prog.extra_kind === "group" ? (
                            <label>
                              グループ
                              <select
                                value={prog.extra || ""}
                                onChange={(e) => patch({
                                  programs: (ch.programs || []).map((row) => (
                                    row.id === prog.id ? { ...row, extra: e.target.value } : row
                                  )),
                                })}
                              >
                                <option value="">選択</option>
                                {(prog.extra_options || []).map((name) => (
                                  <option key={name} value={name}>{tr(name)}</option>
                                ))}
                              </select>
                            </label>
                          ) : null}
                          {prog.extra_kind === "text" ? (
                            <label>
                              対象
                              <input
                                list={`prog-extra-${prog.id}`}
                                value={prog.extra || ""}
                                onChange={(e) => patch({
                                  programs: (ch.programs || []).map((row) => (
                                    row.id === prog.id ? { ...row, extra: e.target.value } : row
                                  )),
                                })}
                              />
                              <datalist id={`prog-extra-${prog.id}`}>
                                {(prog.extra_options || []).slice(0, 80).map((name) => (
                                  <option key={name} value={name} />
                                ))}
                              </datalist>
                            </label>
                          ) : null}
                        </div>
                      ))}
                      <div className="cyber-controls">
                        <select
                          value={slotPick[item.id] || ""}
                          onChange={(e) => {
                            setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }));
                            setExtraPick((cur) => ({ ...cur, [item.id]: "" }));
                          }}
                        >
                          <option value="">オートソフトを追加</option>
                          {(catalog.programs || [])
                            .filter((prog) => prog.program_host === "rccs")
                            .filter((prog) => prog.source === "SR5" || prog.source === "R5")
                            .filter((prog) => prog.needs_extra || !(d.programs || []).some((row) => row.parent_id === item.id && row.gear_id === prog.id))
                            .map((prog) => (
                              <option key={prog.id} value={prog.id}>{tr(prog.name)} ({prog.cost}¥)</option>
                            ))}
                        </select>
                        {(() => {
                          const spec = (catalog.programs || []).find((prog) => prog.id === slotPick[item.id]);
                          if (spec?.extra_kind === "skill" || spec?.extra_kind === "group") {
                            return (
                              <select
                                value={extraPick[item.id] || ""}
                                onChange={(e) => setExtraPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
                              >
                                <option value="">{spec.extra_kind === "group" ? "グループ" : "スキル"}</option>
                                {(spec.extra_options || []).map((name) => (
                                  <option key={name} value={name}>{tr(name)}</option>
                                ))}
                              </select>
                            );
                          }
                          if (spec?.extra_kind === "text") {
                            return (
                              <>
                                <input
                                  list={`pick-extra-${item.id}`}
                                  placeholder="対象"
                                  value={extraPick[item.id] || ""}
                                  onChange={(e) => setExtraPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
                                />
                                <datalist id={`pick-extra-${item.id}`}>
                                  {(spec.extra_options || []).slice(0, 80).map((name) => (
                                    <option key={name} value={name} />
                                  ))}
                                </datalist>
                              </>
                            );
                          }
                          return null;
                        })()}
                        <button
                          className="btn"
                          disabled={!slotPick[item.id]}
                          onClick={() => {
                            const wareId = slotPick[item.id];
                            const spec = (catalog.programs || []).find((prog) => prog.id === wareId);
                            if (!spec) return;
                            patch({
                              programs: [...(ch.programs || []), {
                                gear_id: spec.id,
                                rating: Math.max(1, spec.minrating || 1),
                                parent_id: item.id,
                                extra: extraPick[item.id] || undefined,
                              }],
                            });
                            setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
                            setExtraPick((cur) => ({ ...cur, [item.id]: "" }));
                          }}
                        >
                          装着
                        </button>
                      </div>
                    </div>
                    <button className="btn danger" onClick={() => patch({
                      rccs: (ch.rccs || []).filter((row) => row.id !== item.id),
                      programs: (ch.programs || []).filter((row) => row.parent_id !== item.id),
                    })}>削除</button>
                  </div>
                ))}
              </>
            )}

            {gearKind === "optics" && (
              <>
                {(d.optics || []).filter((item) => !item.parent_id).map((item) => {
                  const childrenItems = (d.optics || []).filter((child) => child.parent_id === item.id);
                  const addons = (catalog.optics || []).filter((mod) => (
                    (item.addoncategories || []).includes(mod.category) && Boolean(mod.requireparent)
                  ));
                  return (
                    <div className="cyber-item" key={item.id}>
                      <div>
                        <b>{tr(item.name)}</b>
                        <div className="muted">
                          {item.name} / {tr(item.category)}
                          {item.capacity_max ? ` / 容量 ${item.capacity_used}/${item.capacity_max}` : ""}
                          {" / "}{item.nuyen.toLocaleString()}¥ / {item.source}
                        </div>
                        {item.rating_max > 0 ? (
                          <div className="cyber-controls">
                            <label>
                              Rating
                              <input
                                type="number"
                                min={1}
                                max={item.rating_max}
                                value={item.rating}
                                onChange={(e) => patch({
                                  optics: (ch.optics || []).map((row) => (
                                    row.id === item.id ? { ...row, rating: Number(e.target.value) } : row
                                  )),
                                })}
                              />
                            </label>
                          </div>
                        ) : null}
                        {childrenItems.map((child) => (
                          <div className="muted" key={child.id} style={{ marginTop: 6 }}>
                            {tr(child.name)}
                            {child.rating_max > 0 ? ` R${child.rating}` : ""}
                            {child.included ? " / 付属" : ` / ${child.nuyen.toLocaleString()}¥`}
                            {child.capacity_cost ? ` / 容量 ${child.capacity_cost}` : ""}
                            {child.included ? null : (
                              <>
                                {" "}
                                <button className="btn danger" onClick={() => patch({
                                  optics: (ch.optics || []).filter((row) => row.id !== child.id),
                                })}>外す</button>
                              </>
                            )}
                            {child.rating_max > 0 && !child.included ? (
                              <label>
                                Rating
                                <input
                                  type="number"
                                  min={1}
                                  max={child.rating_max}
                                  value={child.rating}
                                  onChange={(e) => patch({
                                    optics: (ch.optics || []).map((row) => (
                                      row.id === child.id ? { ...row, rating: Number(e.target.value) } : row
                                    )),
                                  })}
                                />
                              </label>
                            ) : null}
                          </div>
                        ))}
                        {addons.length ? (
                          <div className="cyber-controls">
                            <select
                              value={slotPick[item.id] || ""}
                              onChange={(e) => setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
                            >
                              <option value="">改造を追加</option>
                              {addons
                                .filter((mod) => !childrenItems.some((child) => child.gear_id === mod.id))
                                .map((mod) => (
                                  <option key={mod.id} value={mod.id}>{tr(mod.name)} ({mod.cost}¥)</option>
                                ))}
                            </select>
                            <button
                              className="btn"
                              disabled={!slotPick[item.id]}
                              onClick={() => {
                                const wareId = slotPick[item.id];
                                const spec = addons.find((mod) => mod.id === wareId);
                                if (!spec) return;
                                patch({
                                  optics: [...(ch.optics || []), { gear_id: spec.id, rating: Math.max(1, spec.minrating || 1), parent_id: item.id }],
                                });
                                setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
                              }}
                            >
                              装着
                            </button>
                          </div>
                        ) : null}
                      </div>
                      <button className="btn danger" onClick={() => {
                        const drop = new Set<string>([item.id]);
                        let grew = true;
                        const rows = ch.optics || [];
                        while (grew) {
                          grew = false;
                          for (const row of rows) {
                            if (row.parent_id && drop.has(row.parent_id) && row.id && !drop.has(row.id)) {
                              drop.add(row.id);
                              grew = true;
                            }
                          }
                        }
                        patch({ optics: rows.filter((row) => !row.id || !drop.has(row.id)) });
                      }}>削除</button>
                    </div>
                  );
                })}
              </>
            )}

            {gearKind === "sensor" && (
              <>
                {(d.sensors || []).filter((item) => !item.parent_id).map((item) => {
                  const childrenItems = (d.sensors || []).filter((child) => child.parent_id === item.id);
                  const addons = (catalog.sensors || []).filter((mod) => (
                    (item.addoncategories || []).includes(mod.category) && mod.category !== "Custom"
                  ));
                  return (
                    <div className="cyber-item" key={item.id}>
                      <div>
                        <b>{tr(item.name)}</b>
                        <div className="muted">
                          {item.name} / {tr(item.category)}
                          {deviceRatingBit(item)}
                          {item.capacity_max ? ` / 容量 ${item.capacity_used}/${item.capacity_max}` : ""}
                          {" / "}{item.nuyen.toLocaleString()}¥ / {item.source}
                        </div>
                        {item.rating_max > 0 ? (
                          <div className="cyber-controls">
                            <label>
                              Rating
                              <input
                                type="number"
                                min={1}
                                max={item.rating_max}
                                value={item.rating}
                                onChange={(e) => patch({
                                  sensors: (ch.sensors || []).map((row) => (
                                    row.id === item.id ? { ...row, rating: Number(e.target.value) } : row
                                  )),
                                })}
                              />
                            </label>
                          </div>
                        ) : null}
                        {childrenItems.map((child) => (
                          <div className="muted" key={child.id} style={{ marginTop: 6 }}>
                            {tr(child.name)}
                            {child.rating_max > 0 ? ` R${child.rating}` : ""}
                            {child.included ? " / 付属" : ` / ${child.nuyen.toLocaleString()}¥`}
                            {child.capacity_cost ? ` / 容量 ${child.capacity_cost}` : ""}
                            {child.included ? null : (
                              <>
                                {" "}
                                <button className="btn danger" onClick={() => patch({
                                  sensors: dropTree(ch.sensors || [], child.id),
                                })}>外す</button>
                              </>
                            )}
                            {child.rating_max > 0 && !child.included ? (
                              <label>
                                Rating
                                <input
                                  type="number"
                                  min={1}
                                  max={child.rating_max}
                                  value={child.rating}
                                  onChange={(e) => patch({
                                    sensors: (ch.sensors || []).map((row) => (
                                      row.id === child.id ? { ...row, rating: Number(e.target.value) } : row
                                    )),
                                  })}
                                />
                              </label>
                            ) : null}
                            {(d.sensors || []).filter((grand) => grand.parent_id === child.id).map((grand) => (
                              <div key={grand.id} style={{ marginTop: 4, marginLeft: 12 }}>
                                {tr(grand.name)}
                                {grand.capacity_cost ? ` / 容量 ${grand.capacity_cost}` : ""}
                                {" "}
                                <button className="btn danger" onClick={() => patch({
                                  sensors: (ch.sensors || []).filter((row) => row.id !== grand.id),
                                })}>外す</button>
                              </div>
                            ))}
                            {(child.addoncategories || []).length ? (
                              <div className="cyber-controls">
                                <select
                                  value={slotPick[child.id] || ""}
                                  onChange={(e) => setSlotPick((cur) => ({ ...cur, [child.id]: e.target.value }))}
                                >
                                  <option value="">機能を追加</option>
                                  {(catalog.sensors || [])
                                    .filter((mod) => (child.addoncategories || []).includes(mod.category))
                                    .filter((mod) => mod.category !== "Custom")
                                    .filter((mod) => mod.source === "SR5")
                                    .filter((mod) => !(d.sensors || []).some((row) => row.parent_id === child.id && row.gear_id === mod.id))
                                    .map((mod) => (
                                      <option key={mod.id} value={mod.id}>{tr(mod.name)} ({mod.cost}¥)</option>
                                    ))}
                                </select>
                                <button
                                  className="btn"
                                  disabled={!slotPick[child.id]}
                                  onClick={() => {
                                    const wareId = slotPick[child.id];
                                    const spec = (catalog.sensors || []).find((mod) => mod.id === wareId);
                                    if (!spec) return;
                                    patch({
                                      sensors: [...(ch.sensors || []), { gear_id: spec.id, rating: Math.max(1, spec.minrating || 1), parent_id: child.id }],
                                    });
                                    setSlotPick((cur) => ({ ...cur, [child.id]: "" }));
                                  }}
                                >
                                  装着
                                </button>
                              </div>
                            ) : null}
                          </div>
                        ))}
                        {addons.length ? (
                          <div className="cyber-controls">
                            <select
                              value={slotPick[item.id] || ""}
                              onChange={(e) => setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
                            >
                              <option value="">機能／センサーを追加</option>
                              {addons
                                .filter((mod) => mod.source === "SR5")
                                .filter((mod) => !childrenItems.some((child) => child.gear_id === mod.id))
                                .map((mod) => (
                                  <option key={mod.id} value={mod.id}>{tr(mod.name)} ({mod.cost}¥)</option>
                                ))}
                            </select>
                            <button
                              className="btn"
                              disabled={!slotPick[item.id]}
                              onClick={() => {
                                const wareId = slotPick[item.id];
                                const spec = addons.find((mod) => mod.id === wareId);
                                if (!spec) return;
                                patch({
                                  sensors: [...(ch.sensors || []), { gear_id: spec.id, rating: Math.max(1, spec.minrating || 1), parent_id: item.id }],
                                });
                                setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
                              }}
                            >
                              装着
                            </button>
                          </div>
                        ) : null}
                      </div>
                      <button className="btn danger" onClick={() => patch({
                        sensors: dropTree(ch.sensors || [], item.id),
                      })}>削除</button>
                    </div>
                  );
                })}
              </>
            )}

            { (gearKind === "drone" || gearKind === "vehicle") && (
              <>
                {((gearKind === "drone" ? d.drones : d.vehicles) || []).map((item) => {
                  const addons = (catalog.vehicle_mods || []).filter((mod) => (
                    mod.purchasable !== false
                    && String(mod.cost || "").trim() !== "0"
                    && vehicleFits(mod.required, item)
                    && !vehicleForbidden(mod.forbidden, item)
                    && !(item.mods || []).some((row) => row.mod_id === mod.id)
                  ));
                  const sizes = (catalog.weapon_mounts || []).filter((mod) => (
                    mod.category === "Size"
                    && vehicleFits(mod.required, item)
                  ));
                  const mountedIds = new Set((item.weapon_mounts || []).map((row) => row.weapon_install_id).filter(Boolean));
                  const freeWeapons = (d.weapons || []).filter((weapon) => !weapon.mounted_on && !mountedIds.has(weapon.id));
                  return (
                  <div className="cyber-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / {tr(item.category)} / HND {item.handling} / SPD {item.speed} / ACC {item.accel} / BOD {item.body} / ARM {item.armor} / PLT {item.pilot} / SNR {item.sensor}
                        {item.seats ? ` / SEAT ${item.seats}` : ""}
                        {(item.slot_tracks || []).length
                          ? ` / ${(item.slot_tracks || []).map((track) => `${track.label} ${track.used}/${track.max}`).join(" · ")}`
                          : item.slots_max ? ` / スロット ${item.slots_used ?? 0}/${item.slots_max}` : ""}
                        {" / "}{item.nuyen.toLocaleString()}¥ / {item.source}
                      </div>
                      {(item.mods || []).map((mod) => {
                        const hosted = (d.cyberware || []).filter((row) => row.parent_id === mod.id);
                        const wareOptions = (mod.subsystems || []).length
                          ? catalog.cyberware.items.filter((ware) => wareFitsVehicleMod(ware, mod))
                          : [];
                        const warePickKey = `${mod.id}-ware`;
                        const chosenWare = slotPick[warePickKey] || wareOptions[0]?.id || "";
                        return (
                        <div className="muted" key={mod.id} style={{ marginTop: 6 }}>
                          {tr(mod.name)}
                          {mod.rating_max > 0 ? ` R${mod.rating}` : ""}
                          {mod.included ? " / 付属" : ` / ${mod.nuyen.toLocaleString()}¥`}
                          {mod.slots ? ` / スロット ${mod.slots}` : ""}
                          {mod.capacity_max ? ` / 容量 ${mod.capacity_used ?? 0}/${mod.capacity_max}` : ""}
                          {R5_SLOT_LABELS[mod.category] ? ` / ${R5_SLOT_LABELS[mod.category]}` : null}
                          {mod.included ? null : (
                            <>
                              {" "}
                              <button className="btn danger" onClick={() => patch({
                                vehicle_mods: (ch.vehicle_mods || []).filter((row) => row.id !== mod.id),
                                cyberware: removeWareTree(ch.cyberware || [], mod.id),
                              })}>外す</button>
                            </>
                          )}
                          {mod.rating_max > 0 && !mod.included ? (
                            <label>
                              Rating
                              <input
                                type="number"
                                min={1}
                                max={mod.rating_max}
                                value={mod.rating}
                                onChange={(e) => patch({
                                  vehicle_mods: (ch.vehicle_mods || []).map((row) => (
                                    row.id === mod.id ? { ...row, rating: Number(e.target.value) } : row
                                  )),
                                })}
                              />
                            </label>
                          ) : null}
                          {hosted.map((child) => (
                            <WareRow
                              key={child.id}
                              item={child}
                              childrenItems={(d.cyberware || []).filter((row) => row.parent_id === child.id)}
                              catalogItems={catalog.cyberware.items}
                              grades={catalog.cyberware.grades}
                              kind="cyberware"
                              tr={tr}
                              slotValue={slotPick[child.id] || ""}
                              wareRanges={d.ware_ranges}
                              nested
                              onSlotChange={(wareId) => setSlotPick((cur) => ({ ...cur, [child.id]: wareId }))}
                              onPatchRow={(id, next) => patch({
                                cyberware: (ch.cyberware || []).map((row) => (
                                  row.id === id ? { ...row, ...next } : row
                                )),
                              })}
                              onRemove={(id) => patch({
                                cyberware: removeWareTree(ch.cyberware || [], id),
                              })}
                              onAddChild={(wareId) => {
                                const spec = catalog.cyberware.items.find((w) => w.id === wareId);
                                if (!spec) return;
                                const range = wareBounds(spec, d.ware_ranges);
                                patch({
                                  cyberware: [
                                    ...(ch.cyberware || []),
                                    { ware_id: spec.id, rating: range.min, grade: child.grade, wireless: true, parent_id: child.id },
                                  ],
                                });
                              }}
                            />
                          ))}
                          {wareOptions.length ? (
                            <div className="slot-picker">
                              <select
                                value={chosenWare}
                                onChange={(e) => setSlotPick((cur) => ({ ...cur, [warePickKey]: e.target.value }))}
                              >
                                {wareOptions.map((ware) => {
                                  const range = wareBounds(ware, d.ware_ranges);
                                  const showRange = range.max > range.min || range.max > 1;
                                  return (
                                    <option key={ware.id} value={ware.id}>
                                      {tr(ware.name)} / {ware.capacity ? `[${ware.capacity}]` : ware.category}{showRange ? ` R${range.min}-${range.max}` : ""}
                                    </option>
                                  );
                                })}
                              </select>
                              <button
                                className="btn primary"
                                disabled={!chosenWare}
                                onClick={() => {
                                  const spec = wareOptions.find((w) => w.id === chosenWare);
                                  if (!spec) return;
                                  const range = wareBounds(spec, d.ware_ranges);
                                  patch({
                                    cyberware: [
                                      ...(ch.cyberware || []),
                                      { ware_id: spec.id, rating: range.min, grade: "Standard", wireless: true, parent_id: mod.id },
                                    ],
                                  });
                                  setSlotPick((cur) => ({ ...cur, [warePickKey]: "" }));
                                }}
                              >
                                スロットに追加
                              </button>
                            </div>
                          ) : null}
                        </div>
                        );
                      })}
                      {addons.length ? (
                        <div className="cyber-controls">
                          <select
                            value={slotPick[item.id] || ""}
                            onChange={(e) => setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
                          >
                            <option value="">改造を追加</option>
                            {addons
                              .filter((mod) => gearSearch.trim() || mod.source === "SR5" || mod.source === "R5")
                              .map((mod) => (
                                <option key={mod.id} value={mod.id}>{tr(mod.name)} ({mod.cost}¥)</option>
                              ))}
                          </select>
                          <button
                            className="btn"
                            disabled={!slotPick[item.id]}
                            onClick={() => {
                              const wareId = slotPick[item.id];
                              const spec = addons.find((mod) => mod.id === wareId);
                              if (!spec) return;
                              patch({
                                vehicle_mods: [...(ch.vehicle_mods || []), {
                                  mod_id: spec.id,
                                  parent_id: item.id,
                                  rating: Math.max(1, spec.minrating || 1),
                                }],
                              });
                              setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
                            }}
                          >
                            装着
                          </button>
                        </div>
                      ) : null}
                      {(item.weapon_mounts || []).map((mount) => (
                        <div className="muted" key={mount.id} style={{ marginTop: 6 }}>
                          {tr(mount.label || mount.name)}
                          {mount.included ? " / 付属" : ` / ${mount.nuyen.toLocaleString()}¥`}
                          {mount.slots ? ` / スロット ${mount.slots}` : ""}
                          {mount.weapon_name ? ` / ${tr(mount.weapon_name)}` : " / 未搭載"}
                          {mount.included ? null : (
                            <>
                              {" "}
                              <button className="btn danger" onClick={() => patch({
                                weapon_mounts: (ch.weapon_mounts || []).filter((row) => row.id !== mount.id),
                              })}>外す</button>
                            </>
                          )}
                          <div className="cyber-controls">
                            <select
                              value={mount.weapon_install_id || ""}
                              onChange={(e) => patch({
                                weapon_mounts: (ch.weapon_mounts || []).map((row) => (
                                  row.id === mount.id ? { ...row, weapon_install_id: e.target.value || null } : row
                                )),
                              })}
                            >
                              <option value="">武器を搭載</option>
                              {mount.weapon_install_id && mount.weapon_name ? (
                                <option value={mount.weapon_install_id}>{tr(mount.weapon_name)}</option>
                              ) : null}
                              {freeWeapons.map((weapon) => (
                                <option key={weapon.id} value={weapon.id}>{tr(weapon.name)}</option>
                              ))}
                            </select>
                          </div>
                        </div>
                      ))}
                      {sizes.length ? (
                        <div className="cyber-controls">
                          <select
                            value={slotPick[`${item.id}-mount`] || ""}
                            onChange={(e) => setSlotPick((cur) => ({ ...cur, [`${item.id}-mount`]: e.target.value }))}
                          >
                            <option value="">武器マウントを追加</option>
                            {sizes
                              .filter((mod) => gearSearch.trim() || mod.source === "SR5" || mod.source === "R5")
                              .map((mod) => (
                                <option key={mod.id} value={mod.id}>{tr(mod.name)} ({mod.cost}¥)</option>
                              ))}
                          </select>
                          <button
                            className="btn"
                            disabled={!slotPick[`${item.id}-mount`]}
                            onClick={() => {
                              const wareId = slotPick[`${item.id}-mount`];
                              const spec = sizes.find((mod) => mod.id === wareId);
                              if (!spec) return;
                              patch({
                                weapon_mounts: [...(ch.weapon_mounts || []), { size_id: spec.id, parent_id: item.id }],
                              });
                              setSlotPick((cur) => ({ ...cur, [`${item.id}-mount`]: "" }));
                            }}
                          >
                            装着
                          </button>
                        </div>
                      ) : null}
                      {(item.sensors || []).map((sensor) => {
                        const functions = (d.sensors || []).filter((child) => child.parent_id === sensor.id);
                        const sensorAddons = (catalog.sensors || []).filter((mod) => (
                          (sensor.addoncategories || []).includes(mod.category)
                          && mod.category !== "Custom"
                          && !functions.some((child) => child.gear_id === mod.id)
                        ));
                        return (
                          <div className="muted" key={sensor.id} style={{ marginTop: 6 }}>
                            {tr(sensor.name)}
                            {sensor.rating_max > 0 ? ` R${sensor.rating}` : ""}
                            {sensor.capacity_max ? ` / 容量 ${sensor.capacity_used}/${sensor.capacity_max}` : ""}
                            {sensor.included ? " / 付属" : ` / ${sensor.nuyen.toLocaleString()}¥`}
                            {functions.map((child) => (
                              <div key={child.id} style={{ marginTop: 4, marginLeft: 12 }}>
                                {tr(child.name)}
                                {child.capacity_cost ? ` / 容量 ${child.capacity_cost}` : ""}
                                {" "}
                                <button className="btn danger" onClick={() => patch({
                                  sensors: (ch.sensors || []).filter((row) => row.id !== child.id),
                                })}>外す</button>
                              </div>
                            ))}
                            {sensorAddons.length ? (
                              <div className="cyber-controls">
                                <select
                                  value={slotPick[sensor.id] || ""}
                                  onChange={(e) => setSlotPick((cur) => ({ ...cur, [sensor.id]: e.target.value }))}
                                >
                                  <option value="">機能を追加</option>
                                  {sensorAddons
                                    .filter((mod) => mod.source === "SR5")
                                    .map((mod) => (
                                      <option key={mod.id} value={mod.id}>{tr(mod.name)} ({mod.cost}¥)</option>
                                    ))}
                                </select>
                                <button
                                  className="btn"
                                  disabled={!slotPick[sensor.id]}
                                  onClick={() => {
                                    const wareId = slotPick[sensor.id];
                                    const spec = sensorAddons.find((mod) => mod.id === wareId);
                                    if (!spec) return;
                                    patch({
                                      sensors: [...(ch.sensors || []), { gear_id: spec.id, rating: Math.max(1, spec.minrating || 1), parent_id: sensor.id }],
                                    });
                                    setSlotPick((cur) => ({ ...cur, [sensor.id]: "" }));
                                  }}
                                >
                                  装着
                                </button>
                              </div>
                            ) : null}
                          </div>
                        );
                      })}
                      {(item.gear || []).map((acc) => (
                        <div className="muted" key={acc.id} style={{ marginTop: 6 }}>
                          {tr(acc.label || acc.name)}
                          {acc.rating_max > 0 ? ` R${acc.rating}` : ""}
                          {acc.included ? " / 付属" : ` / ${acc.nuyen.toLocaleString()}¥`}
                          {acc.included ? null : (
                            <>
                              {" "}
                              <button className="btn danger" onClick={() => patch({
                                gear: dropTree(ch.gear || [], acc.id),
                              })}>外す</button>
                            </>
                          )}
                          {acc.rating_max > 0 && !acc.included ? (
                            <label>
                              Rating
                              <input
                                type="number"
                                min={1}
                                max={acc.rating_max}
                                value={acc.rating}
                                onChange={(e) => patch({
                                  gear: (ch.gear || []).map((row) => (
                                    row.id === acc.id ? { ...row, rating: Number(e.target.value) } : row
                                  )),
                                })}
                              />
                            </label>
                          ) : null}
                        </div>
                      ))}
                      <div className="cyber-controls">
                        <select
                          value={slotPick[`${item.id}-gear`] || ""}
                          onChange={(e) => setSlotPick((cur) => ({ ...cur, [`${item.id}-gear`]: e.target.value }))}
                        >
                          <option value="">内装ギアを追加</option>
                          {(catalog.gear || [])
                            .filter((mod) => vehicleInteriorFits(mod) && String(mod.cost || "").trim() !== "0")
                            .filter((mod) => mod.source === "SR5")
                            .filter((mod) => !(item.gear || []).some((row) => row.gear_id === mod.id))
                            .map((mod) => (
                              <option key={mod.id} value={mod.id}>{tr(mod.name)} ({mod.cost}¥)</option>
                            ))}
                        </select>
                        <button
                          className="btn"
                          disabled={!slotPick[`${item.id}-gear`]}
                          onClick={() => {
                            const wareId = slotPick[`${item.id}-gear`];
                            const spec = (catalog.gear || []).find((mod) => mod.id === wareId);
                            if (!spec) return;
                            patch({
                              gear: [...(ch.gear || []), {
                                gear_id: spec.id,
                                rating: Math.max(1, spec.minrating || 1),
                                parent_id: item.id,
                              }],
                            });
                            setSlotPick((cur) => ({ ...cur, [`${item.id}-gear`]: "" }));
                          }}
                        >
                          装着
                        </button>
                      </div>
                    </div>
                    <button className="btn danger" onClick={() => patch(dropDrone(ch, item.id, gearKind === "vehicle" ? "vehicles" : "drones"))}>削除</button>
                  </div>
                  );
                })}
              </>
            )}

            {gearKind === "misc" && (
              <>
                {(d.gear || []).filter((item) => !item.parent_id).map((item) => {
                  const childrenItems = (d.gear || []).filter((child) => child.parent_id === item.id);
                  const addons = (catalog.gear || []).filter((mod) => (
                    Boolean(mod.requireparent) && miscFits(item, mod)
                  ));
                  const addonSpec = (catalog.gear || []).find((mod) => mod.id === (slotPick[item.id] || ""));
                  return (
                    <div className="cyber-item" key={item.id}>
                      <div>
                        <b>{tr(item.label || item.name)}</b>
                        <div className="muted">
                          {item.name} / {tr(item.category)}
                          {item.qty > 1 ? ` ×${item.qty}` : ""}
                          {item.add_weapon ? " / 武器化" : ""}
                          {item.capacity_max ? ` / 容量 ${item.capacity_used}/${item.capacity_max}` : ""}
                          {" / "}{item.nuyen.toLocaleString()}¥ / {item.source}
                        </div>
                        <div className="cyber-controls">
                          <label>
                            数量
                            <input
                              type="number"
                              min={1}
                              max={99}
                              value={item.qty}
                              onChange={(e) => patch({
                                gear: (ch.gear || []).map((row) => (
                                  row.id === item.id ? { ...row, qty: Number(e.target.value) } : row
                                )),
                              })}
                            />
                          </label>
                          {item.rating_max > 0 ? (
                            <label>
                              Rating
                              <input
                                type="number"
                                min={1}
                                max={item.rating_max}
                                value={item.rating}
                                onChange={(e) => patch({
                                  gear: (ch.gear || []).map((row) => (
                                    row.id === item.id ? { ...row, rating: Number(e.target.value) } : row
                                  )),
                                })}
                              />
                            </label>
                          ) : null}
                          {item.needs_extra && item.extra_kind === "skill" ? (
                            <select
                              value={item.extra || ""}
                              onChange={(e) => patch({
                                gear: (ch.gear || []).map((row) => (
                                  row.id === item.id ? { ...row, extra: e.target.value || undefined } : row
                                )),
                              })}
                            >
                              <option value="">スキル</option>
                              {(item.extra_options || []).map((name) => (
                                <option key={name} value={name}>{tr(name)}</option>
                              ))}
                            </select>
                          ) : null}
                          {item.needs_extra && item.extra_kind === "text" ? (
                            <>
                              <input
                                list={`gear-extra-${item.id}`}
                                placeholder="対象"
                                value={item.extra || ""}
                                onChange={(e) => patch({
                                  gear: (ch.gear || []).map((row) => (
                                    row.id === item.id ? { ...row, extra: e.target.value || undefined } : row
                                  )),
                                })}
                              />
                              <datalist id={`gear-extra-${item.id}`}>
                                {(item.extra_options || []).slice(0, 80).map((name) => (
                                  <option key={name} value={name} />
                                ))}
                              </datalist>
                            </>
                          ) : null}
                        </div>
                        {childrenItems.map((child) => (
                          <div className="muted" key={child.id} style={{ marginTop: 6 }}>
                            {tr(child.label || child.name)}
                            {child.rating_max > 0 ? ` R${child.rating}` : ""}
                            {child.qty > 1 ? ` ×${child.qty}` : ""}
                            {child.included ? " / 付属" : ` / ${child.nuyen.toLocaleString()}¥`}
                            {child.capacity_cost ? ` / 容量 ${child.capacity_cost}` : ""}
                            {child.included ? null : (
                              <>
                                {" "}
                                <button className="btn danger" onClick={() => patch({
                                  gear: dropTree(ch.gear || [], child.id),
                                })}>外す</button>
                              </>
                            )}
                            {child.rating_max > 0 && !child.included ? (
                              <label>
                                Rating
                                <input
                                  type="number"
                                  min={1}
                                  max={child.rating_max}
                                  value={child.rating}
                                  onChange={(e) => patch({
                                    gear: (ch.gear || []).map((row) => (
                                      row.id === child.id ? { ...row, rating: Number(e.target.value) } : row
                                    )),
                                  })}
                                />
                              </label>
                            ) : null}
                          </div>
                        ))}
                        {addons.length ? (
                          <div className="cyber-controls">
                            <select
                              value={slotPick[item.id] || ""}
                              onChange={(e) => setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
                            >
                              <option value="">追加ギア</option>
                              {addons
                                .filter((mod) => !childrenItems.some((child) => child.gear_id === mod.id))
                                .filter((mod) => gearSearch.trim() || mod.source === "SR5")
                                .map((mod) => (
                                  <option key={mod.id} value={mod.id}>{tr(mod.name)} ({mod.cost}¥)</option>
                                ))}
                            </select>
                            {addonSpec?.extra_kind === "skill" || addonSpec?.extra_kind === "text" ? (
                              addonSpec.extra_kind === "skill" ? (
                                <select
                                  value={extraPick[item.id] || ""}
                                  onChange={(e) => setExtraPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
                                >
                                  <option value="">対象</option>
                                  {(addonSpec.extra_options || []).map((name) => (
                                    <option key={name} value={name}>{tr(name)}</option>
                                  ))}
                                </select>
                              ) : (
                                <>
                                  <input
                                    list={`gear-addon-extra-${item.id}`}
                                    placeholder="対象"
                                    value={extraPick[item.id] || ""}
                                    onChange={(e) => setExtraPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
                                  />
                                  <datalist id={`gear-addon-extra-${item.id}`}>
                                    {(addonSpec.extra_options || []).slice(0, 80).map((name) => (
                                      <option key={name} value={name} />
                                    ))}
                                  </datalist>
                                </>
                              )
                            ) : null}
                            <button
                              className="btn"
                              disabled={!slotPick[item.id]}
                              onClick={() => {
                                const wareId = slotPick[item.id];
                                const spec = addons.find((mod) => mod.id === wareId);
                                if (!spec) return;
                                patch({
                                  gear: [...(ch.gear || []), {
                                    gear_id: spec.id,
                                    rating: Math.max(1, spec.minrating || 1),
                                    parent_id: item.id,
                                    extra: extraPick[item.id] || undefined,
                                  }],
                                });
                                setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
                                setExtraPick((cur) => ({ ...cur, [item.id]: "" }));
                              }}
                            >
                              装着
                            </button>
                          </div>
                        ) : null}
                      </div>
                      <button className="btn danger" onClick={() => patch({
                        gear: dropTree(ch.gear || [], item.id),
                      })}>削除</button>
                    </div>
                  );
                })}
              </>
            )}

            {gearKind === "lifestyle" && (
              <>
                {(d.lifestyles || []).map((item) => (
                  <div className="cyber-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / {item.monthly.toLocaleString()}¥/{lifeIncrement(item.increment)} × {item.months} = {item.nuyen.toLocaleString()}¥ / {item.source}
                      </div>
                      <div className="cyber-controls">
                        <label>
                          {lifeIncrement(item.increment)}
                          <input
                            type="number"
                            min={1}
                            value={item.months}
                            onChange={(e) => patch({
                              lifestyles: (ch.lifestyles || []).map((row) => (
                                row.id === item.id ? { ...row, months: Number(e.target.value) } : row
                              )),
                            })}
                          />
                        </label>
                      </div>
                    </div>
                    <button className="btn danger" onClick={() => patch({
                      lifestyles: (ch.lifestyles || []).filter((row) => row.id !== item.id),
                    })}>削除</button>
                  </div>
                ))}
              </>
            )}

            <div className="option-row">
              <button className={`tab ${gearCat === "all" ? "active" : ""}`} onClick={() => setGearCat("all")}>すべて</button>
              {(gearKind === "armor"
                ? [...new Set((catalog.armor || []).map((item) => item.category))]
                : gearKind === "weapon"
                  ? [...new Set((catalog.weapons || []).map((item) => item.category))]
                  : gearKind === "optics"
                    ? [...new Set((catalog.optics || []).filter((item) => OPTICS_DEVICE_CATS.has(item.category)).map((item) => item.category))]
                    : gearKind === "sensor"
                      ? [...new Set((catalog.sensors || []).filter((item) => SENSOR_DEVICE_CATS.has(item.category)).map((item) => item.category))]
                      : gearKind === "drone"
                        ? [...new Set((catalog.drones || []).map((item) => item.category))]
                        : gearKind === "vehicle"
                          ? [...new Set((catalog.vehicles || []).map((item) => item.category))]
                        : gearKind === "misc"
                          ? [...new Set((catalog.gear || []).filter((item) => !item.requireparent && (gearSearch.trim() || item.source === "SR5")).map((item) => item.category))]
                    : []
              ).sort().map((cat) => (
                <button key={cat} className={`tab ${gearCat === cat ? "active" : ""}`} onClick={() => setGearCat(cat)}>{tr(cat)}</button>
              ))}
            </div>
            <input
              type="search"
              placeholder={
                gearKind === "armor" ? "防具を検索" :
                gearKind === "weapon" ? "武器を検索" :
                gearKind === "commlink" ? "通信機を検索" :
                gearKind === "cyberdeck" ? "サイバーデッキを検索" :
                gearKind === "rcc" ? "RCCを検索" :
                gearKind === "optics" ? "視覚／聴覚を検索" :
                gearKind === "sensor" ? "センサーを検索" :
                gearKind === "drone" ? "ドローンを検索" :
                gearKind === "vehicle" ? "車両を検索" :
                gearKind === "misc" ? "ギアを検索" : "ライフスタイルを検索"
              }
              value={gearSearch}
              onChange={(e) => setGearSearch(e.target.value)}
            />
            <div className="quality-list">
              {gearKind === "armor" && (catalog.armor || [])
                .filter((item) => gearCat === "all" || item.category === gearCat)
                .filter((item) => {
                  const q = gearSearch.trim().toLowerCase();
                  if (q) return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
                  return item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / 装甲 {item.armor} / {item.cost}¥ / {item.avail || "-"} / {item.source}
                      </div>
                    </div>
                    <button className="btn primary" onClick={() => patch({
                      armor: [...(ch.armor || []), { armor_id: item.id, rating: Math.max(1, item.minrating || 1), equipped: true }],
                    })}>購入</button>
                  </div>
                ))}
              {gearKind === "weapon" && (catalog.weapons || [])
                .filter((item) => gearCat === "all" || item.category === gearCat)
                .filter((item) => {
                  const q = gearSearch.trim().toLowerCase();
                  if (q) return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q) || item.category.toLowerCase().includes(q);
                  return item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / {weaponLine(item)} / {item.cost}¥ / {item.avail || "-"} / {item.source}
                      </div>
                    </div>
                    <button className="btn primary" onClick={() => {
                      if (item.add_gear_id) {
                        patch({
                          gear: [...(ch.gear || []), { gear_id: item.add_gear_id, qty: 1 }],
                        });
                        return;
                      }
                      patch({
                        weapons: [...(ch.weapons || []), { weapon_id: item.id, qty: 1 }],
                      });
                    }}>購入</button>
                  </div>
                ))}
              {gearKind === "commlink" && (catalog.commlinks || [])
                .filter((item) => {
                  const q = gearSearch.trim().toLowerCase();
                  if (q) return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
                  return item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / DR {item.devicerating} / DP {item.dataprocessing} / FW {item.firewall} / {item.cost}¥ / {item.avail || "-"} / {item.source}
                      </div>
                    </div>
                    <button className="btn primary" onClick={() => patch({
                      commlinks: [...(ch.commlinks || []), { gear_id: item.id, rating: Math.max(1, item.minrating || 1) }],
                    })}>購入</button>
                  </div>
                ))}
              {gearKind === "cyberdeck" && (catalog.cyberdecks || [])
                .filter((item) => {
                  const q = gearSearch.trim().toLowerCase();
                  if (q) return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
                  return item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / DR {item.devicerating}{item.attributearray ? ` / ${item.attributearray}` : ""} / プログラム {item.programs} / {item.cost}¥ / {item.avail || "-"} / {item.source}
                      </div>
                    </div>
                    <button className="btn primary" onClick={() => patch({
                      cyberdecks: [...(ch.cyberdecks || []), { gear_id: item.id, rating: Math.max(1, item.minrating || 1) }],
                    })}>購入</button>
                  </div>
                ))}
              {gearKind === "rcc" && (catalog.rccs || [])
                .filter((item) => {
                  const q = gearSearch.trim().toLowerCase();
                  if (q) return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
                  return item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / DR {item.devicerating} / DP {item.dataprocessing} / FW {item.firewall} / プログラム {item.programs} / {item.cost}¥ / {item.avail || "-"} / {item.source}
                      </div>
                    </div>
                    <button className="btn primary" onClick={() => patch({
                      rccs: [...(ch.rccs || []), { gear_id: item.id, rating: Math.max(1, item.minrating || 1) }],
                    })}>購入</button>
                  </div>
                ))}
              {gearKind === "optics" && (catalog.optics || [])
                .filter((item) => OPTICS_DEVICE_CATS.has(item.category) && !item.requireparent)
                .filter((item) => gearCat === "all" || item.category === gearCat)
                .filter((item) => {
                  const q = gearSearch.trim().toLowerCase();
                  if (q) return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q) || item.category.toLowerCase().includes(q);
                  return item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / {tr(item.category)}{item.maxrating > 0 ? ` / R${item.minrating || 1}-${item.maxrating}` : ""} / {item.cost}¥ / {item.avail || "-"} / {item.source}
                      </div>
                    </div>
                    <button className="btn primary" onClick={() => patch({
                      optics: [...(ch.optics || []), { gear_id: item.id, rating: Math.max(1, item.minrating || 1) }],
                    })}>購入</button>
                  </div>
                ))}
              {gearKind === "sensor" && (catalog.sensors || [])
                .filter((item) => SENSOR_DEVICE_CATS.has(item.category) && !item.requireparent)
                .filter((item) => gearCat === "all" || item.category === gearCat)
                .filter((item) => {
                  const q = gearSearch.trim().toLowerCase();
                  if (q) return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q) || item.category.toLowerCase().includes(q);
                  return item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / {tr(item.category)}{item.maxrating > 0 ? ` / R${item.minrating || 1}-${item.maxrating}` : ""} / {item.cost}¥ / {item.avail || "-"} / {item.source}
                      </div>
                    </div>
                    <button className="btn primary" onClick={() => patch({
                      sensors: [...(ch.sensors || []), { gear_id: item.id, rating: Math.max(1, item.minrating || 1) }],
                    })}>購入</button>
                  </div>
                ))}
              {gearKind === "drone" && (catalog.drones || [])
                .filter((item) => gearCat === "all" || item.category === gearCat)
                .filter((item) => {
                  const q = gearSearch.trim().toLowerCase();
                  if (q) return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q) || item.category.toLowerCase().includes(q);
                  return item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / {tr(item.category)} / HND {item.handling} / SPD {item.speed} / PLT {item.pilot} / SNR {item.sensor} / {item.cost}¥ / {item.avail || "-"} / {item.source}
                      </div>
                    </div>
                    <button className="btn primary" onClick={() => patch({
                      drones: [...(ch.drones || []), { gear_id: item.id }],
                    })}>購入</button>
                  </div>
                ))}
              {gearKind === "vehicle" && (catalog.vehicles || [])
                .filter((item) => gearCat === "all" || item.category === gearCat)
                .filter((item) => {
                  const q = gearSearch.trim().toLowerCase();
                  if (q) return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q) || item.category.toLowerCase().includes(q);
                  return item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / {tr(item.category)} / HND {item.handling} / SPD {item.speed} / SEAT {item.seats || "-"} / {item.cost}¥ / {item.avail || "-"} / {item.source}
                      </div>
                    </div>
                    <button className="btn primary" onClick={() => patch({
                      vehicles: [...(ch.vehicles || []), { gear_id: item.id }],
                    })}>購入</button>
                  </div>
                ))}
              {gearKind === "misc" && (catalog.gear || [])
                .filter((item) => !item.requireparent)
                .filter((item) => gearCat === "all" || item.category === gearCat)
                .filter((item) => {
                  const q = gearSearch.trim().toLowerCase();
                  if (q) return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q) || item.category.toLowerCase().includes(q);
                  return item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / {tr(item.category)}{item.maxrating > 0 ? ` / R${item.minrating || 1}-${item.maxrating}` : ""} / {item.cost}¥ / {item.avail || "-"} / {item.source}
                      </div>
                      {item.needs_extra ? (
                        <div className="cyber-controls">
                          {item.extra_kind === "skill" ? (
                            <select
                              value={extraPick[`buy-${item.id}`] || ""}
                              onChange={(e) => setExtraPick((cur) => ({ ...cur, [`buy-${item.id}`]: e.target.value }))}
                            >
                              <option value="">スキル</option>
                              {(item.extra_options || []).map((name) => (
                                <option key={name} value={name}>{tr(name)}</option>
                              ))}
                            </select>
                          ) : (
                            <>
                              <input
                                list={`buy-extra-${item.id}`}
                                placeholder="対象"
                                value={extraPick[`buy-${item.id}`] || ""}
                                onChange={(e) => setExtraPick((cur) => ({ ...cur, [`buy-${item.id}`]: e.target.value }))}
                              />
                              <datalist id={`buy-extra-${item.id}`}>
                                {(item.extra_options || []).slice(0, 80).map((name) => (
                                  <option key={name} value={name} />
                                ))}
                              </datalist>
                            </>
                          )}
                        </div>
                      ) : null}
                    </div>
                    <button className="btn primary" onClick={() => {
                      patch({
                        gear: [...(ch.gear || []), {
                          gear_id: item.id,
                          rating: Math.max(1, item.minrating || 1),
                          extra: extraPick[`buy-${item.id}`] || undefined,
                        }],
                      });
                      setExtraPick((cur) => ({ ...cur, [`buy-${item.id}`]: "" }));
                    }}>購入</button>
                  </div>
                ))}
              {gearKind === "lifestyle" && (catalog.lifestyles || [])
                .filter((item) => {
                  const q = gearSearch.trim().toLowerCase();
                  if (q) return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
                  return CORE_LIFESTYLES.has(item.name);
                })
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / {item.cost.toLocaleString()}¥/{lifeIncrement(item.increment)} / {item.source}
                      </div>
                    </div>
                    <button className="btn primary" onClick={() => patch({
                      lifestyles: [...(ch.lifestyles || []), { lifestyle_id: item.id, months: 1 }],
                    })}>購入</button>
                  </div>
                ))}
            </div>
          </div>
        )}

        {tab === "contacts" && (
          <div className="card">
            <p className="muted">
              無料枠 CHA×3 = {d.contact_points?.used || 0}/{d.contact_points?.free || 0}
              {(d.contact_points?.paid || 0) > 0 ? ` ・ 超過 ${d.contact_points?.paid}カルマ` : ""}
              。Connection と Loyalty は最低1、作成時は合計7まで。超過分は1点1カルマです。
            </p>
            {(d.contacts || []).map((item) => (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>{item.name || "（無名）"}</b>
                  <div className="muted">
                    {item.role ? `${item.role} / ` : ""}
                    Connection {item.connection} / Loyalty {item.loyalty} / {item.cost}点
                  </div>
                  <div className="cyber-controls">
                    <label>
                      名前
                      <input
                        type="text"
                        value={(ch.contacts || []).find((row) => row.id === item.id)?.name ?? item.name}
                        onChange={(e) => setCh({
                          ...ch,
                          contacts: (ch.contacts || []).map((row) => (
                            row.id === item.id ? { ...row, name: e.target.value } : row
                          )),
                        })}
                        onBlur={(e) => patch({
                          contacts: (ch.contacts || []).map((row) => (
                            row.id === item.id ? { ...row, name: e.target.value } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      役割
                      <input
                        type="text"
                        list="contact-roles"
                        value={(ch.contacts || []).find((row) => row.id === item.id)?.role ?? item.role ?? ""}
                        onChange={(e) => setCh({
                          ...ch,
                          contacts: (ch.contacts || []).map((row) => (
                            row.id === item.id ? { ...row, role: e.target.value } : row
                          )),
                        })}
                        onBlur={(e) => patch({
                          contacts: (ch.contacts || []).map((row) => (
                            row.id === item.id ? { ...row, role: e.target.value || null } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      Connection
                      <input
                        type="number"
                        min={1}
                        max={item.connection_max}
                        value={item.connection}
                        onChange={(e) => patch({
                          contacts: (ch.contacts || []).map((row) => (
                            row.id === item.id ? { ...row, connection: Number(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      Loyalty
                      <input
                        type="number"
                        min={1}
                        max={item.loyalty_max}
                        value={item.loyalty}
                        onChange={(e) => patch({
                          contacts: (ch.contacts || []).map((row) => (
                            row.id === item.id ? { ...row, loyalty: Number(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                  </div>
                </div>
                <button className="btn danger" onClick={() => patch({
                  contacts: (ch.contacts || []).filter((row) => row.id !== item.id),
                })}>削除</button>
              </div>
            ))}
            <div className="cyber-toolbar">
              <input
                type="text"
                placeholder="名前"
                value={contactName}
                onChange={(e) => setContactName(e.target.value)}
              />
              <input
                type="text"
                list="contact-roles"
                placeholder="役割（任意）"
                value={contactRole}
                onChange={(e) => setContactRole(e.target.value)}
              />
              <datalist id="contact-roles">
                {[...new Set(CONTACT_ROLES)].map((role) => (
                  <option key={role} value={role} />
                ))}
              </datalist>
              <button
                className="btn primary"
                onClick={() => {
                  const name = contactName.trim();
                  patch({
                    contacts: [...(ch.contacts || []), {
                      name,
                      role: contactRole.trim() || null,
                      connection: 1,
                      loyalty: 1,
                    }],
                  });
                  setContactName("");
                  setContactRole("");
                }}
              >
                追加
              </button>
            </div>
          </div>
        )}

        {tab === "martial" && (
          <div className="card">
            <p className="muted">
              流派 {d.martial_art_points?.styles || 0}/{d.martial_art_points?.style_max || 1}
              {" ・ "}技 {d.martial_art_points?.techniques || 0}/{d.martial_art_points?.technique_max || 5}
              {" ・ "}カルマ {d.martial_art_points?.karma || 0}
              （流派7カルマに技1つ込み、追加技は各5カルマ。作成時は流派1・技合計5まで）
              {(d.unarmed_reach || 0) > 0 ? ` ・ 素手Reach +${d.unarmed_reach}` : ""}
            </p>
            {(d.martial_arts || []).map((item) => {
              const local = (ch.martial_arts || []).find((row) => row.id === item.id);
              const selected = new Set(local?.techniques || item.techniques.map((tech) => tech.name));
              return (
                <div className="cyber-item" key={item.id}>
                  <div>
                    <b>{tr(item.name)}</b>
                    <div className="muted">
                      {item.name} / {item.karma}カルマ（流派 {item.style_karma} + 追加技） / {item.source}
                      {item.page ? ` p.${item.page}` : ""}
                    </div>
                    <div className="martial-techs" style={{ display: "grid", gap: 4, marginTop: 8 }}>
                      {item.technique_options.map((name) => {
                        const owned = selected.has(name);
                        const techMeta = item.techniques.find((tech) => tech.name === name);
                        return (
                          <label key={name} style={{ display: "flex", gap: 8, alignItems: "center" }}>
                            <input
                              type="checkbox"
                              checked={owned}
                              onChange={(e) => {
                                const next = new Set(selected);
                                if (e.target.checked) next.add(name);
                                else next.delete(name);
                                const techniques = item.technique_options.filter((opt) => next.has(opt));
                                patch({
                                  martial_arts: (ch.martial_arts || []).map((row) => (
                                    row.id === item.id ? { ...row, techniques } : row
                                  )),
                                });
                              }}
                            />
                            <span>
                              {tr(name)}
                              {owned && techMeta?.free ? " / 込み" : owned ? ` / ${techMeta?.karma || 5}カルマ` : ""}
                            </span>
                          </label>
                        );
                      })}
                    </div>
                  </div>
                  <button
                    className="btn"
                    onClick={() => patch({
                      martial_arts: (ch.martial_arts || []).filter((row) => row.id !== item.id),
                    })}
                  >
                    削除
                  </button>
                </div>
              );
            })}
            <input
              type="search"
              placeholder="武道を検索"
              value={martialSearch}
              onChange={(e) => setMartialSearch(e.target.value)}
            />
            <div className="list">
              {(catalog.martial_arts || [])
                .filter((item) => {
                  const q = martialSearch.trim().toLowerCase();
                  if (!q) return true;
                  return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
                })
                .slice(0, 40)
                .map((item) => {
                  const owned = (d.martial_arts || []).some((row) => row.art_id === item.id);
                  const blocked = !owned && (d.martial_art_points?.styles || 0) >= (d.martial_art_points?.style_max || 1);
                  return (
                    <div className="list-row" key={item.id}>
                      <div>
                        <b>{tr(item.name)}</b>
                        <div className="muted">
                          {item.name} / {item.cost}カルマ（技1込み） / 技 {item.techniques.length}種 / {item.source}
                          {item.spec_options?.length
                            ? ` / 専門化候補 ${item.spec_options.map((opt) => `${opt.skill}:${opt.spec}`).join(", ")}`
                            : ""}
                        </div>
                      </div>
                      <button
                        className="btn"
                        disabled={owned || blocked}
                        onClick={() => {
                          const first = item.techniques[0];
                          if (!first) return;
                          patch({
                            martial_arts: [
                              ...(ch.martial_arts || []),
                              { art_id: item.id, techniques: [first] },
                            ],
                          });
                        }}
                      >
                        {owned ? "取得済" : blocked ? "上限" : "取得"}
                      </button>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

        {tab === "initiation" && d.enabled_tabs.includes("initiation") && (
          <div className="card">
            <p className="muted">
              等級 {d.initiation?.grade || 0}
              {" ・ "}カルマ {d.initiation?.karma || 0}
              （各等級 10 + 等級×3。魔力上限 = 種族上限 + 等級。等級 ≤ MAG）
            </p>
            <label>
              イニシエーション等級
              <input
                type="range"
                min={0}
                max={Math.max(6, Number(d.totals.MAG || 0))}
                value={ch.initiate_grade || 0}
                onChange={(e) => {
                  const grade = Number(e.target.value);
                  const existing = [...(ch.initiations || [])];
                  const byGrade = new Map(existing.map((row) => [row.grade, row]));
                  const next = [];
                  for (let g = 1; g <= grade; g += 1) {
                    next.push(byGrade.get(g) || { grade: g, kind: "metamagic", option_id: "" });
                  }
                  setCh({ ...ch, initiate_grade: grade, initiations: next });
                }}
                onMouseUp={(e) => {
                  const grade = Number((e.target as HTMLInputElement).value);
                  const existing = [...(ch.initiations || [])];
                  const byGrade = new Map(existing.map((row) => [row.grade, row]));
                  const next = [];
                  for (let g = 1; g <= grade; g += 1) {
                    next.push(byGrade.get(g) || { grade: g, kind: "metamagic", option_id: "" });
                  }
                  patch({ initiate_grade: grade, initiations: next });
                }}
                onTouchEnd={(e) => {
                  const grade = Number((e.target as HTMLInputElement).value);
                  const existing = [...(ch.initiations || [])];
                  const byGrade = new Map(existing.map((row) => [row.grade, row]));
                  const next = [];
                  for (let g = 1; g <= grade; g += 1) {
                    next.push(byGrade.get(g) || { grade: g, kind: "metamagic", option_id: "" });
                  }
                  patch({ initiate_grade: grade, initiations: next });
                }}
              />
              <b style={{ marginLeft: 8 }}>{ch.initiate_grade || 0}</b>
            </label>
            <div style={{ display: "grid", gap: 12, marginTop: 12 }}>
              {(d.initiation?.choices || []).map((choice) => {
                const local = (ch.initiations || []).find((row) => row.grade === choice.grade);
                const kind = (local?.kind || choice.kind || "metamagic") as string;
                const optionId = local?.option_id || choice.option_id || "";
                const talentName = ch.talent || "";
                const canAdept = talentName === "Adept" || talentName === "Mystic Adept";
                const canMagician = talentName !== "Adept";
                const metaOptions = (catalog.metamagics || []).filter((item) => {
                  if (canAdept && !canMagician) return item.adept;
                  if (canMagician && !canAdept) return item.magician;
                  return item.adept || item.magician;
                });
                return (
                  <div className="cyber-item" key={choice.id || choice.grade}>
                    <div style={{ width: "100%" }}>
                      <b>等級 {choice.grade}</b>
                      <div className="muted">{choice.karma}カルマ{choice.name ? ` ・ ${tr(choice.name)}` : ""}</div>
                      <div className="grid" style={{ marginTop: 8 }}>
                        <label>
                          種類
                          <select
                            value={kind}
                            onChange={(e) => {
                              const nextKind = e.target.value;
                              const initiations = (ch.initiations || []).map((row) => (
                                row.grade === choice.grade
                                  ? { ...row, kind: nextKind, option_id: "" }
                                  : row
                              ));
                              patch({ initiations });
                            }}
                          >
                            <option value="metamagic">メタマジック</option>
                            <option value="art">Art</option>
                          </select>
                        </label>
                        <label>
                          {kind === "art" ? "Art" : "メタマジック"}
                          <select
                            value={optionId}
                            onChange={(e) => {
                              const initiations = (ch.initiations || []).map((row) => (
                                row.grade === choice.grade
                                  ? { ...row, kind, option_id: e.target.value }
                                  : row
                              ));
                              patch({ initiations });
                            }}
                          >
                            <option value="">選択してください</option>
                            {kind === "art"
                              ? (catalog.magic_arts || []).map((item) => (
                                  <option key={item.id} value={item.id}>{tr(item.name)} ({item.name})</option>
                                ))
                              : metaOptions.map((item) => (
                                  <option key={item.id} value={item.id}>
                                    {tr(item.name)} ({item.name})
                                    {item.required?.length ? ` / 要 ${item.required.join(", ")}` : ""}
                                  </option>
                                ))}
                          </select>
                        </label>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {tab === "submersion" && d.enabled_tabs.includes("submersion") && (
          <div className="card">
            <p className="muted">
              等級 {d.submersion?.grade || 0}
              {" ・ "}カルマ {d.submersion?.karma || 0}
              （各等級 10 + 等級×3。RES上限 = 種族上限 + 等級。等級 ≤ RES）
            </p>
            <label>
              サブマージョン等級
              <input
                type="range"
                min={0}
                max={Math.max(6, Number(d.totals.RES || 0))}
                value={ch.submersion_grade || 0}
                onChange={(e) => {
                  const grade = Number(e.target.value);
                  const existing = [...(ch.submersions || [])];
                  const byGrade = new Map(existing.map((row) => [row.grade, row]));
                  const next = [];
                  for (let g = 1; g <= grade; g += 1) {
                    next.push(byGrade.get(g) || { grade: g, echo_id: "" });
                  }
                  setCh({ ...ch, submersion_grade: grade, submersions: next });
                }}
                onMouseUp={(e) => {
                  const grade = Number((e.target as HTMLInputElement).value);
                  const existing = [...(ch.submersions || [])];
                  const byGrade = new Map(existing.map((row) => [row.grade, row]));
                  const next = [];
                  for (let g = 1; g <= grade; g += 1) {
                    next.push(byGrade.get(g) || { grade: g, echo_id: "" });
                  }
                  patch({ submersion_grade: grade, submersions: next });
                }}
                onTouchEnd={(e) => {
                  const grade = Number((e.target as HTMLInputElement).value);
                  const existing = [...(ch.submersions || [])];
                  const byGrade = new Map(existing.map((row) => [row.grade, row]));
                  const next = [];
                  for (let g = 1; g <= grade; g += 1) {
                    next.push(byGrade.get(g) || { grade: g, echo_id: "" });
                  }
                  patch({ submersion_grade: grade, submersions: next });
                }}
              />
              <b style={{ marginLeft: 8 }}>{ch.submersion_grade || 0}</b>
            </label>
            <div style={{ display: "grid", gap: 12, marginTop: 12 }}>
              {(d.submersion?.choices || []).map((choice) => {
                const local = (ch.submersions || []).find((row) => row.grade === choice.grade);
                const echoId = local?.echo_id || choice.echo_id || "";
                const extra = local?.extra ?? choice.extra ?? "";
                const selected = (catalog.echoes || []).find((item) => item.id === echoId);
                return (
                  <div className="cyber-item" key={choice.id || choice.grade}>
                    <div style={{ width: "100%" }}>
                      <b>等級 {choice.grade}</b>
                      <div className="muted">{choice.karma}カルマ{choice.name ? ` ・ ${tr(choice.name)}` : ""}</div>
                      <div className="grid" style={{ marginTop: 8 }}>
                        <label>
                          エコー
                          <select
                            value={echoId}
                            onChange={(e) => {
                              const nextId = e.target.value;
                              const nextSpec = (catalog.echoes || []).find((item) => item.id === nextId);
                              const submersions = (ch.submersions || []).map((row) => (
                                row.grade === choice.grade
                                  ? { ...row, echo_id: nextId, extra: nextSpec?.needs_extra ? (row.extra || "") : null }
                                  : row
                              ));
                              patch({ submersions });
                            }}
                          >
                            <option value="">選択してください</option>
                            {(catalog.echoes || []).map((item) => (
                              <option key={item.id} value={item.id}>
                                {tr(item.name)} ({item.name})
                                {item.max_takes == null ? " / 繰り返し可" : item.max_takes > 1 ? ` / 最大${item.max_takes}` : ""}
                              </option>
                            ))}
                          </select>
                        </label>
                        {selected?.needs_extra ? (
                          <label>
                            対象（プログラム名など）
                            <input
                              type="text"
                              value={extra || ""}
                              onChange={(e) => {
                                const submersions = (ch.submersions || []).map((row) => (
                                  row.grade === choice.grade ? { ...row, extra: e.target.value } : row
                                ));
                                setCh({ ...ch, submersions });
                              }}
                              onBlur={(e) => {
                                const submersions = (ch.submersions || []).map((row) => (
                                  row.grade === choice.grade ? { ...row, extra: e.target.value } : row
                                ));
                                patch({ submersions });
                              }}
                            />
                          </label>
                        ) : null}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {tab === "adept" && d.enabled_tabs.includes("adept") && (
          <div className="card">
            <p className="muted">
              パワー点 {formatPoints(d.power_points?.used || 0)}/{formatPoints(d.power_points?.max || 0)}
              {(d.way_discount?.max || 0) > 0 ? ` ・ Way割引 ${formatPoints(d.way_discount?.used || 0)}/${formatPoints(d.way_discount?.max || 0)}` : ""}
            </p>
            {d.needs_mentor ? (
              <MentorPicker catalog={catalog} mentor={d.mentor} ch={ch} tr={tr} onPatch={patch} />
            ) : null}
            {ch.talent === "Mystic Adept" ? (
              <div className="skill-row">
                <span>購入したパワー点（1点=5カルマ）</span>
                <input
                  type="range"
                  min={0}
                  max={d.totals.MAG || 0}
                  value={ch.mystic_pp || 0}
                  onChange={(e) => setCh({ ...ch, mystic_pp: Number(e.target.value) })}
                  onMouseUp={(e) => patch({ mystic_pp: Number((e.target as HTMLInputElement).value) })}
                  onBlur={(e) => patch({ mystic_pp: Number(e.target.value) })}
                />
                <b>{ch.mystic_pp || 0}</b>
              </div>
            ) : null}
            {(d.adept_powers || []).map((item) => (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name}
                    {item.extra ? `（${item.select === "attribute" ? (ATTR_JA[item.extra] || item.extra) : tr(item.extra)}）` : ""}
                    {" / "}{formatPoints(item.cost)} PP
                    {item.discounted && item.full_cost != null ? `（割引前 ${formatPoints(item.full_cost)}）` : ""}
                    {item.free_levels ? ` / 無料Lv ${item.free_levels}` : ""}
                    {item.total_rating && item.total_rating !== item.rating ? ` / 合計R${item.total_rating}` : ""}
                    {" / "}{item.source}
                    {item.notes?.length ? ` / ${item.notes.join(" ・ ")}` : ""}
                    {item.spell ? ` / ${item.spell.dv} @ F${item.spell.force} → ドレイン ${item.spell.drain == null ? "特殊" : `${item.spell.drain}${item.spell.drain_code || ""}`}（抵抗 ${item.spell.resist_attrs} ${item.spell.resist}）` : ""}
                  </div>
                  <div className="cyber-controls">
                    {!item.free_only && item.rating_max > item.rating_min ? (
                      <label>
                        レーティング
                        <input
                          type="number"
                          min={item.rating_min}
                          max={item.rating_max}
                          value={item.rating}
                          onChange={(e) => patch({
                            adept_powers: (ch.adept_powers || []).map((row) => (
                              row.id === item.id ? { ...row, rating: Number(e.target.value) } : row
                            )),
                          })}
                        />
                      </label>
                    ) : null}
                    {!item.free_only ? (
                      <ExtraSelect
                        item={item}
                        tr={tr}
                        onChange={(extra) => patch({
                          adept_powers: (ch.adept_powers || []).map((row) => (
                            row.id === item.id ? { ...row, extra } : row
                          )),
                        })}
                      />
                    ) : null}
                    {item.spell ? (
                      <label>
                        Force
                        <input
                          type="number"
                          min={item.spell.force_min}
                          max={item.spell.force_max}
                          value={item.spell.force}
                          onChange={(e) => patch({
                            adept_powers: (ch.adept_powers || []).map((row) => (
                              row.id === item.id ? { ...row, force: Number(e.target.value) } : row
                            )),
                          })}
                        />
                      </label>
                    ) : null}
                    {item.can_discount ? (
                      <label>
                        <input
                          type="checkbox"
                          checked={!!item.discounted}
                          onChange={(e) => patch({
                            adept_powers: (ch.adept_powers || []).map((row) => (
                              row.id === item.id ? { ...row, discounted: e.target.checked } : row
                            )),
                          })}
                        />
                        Way割引
                      </label>
                    ) : null}
                  </div>
                </div>
                {item.free_only ? <span className="muted">無料</span> : (
                  <button className="btn danger" onClick={() => patch({
                    adept_powers: (ch.adept_powers || []).filter((row) => row.id !== item.id),
                  })}>削除</button>
                )}
              </div>
            ))}
            <div className="cyber-toolbar" style={{ gridTemplateColumns: "1fr" }}>
              <input type="search" placeholder="アデプトパワーを検索" value={powerSearch} onChange={(e) => setPowerSearch(e.target.value)} />
            </div>
            <div className="quality-list">
              {filteredPowers.map((item) => (
                <div className="quality-item" key={item.id}>
                  <div>
                    <b>{tr(item.name)}</b>
                    <div className="muted">
                      {item.name} / {formatPoints(item.points)} PP{item.extrapointcost ? ` +${formatPoints(item.extrapointcost)}` : ""}
                      {item.adeptway ? ` / Way ${formatPoints(item.adeptway)} 割引` : ""}
                      {item.levels ? " / レベルあり" : ""}
                      {item.select === "spell" ? " / 呪文選択" : ""}
                      {" / "}{item.source}
                    </div>
                  </div>
                  <button
                    className="btn primary"
                    onClick={() => patch({
                      adept_powers: [...(ch.adept_powers || []), { power_id: item.id, rating: 1, discounted: !!item.adeptway }],
                    })}
                  >
                    追加
                  </button>
                </div>
              ))}
            </div>
            <h3>Enhancement</h3>
            <p className="muted">Way と対応パワーがあるとき、1つ 2カルマ</p>
            {(d.enhancements || []).map((item) => (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">{item.name}{item.power ? ` / ${item.power}` : ""} / 2カルマ / {item.source}</div>
                </div>
                <button className="btn danger" onClick={() => patch({
                  adept_enhancements: (ch.adept_enhancements || []).filter((id) => id !== item.id),
                })}>削除</button>
              </div>
            ))}
            <input type="search" placeholder="Enhancement を検索" value={enhSearch} onChange={(e) => setEnhSearch(e.target.value)} />
            <div className="quality-list">
              {(catalog.enhancements || [])
                .filter((item) => {
                  const q = enhSearch.trim().toLowerCase();
                  return !q || item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
                })
                .filter((item) => !(ch.adept_enhancements || []).includes(item.id))
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name}{item.power ? ` / ${item.power}` : ""}
                        {item.required?.quality?.length ? ` / ${item.required.quality.join(" ・ ")}` : ""}
                        {" / 2カルマ / "}{item.source}
                      </div>
                    </div>
                    <button className="btn primary" onClick={() => patch({
                      adept_enhancements: [...(ch.adept_enhancements || []), item.id],
                    })}>追加</button>
                  </div>
                ))}
            </div>
            <h3>気焦点</h3>
            <p className="muted">Force × 3,000¥。結合カルマ = Force（Way で減）。Force はパワー点×4</p>
            {(d.qi_foci || []).map((item) => (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>Qi Focus F{item.rating}</b>
                  <div className="muted">
                    {tr(item.name)}{item.extra ? `（${tr(item.extra)}）` : ""} / R{item.power_rating}
                    {" / "}{item.nuyen.toLocaleString()}¥ / 結合 {item.karma}カルマ
                  </div>
                  <div className="cyber-controls">
                    <label>
                      Force
                      <input
                        type="number"
                        min={item.rating_min}
                        max={item.rating_max}
                        value={item.rating}
                        onChange={(e) => patch({
                          qi_foci: (ch.qi_foci || []).map((row) => (
                            row.id === item.id ? { ...row, rating: Number(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    {item.power_rating_max > 1 ? (
                      <label>
                        パワーR
                        <input
                          type="number"
                          min={1}
                          max={item.power_rating_max}
                          value={item.power_rating}
                          onChange={(e) => patch({
                            qi_foci: (ch.qi_foci || []).map((row) => (
                              row.id === item.id ? { ...row, power_rating: Number(e.target.value) } : row
                            )),
                          })}
                        />
                      </label>
                    ) : null}
                    {item.select ? (
                      <label>
                        {selectLabel(item.select)}
                        <select
                          value={item.extra || ""}
                          onChange={(e) => patch({
                            qi_foci: (ch.qi_foci || []).map((row) => (
                              row.id === item.id ? { ...row, extra: e.target.value } : row
                            )),
                          })}
                        >
                          <option value="">選択してください</option>
                          {item.options.map((name) => (
                            <option key={name} value={name}>{item.select === "attribute" ? (ATTR_JA[name] || name) : tr(name)}</option>
                          ))}
                        </select>
                      </label>
                    ) : null}
                  </div>
                </div>
                <button className="btn danger" onClick={() => patch({
                  qi_foci: (ch.qi_foci || []).filter((row) => row.id !== item.id),
                })}>削除</button>
              </div>
            ))}
            <input type="search" placeholder="気焦点に入れるパワーを検索" value={qiSearch} onChange={(e) => setQiSearch(e.target.value)} />
            <div className="quality-list">
              {(catalog.powers || [])
                .filter((item) => {
                  const q = qiSearch.trim().toLowerCase();
                  return q ? item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q) : item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => (
                  <div className="quality-item" key={`qi-${item.id}`}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">{item.name} / Force {Math.max(1, Math.ceil((item.points || 0) / 0.25))}〜 / {item.source}</div>
                    </div>
                    <button className="btn primary" onClick={() => patch({
                      qi_foci: [...(ch.qi_foci || []), { power_id: item.id, rating: Math.max(1, Math.ceil((item.points || 0) / 0.25)), power_rating: 1 }],
                    })}>結合</button>
                  </div>
                ))}
            </div>
          </div>
        )}

        {tab === "spells" && d.enabled_tabs.includes("spells") && (
          <div className="card">
            <p className="muted">
              無料 {(d.spell_points?.used || 0) - (d.spell_points?.paid || 0)}/{d.spell_points?.free || 0}
              {(d.spell_points?.paid || 0) > 0 ? ` ・ 追加 ${d.spell_points?.paid}（各5カルマ）` : ""}
              {d.drain_resist ? ` ・ ドレイン抵抗 ${d.drain_resist.attrs} ${d.drain_resist.pool}` : ""}
              {" ・ 呪文・儀式・エンチャントは同じ無料枠"}
            </p>
            <label>
              伝統
              <select
                value={ch.tradition_id || ""}
                onChange={(e) => patch({ tradition_id: e.target.value || null })}
              >
                <option value="">選択してください</option>
                {(catalog.traditions || []).map((item) => (
                  <option key={item.id} value={item.id}>
                    {tr(item.name)}（{item.drain_attrs.join("+")}）
                  </option>
                ))}
              </select>
            </label>
            {(d.spells || []).map((item) => (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name} / {kindLabel(item.kind)} / {item.useskill || "Spellcasting"} / {item.dv}
                    {item.spell ? ` @ F${item.spell.force} → ドレイン ${item.spell.drain == null ? "特殊" : `${item.spell.drain}${item.spell.drain_code || ""}`}` : ""}
                    {item.focus_bonus ? ` / 焦点+${item.focus_bonus}` : ""}
                    {item.free ? " / 無料" : ` / ${item.karma}カルマ`}
                    {item.required?.length ? ` / 必要 ${item.required.map((name) => tr(name)).join("・")}` : ""}
                    {" / "}{item.source}
                  </div>
                  {item.has_force && item.spell ? (
                    <div className="cyber-controls">
                      <label>
                        Force
                        <input
                          type="number"
                          min={item.spell.force_min}
                          max={item.spell.force_max}
                          value={item.spell.force}
                          onChange={(e) => patch({
                            spells: (ch.spells || []).map((row) => (
                              row.id === item.id ? { ...row, force: Number(e.target.value) } : row
                            )),
                          })}
                        />
                      </label>
                    </div>
                  ) : null}
                </div>
                <button className="btn danger" onClick={() => patch({
                  spells: (ch.spells || []).filter((row) => row.id !== item.id),
                })}>削除</button>
              </div>
            ))}
            <div className="tabs" style={{ marginTop: 12 }}>
              {([
                ["all", "すべて"],
                ["spell", "呪文"],
                ["ritual", "儀式"],
                ["enchantment", "エンチャント"],
              ] as const).map(([key, label]) => (
                <button key={key} className={`tab ${spellKind === key ? "active" : ""}`} onClick={() => setSpellKind(key)}>{label}</button>
              ))}
            </div>
            <input type="search" placeholder="術式を検索" value={spellSearch} onChange={(e) => setSpellSearch(e.target.value)} />
            <div className="quality-list">
              {(catalog.spells || [])
                .filter((item) => item.learnable !== false)
                .filter((item) => !(ch.spells || []).some((row) => row.spell_id === item.id))
                .filter((item) => spellKind === "all" || (item.kind || "spell") === spellKind)
                .filter((item) => {
                  const q = spellSearch.trim().toLowerCase();
                  if (q) {
                    return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q) || (item.category || "").toLowerCase().includes(q);
                  }
                  if (spellKind === "enchantment") return true;
                  return item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => {
                  const paid = (d.spell_points?.used || 0) >= (d.spell_points?.free || 0);
                  return (
                    <div className="quality-item" key={item.id}>
                      <div>
                        <b>{tr(item.name)}</b>
                        <div className="muted">
                          {item.name} / {kindLabel(item.kind)} / {item.useskill || "Spellcasting"} / {item.dv} / {item.source}
                          {item.required?.length ? ` / 必要 ${item.required.map((name) => tr(name)).join("・")}` : ""}
                          {paid ? " / 5カルマ" : " / 無料"}
                        </div>
                      </div>
                      <button className="btn primary" onClick={() => patch({
                        spells: [...(ch.spells || []), { spell_id: item.id }],
                      })}>追加</button>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

        {tab === "spirits" && d.enabled_tabs.includes("spirits") && (
          <div className="card">
            <p className="muted">
              一時召喚は召喚+MAG[Force] vs Force。結合は結合+MAG[Force] vs Force×2と試薬 Force×20¥。ドレインは相手ヒット×2（最低2）。Forceが魔力超なら物理。
              {d.drain_resist ? ` ・ ドレイン抵抗 ${d.drain_resist.attrs} ${d.drain_resist.pool}` : ""}
            </p>
            <label>
              伝統
              <select
                value={ch.tradition_id || ""}
                onChange={(e) => patch({ tradition_id: e.target.value || null })}
              >
                <option value="">選択してください</option>
                {(catalog.traditions || []).map((item) => (
                  <option key={item.id} value={item.id}>
                    {tr(item.name)}（{item.drain_attrs.join("+")}）
                  </option>
                ))}
              </select>
            </label>
            {(d.spirits || []).map((item) => (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name} / {item.role_label || item.role} / {item.bound ? "結合" : "一時召喚"} / F{item.force} / サービス {item.services}
                    {item.bound ? ` / 試薬 ${item.nuyen.toLocaleString()}¥` : " / 日の出または日の入りまで"}
                    {" / "}{item.source}
                  </div>
                  {item.test ? <div className="muted">{testLine(item.test)}</div> : null}
                  {item.attributes ? (
                    <div className="muted">
                      {["BOD", "AGI", "REA", "STR", "WIL", "LOG", "INT", "CHA"].map((key) => `${key} ${item.attributes?.[key] ?? "-"}`).join(" ・ ")}
                      {item.attributes.INI != null ? ` ・ INI ${item.attributes.INI}` : ""}
                    </div>
                  ) : null}
                  {item.powers?.length ? <div className="muted">能力 {item.powers.map((name) => tr(name)).join("・")}</div> : null}
                  <div className="cyber-controls">
                    <label>
                      Force
                      <input
                        type="number"
                        min={1}
                        max={item.force_max}
                        value={item.force}
                        onChange={(e) => patch({
                          spirits: (ch.spirits || []).map((row) => (
                            row.id === item.id ? { ...row, force: Number(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      サービス
                      <input
                        type="number"
                        min={0}
                        max={item.force_max}
                        value={item.services}
                        onChange={(e) => patch({
                          spirits: (ch.spirits || []).map((row) => (
                            row.id === item.id ? { ...row, services: Number(e.target.value), hits: null, opposed_hits: null } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      {item.bound ? "結合" : "召喚"}ヒット
                      <input
                        type="number"
                        min={0}
                        value={item.hits ?? ""}
                        onChange={(e) => patch({
                          spirits: (ch.spirits || []).map((row) => (
                            row.id === item.id ? { ...row, hits: optionalNumber(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      精霊ヒット
                      <input
                        type="number"
                        min={0}
                        value={item.opposed_hits ?? ""}
                        onChange={(e) => patch({
                          spirits: (ch.spirits || []).map((row) => (
                            row.id === item.id ? { ...row, opposed_hits: optionalNumber(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      種類
                      <select
                        value={item.bound ? "bound" : "summoned"}
                        onChange={(e) => patch({
                          spirits: (ch.spirits || []).map((row) => (
                            row.id === item.id ? { ...row, bound: e.target.value === "bound" } : row
                          )),
                        })}
                      >
                        <option value="summoned">一時召喚</option>
                        <option value="bound">結合</option>
                      </select>
                    </label>
                  </div>
                </div>
                <button className="btn danger" onClick={() => patch({
                  spirits: (ch.spirits || []).filter((row) => row.id !== item.id),
                })}>削除</button>
              </div>
            ))}
            <div className="quality-list">
              {Object.entries(d.tradition?.spirits || {}).map(([role, name]) => {
                const spec = (catalog.spirits || []).find((row) => row.name === name);
                if (!spec) return null;
                return (
                  <div className="quality-item" key={role}>
                    <div>
                      <b>{tr(spec.name)}</b>
                      <div className="muted">
                        {spec.name} / {SPIRIT_ROLE_JA[role] || role} / 召喚 vs Force ・ 結合 vs Force×2 / {spec.source}
                      </div>
                      <div className="muted">
                        {["BOD", "AGI", "REA", "STR"].map((key) => `${key} ${spec.attributes?.[key] || "F"}`).join(" ・ ")}
                      </div>
                    </div>
                    <div>
                      <button className="btn" onClick={() => patch({
                        spirits: [...(ch.spirits || []), { spirit_id: spec.id, force: 1, services: 1, bound: false }],
                      })}>召喚</button>
                      {" "}
                      <button className="btn primary" onClick={() => patch({
                        spirits: [...(ch.spirits || []), { spirit_id: spec.id, force: 1, services: 1, bound: true }],
                      })}>結合</button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {tab === "foci" && d.enabled_tabs.includes("foci") && (
          <div className="card">
            <p className="muted">
              購入は定価。クラフトは術式＋試薬Force×20¥とアーティフィシング+MAG[Force] vs Force×2（Force日）。結合カルマは Force。同時 {d.focus_limits?.count || 0}/{d.focus_limits?.count_max || 0} ・ Force合計 {d.focus_limits?.force || 0}/{d.focus_limits?.force_max || 0}
              {d.enabled_tabs.includes("adept") ? " ・ 気焦点はアデプトタブ（この上限に含む）" : ""}
            </p>
            {(d.foci || []).map((item) => (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name} / F{item.force} / {item.crafted ? "クラフト" : "購入"} / {item.nuyen.toLocaleString()}¥ / 結合 {item.karma}カルマ
                    {item.crafted ? `（術式 ${item.formula_nuyen?.toLocaleString() || 0}¥ + 試薬 ${item.reagent_nuyen?.toLocaleString() || 0}¥ / 定価 ${item.retail_nuyen?.toLocaleString() || 0}¥）` : ""}
                    {item.effect ? ` / ${item.effect.replace(/Rating/g, String(item.force))}` : ""}
                    {item.needs_weapon ? (item.weapon_name ? ` / 対象 ${tr(item.weapon_name)} +${item.weapon_dice || item.force}` : " / 対象武器が必要") : ""}
                    {" / "}{item.source}
                  </div>
                  {item.formula_test ? <div className="muted">術式自作 {testLine(item.formula_test)}</div> : null}
                  {item.test ? <div className="muted">{testLine(item.test)}</div> : null}
                  <div className="cyber-controls">
                    <label>
                      Force
                      <input
                        type="number"
                        min={1}
                        max={item.force_max}
                        value={item.force}
                        onChange={(e) => patch({
                          foci: (ch.foci || []).map((row) => (
                            row.id === item.id ? { ...row, force: Number(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    {item.needs_weapon ? (
                      <label>
                        対象武器
                        <select
                          value={item.weapon_id || ""}
                          onChange={(e) => patch({
                            foci: (ch.foci || []).map((row) => (
                              row.id === item.id ? { ...row, extra: e.target.value || null } : row
                            )),
                          })}
                        >
                          <option value="">{item.weapon_type === "Melee" ? "近接武器" : "武器"}</option>
                          {(item.weapon_options || []).map((opt) => (
                            <option key={opt.id} value={opt.id}>{tr(opt.name)}</option>
                          ))}
                        </select>
                      </label>
                    ) : null}
                    {item.crafted ? (
                      <>
                        <label>
                          作成ヒット
                          <input
                            type="number"
                            min={0}
                            value={item.hits ?? ""}
                            onChange={(e) => patch({
                              foci: (ch.foci || []).map((row) => (
                                row.id === item.id ? { ...row, hits: optionalNumber(e.target.value) } : row
                              )),
                            })}
                          />
                        </label>
                        <label>
                          抵抗ヒット
                          <input
                            type="number"
                            min={0}
                            value={item.opposed_hits ?? ""}
                            onChange={(e) => patch({
                              foci: (ch.foci || []).map((row) => (
                                row.id === item.id ? { ...row, opposed_hits: optionalNumber(e.target.value) } : row
                              )),
                            })}
                          />
                        </label>
                        <label>
                          術式
                          <select
                            value={item.formula_bought ? "buy" : "design"}
                            onChange={(e) => patch({
                              foci: (ch.foci || []).map((row) => (
                                row.id === item.id ? { ...row, formula_bought: e.target.value === "buy" } : row
                              )),
                            })}
                          >
                            <option value="buy">購入</option>
                            <option value="design">自作（アーカナ）</option>
                          </select>
                        </label>
                      </>
                    ) : null}
                  </div>
                </div>
                <button className="btn danger" onClick={() => patch({
                  foci: (ch.foci || []).filter((row) => row.id !== item.id),
                })}>削除</button>
              </div>
            ))}
            <input type="search" placeholder="フォーカスを検索" value={focusSearch} onChange={(e) => setFocusSearch(e.target.value)} />
            <div className="quality-list">
              {(catalog.foci || [])
                .filter((item) => {
                  const q = focusSearch.trim().toLowerCase();
                  if (q) {
                    return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q) || (item.effect || "").toLowerCase().includes(q);
                  }
                  return item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / 購入 {item.cost}
                        {item.formula ? ` / クラフト 術式 ${item.formula.cost} + 試薬 20¥×F` : ""}
                        {" / "}{item.effect || "結合のみ"}
                        {item.needs_weapon ? ` / ${item.weapon_type || "Melee"}武器指定` : ""}
                        {" / "}{item.source}
                      </div>
                    </div>
                    <div>
                      <button className="btn" onClick={() => patch({
                        foci: [...(ch.foci || []), { gear_id: item.id, force: 1, crafted: false }],
                      })}>購入</button>
                      {" "}
                      <button className="btn primary" onClick={() => patch({
                        foci: [...(ch.foci || []), { gear_id: item.id, force: 1, crafted: true, formula_bought: true }],
                      })}>クラフト</button>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}

        {tab === "complexforms" && d.enabled_tabs.includes("complexforms") && (
          <div className="card">
            <p className="muted">
              優先度の無料枠 {d.complex_form_points?.used || 0}/{d.complex_form_points?.free || 0}
              {(d.complex_form_points?.paid || 0) > 0 ? ` ・ 追加 ${d.complex_form_points?.paid}×4カルマ` : ""}
              {d.fade_resist ? ` ・ フェード抵抗 ${d.fade_resist.attrs} ${d.fade_resist.pool}` : ""}
              。スレッディングは Software+RES[Level]。Level が共振力超なら物理フェード。
            </p>
            {(d.complex_forms || []).map((item) => (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>{tr(item.label || item.name)}</b>
                  <div className="muted">
                    {item.name} / {item.target} / {cfDuration(item.duration)} / {item.fv}
                    {` @ L${item.level} → フェード ${item.fade == null ? "特殊" : `${item.fade}${item.fade_code || ""}`}`}
                    {item.free ? " / 無料" : ` / ${item.karma}カルマ`}
                    {" / "}{item.source}
                  </div>
                  {item.test ? <div className="muted">{testLine(item.test, "フェード")}</div> : null}
                  <div className="cyber-controls">
                    <label>
                      Level
                      <input
                        type="number"
                        min={item.level_min}
                        max={item.level_max}
                        value={item.level}
                        onChange={(e) => patch({
                          complex_forms: (ch.complex_forms || []).map((row) => (
                            row.id === item.id ? { ...row, level: Number(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    {item.needs_extra ? (
                      <label>
                        属性
                        <select
                          value={item.extra || ""}
                          onChange={(e) => patch({
                            complex_forms: (ch.complex_forms || []).map((row) => (
                              row.id === item.id ? { ...row, extra: e.target.value } : row
                            )),
                          })}
                        >
                          <option value="">選択してください</option>
                          {(item.options || []).map((name) => (
                            <option key={name} value={name}>{tr(name)}</option>
                          ))}
                        </select>
                      </label>
                    ) : null}
                  </div>
                </div>
                <button className="btn danger" onClick={() => patch({
                  complex_forms: (ch.complex_forms || []).filter((row) => row.id !== item.id),
                })}>削除</button>
              </div>
            ))}
            <input type="search" placeholder="複合体を検索" value={cfSearch} onChange={(e) => setCfSearch(e.target.value)} />
            <div className="quality-list">
              {(catalog.complex_forms || [])
                .filter((item) => !(ch.complex_forms || []).some((row) => row.form_id === item.id))
                .filter((item) => {
                  const q = cfSearch.trim().toLowerCase();
                  if (q) {
                    return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q) || (item.target || "").toLowerCase().includes(q);
                  }
                  return item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => {
                  const paid = (d.complex_form_points?.used || 0) >= (d.complex_form_points?.free || 0);
                  const blocked = (item.required || []).length ? `必要 ${item.required!.map((name) => tr(name)).join("・")}` : "";
                  return (
                    <div className="quality-item" key={item.id}>
                      <div>
                        <b>{tr(item.name)}</b>
                        <div className="muted">
                          {item.name} / {item.target} / {cfDuration(item.duration)} / {item.fv} / {item.source}
                          {item.needs_extra ? " / マトリクス属性が必要" : ""}
                          {blocked ? ` / ${blocked}` : ""}
                          {paid ? " / 4カルマ" : " / 無料"}
                        </div>
                      </div>
                      <button className="btn primary" onClick={() => patch({
                        complex_forms: [...(ch.complex_forms || []), { form_id: item.id }],
                      })}>追加</button>
                    </div>
                  );
                })}
            </div>
          </div>
        )}

        {tab === "sprites" && d.enabled_tabs.includes("sprites") && (
          <div className="card">
            <p className="muted">
              コンパイルは Compiling+RES[Level] vs Level×2。登録は Registering+RES[Level] vs Level×2（Level時間）。フェードは相手ヒット×2（最低2）。Levelが共振力超なら物理。登録数は共振力まで。
              {d.fade_resist ? ` ・ フェード抵抗 ${d.fade_resist.attrs} ${d.fade_resist.pool}` : ""}
              {d.living_persona ? ` ・ リビングペルソナ DR${d.living_persona.device_rating} ATK${d.living_persona.attack} SLZ${d.living_persona.sleaze} DP${d.living_persona.dataprocessing} FW${d.living_persona.firewall}` : ""}
            </p>
            {(d.sprites || []).map((item) => (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name} / {item.registered ? "登録" : "コンパイル"} / L{item.level} / タスク {item.services}
                    {item.registered ? "" : " / 再起動またはリブートまで"}
                    {" / "}{item.source}
                  </div>
                  {item.test ? <div className="muted">{testLine(item.test, "フェード")}</div> : null}
                  {item.matrix ? (
                    <div className="muted">
                      ATK {item.matrix.attack} ・ SLZ {item.matrix.sleaze} ・ DP {item.matrix.dataprocessing} ・ FW {item.matrix.firewall} ・ INI {item.matrix.initiative}
                    </div>
                  ) : null}
                  {item.powers?.length ? <div className="muted">能力 {item.powers.map((name) => tr(name)).join("・")}</div> : null}
                  <div className="cyber-controls">
                    <label>
                      Level
                      <input
                        type="number"
                        min={1}
                        max={item.level_max}
                        value={item.level}
                        onChange={(e) => patch({
                          sprites: (ch.sprites || []).map((row) => (
                            row.id === item.id ? { ...row, level: Number(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      タスク
                      <input
                        type="number"
                        min={0}
                        max={item.level_max}
                        value={item.services}
                        onChange={(e) => patch({
                          sprites: (ch.sprites || []).map((row) => (
                            row.id === item.id ? { ...row, services: Number(e.target.value), hits: null, opposed_hits: null } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      {item.registered ? "登録" : "コンパイル"}ヒット
                      <input
                        type="number"
                        min={0}
                        value={item.hits ?? ""}
                        onChange={(e) => patch({
                          sprites: (ch.sprites || []).map((row) => (
                            row.id === item.id ? { ...row, hits: optionalNumber(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      スプライトヒット
                      <input
                        type="number"
                        min={0}
                        value={item.opposed_hits ?? ""}
                        onChange={(e) => patch({
                          sprites: (ch.sprites || []).map((row) => (
                            row.id === item.id ? { ...row, opposed_hits: optionalNumber(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      種類
                      <select
                        value={item.registered ? "registered" : "compiled"}
                        onChange={(e) => patch({
                          sprites: (ch.sprites || []).map((row) => (
                            row.id === item.id ? { ...row, registered: e.target.value === "registered" } : row
                          )),
                        })}
                      >
                        <option value="compiled">コンパイル</option>
                        <option value="registered">登録</option>
                      </select>
                    </label>
                  </div>
                </div>
                <button className="btn danger" onClick={() => patch({
                  sprites: (ch.sprites || []).filter((row) => row.id !== item.id),
                })}>削除</button>
              </div>
            ))}
            <input type="search" placeholder="スプライトを検索" value={spriteSearch} onChange={(e) => setSpriteSearch(e.target.value)} />
            <div className="quality-list">
              {(catalog.sprites || [])
                .filter((item) => {
                  const q = spriteSearch.trim().toLowerCase();
                  if (q) return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
                  return item.source === "SR5";
                })
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">{item.name} / {item.source}</div>
                    </div>
                    <div>
                      <button className="btn" onClick={() => patch({
                        sprites: [...(ch.sprites || []), { sprite_id: item.id, level: 1, registered: false }],
                      })}>コンパイル</button>
                      {" "}
                      <button className="btn primary" onClick={() => patch({
                        sprites: [...(ch.sprites || []), { sprite_id: item.id, level: 1, registered: true }],
                      })}>登録</button>
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>

      <aside className="side">
        <h2>{ch.name}</h2>
        <div className="muted">{tr(ch.metatype)}{ch.metavariant ? ` / ${tr(ch.metavariant)}` : ""} ・ {ch.talent}</div>
        <div className="stat">
          <span>作成方式</span>
          <b>
            {(ch.build_method || "Priority") === "Karma"
              ? `Karma ${d.karma.remaining}/${d.karma.pool}`
              : (ch.build_method || "Priority") === "SumToTen"
                ? `Sum to Ten ${d.sum_to_ten?.used ?? 0}/${d.sum_to_ten?.max ?? 10}`
                : "Priority"}
          </b>
        </div>
        {error ? <p className="errors">{error}</p> : null}
        {d.errors.length ? (
          <ul className="errors">{d.errors.map((e) => <li key={e}>{e}</li>)}</ul>
        ) : (
          <p className="ok">作成ルール上は問題なし</p>
        )}
        {(d.warnings || []).length ? (
          <ul className="warn">{d.warnings!.map((w) => <li key={w}>{w}</li>)}</ul>
        ) : null}
        <div className="stat"><span>物理/精神/社会リミット</span><b>{d.limits.physical}/{d.limits.mental}/{d.limits.social}</b></div>
        {(d.limit_modifiers || []).map((mod, idx) => (
          <div className="stat" key={`${mod.limit}-${mod.condition || ""}-${idx}`}>
            <span>{limitModifierLine([mod])}</span>
          </div>
        ))}
        <div className="stat"><span>コンディション</span><b>P{d.condition_monitor.physical} / S{d.condition_monitor.stun}</b></div>
        {d.limb_quality ? <div className="stat"><span>リム本数 Quality</span><b>{d.limb_quality.count}本 / {d.limb_quality.pairs}組</b></div> : null}
        <div className="stat"><span>イニシアチブ</span><b>{d.initiative.value}+{d.initiative.dice}d6</b></div>
        <div className="stat"><span>アーマー</span><b>{d.armor}{d.worn_armor ? `（${tr(d.worn_armor)}）` : ""}</b></div>
        {specialArmorBits(d.special_armor).map((row) => (
          <div className="stat" key={row.label}><span>{row.label}</span><b>{row.value}</b></div>
        ))}
        <div className="stat"><span>エッセンス</span><b>{d.essence}{(d.essence_lost_cyber || d.essence_lost_bio) ? `（C −${d.essence_lost_cyber ?? 0} / B −${d.essence_lost_bio ?? 0}）` : ""}</b></div>
        <div className="stat"><span>ニューエン</span><b>{d.nuyen.toLocaleString()}¥</b></div>
        <div className="stat"><span>入手制限</span><b>{d.avail_limit ?? 12}</b></div>
        <div className="stat"><span>デバイスレーティング</span><b>{d.device_rating_limit ?? 6}</b></div>
        {d.skillwires ? <div className="stat"><span>スキルワイヤ</span><b>R{d.skillwires}</b></div> : null}
        {d.skilljack ? <div className="stat"><span>スキルジャック</span><b>R{d.skilljack}</b></div> : null}
        <div className="stat">
          <span>ウェア強化</span>
          <b>
            {wareAttrLine(d.ware_attr_bonus)
              ? `${wareAttrLine(d.ware_attr_bonus)} / 上限+${d.ware_attr_limit ?? 4}`
              : `+${d.ware_attr_limit ?? 4}`}
          </b>
        </div>
        {d.lifestyle ? <div className="stat"><span>ライフスタイル</span><b>{tr(d.lifestyle.name)} {d.lifestyle.months}{lifeIncrement(d.lifestyle.increment)}</b></div> : null}
        {d.commlink ? <div className="stat"><span>通信機</span><b>{tr(d.commlink.name)} DR{d.commlink.device_rating}</b></div> : null}
        {d.cyberdeck ? <div className="stat"><span>サイバーデッキ</span><b>{tr(d.cyberdeck.name)} DR{d.cyberdeck.device_rating} / {d.cyberdeck.attack}/{d.cyberdeck.sleaze}/{d.cyberdeck.dataprocessing}/{d.cyberdeck.firewall}{d.cyberdeck.program_max ? ` / プログラム ${d.cyberdeck.program_used ?? 0}/${d.cyberdeck.program_max}` : ""}</b></div> : null}
        {d.rcc ? <div className="stat"><span>RCC</span><b>{tr(d.rcc.name)} DR{d.rcc.device_rating} / DP{d.rcc.dataprocessing} FW{d.rcc.firewall}{d.rcc.program_max ? ` / プログラム ${d.rcc.program_used ?? 0}/${d.rcc.program_max}` : ""}</b></div> : null}
        {(d.optics || []).some((item) => !item.parent_id) ? (
          <div className="stat"><span>視覚／聴覚</span><b>{(d.optics || []).filter((item) => !item.parent_id).length}件</b></div>
        ) : null}
        {(d.sensors || []).some((item) => !item.parent_id) ? (
          <div className="stat"><span>センサー</span><b>{(d.sensors || []).filter((item) => !item.parent_id).length}件</b></div>
        ) : null}
        {(d.drones || []).length ? (
          <div className="stat"><span>ドローン</span><b>{(d.drones || []).length}件</b></div>
        ) : null}
        <div className="stat"><span>カルマ</span><b>{d.karma.remaining} / {d.karma.pool}</b></div>
        <div className="stat"><span>不利カルマ</span><b>{d.karma.negative?.used || 0}/{d.karma.negative?.max || 25}</b></div>
        <div className="stat"><span>属性点</span><b>{d.points.attributes.used}/{d.points.attributes.max}</b></div>
        <div className="stat"><span>特殊点</span><b>{d.points.special.used}/{d.points.special.max}</b></div>
        <div className="stat"><span>スキル点</span><b>{d.points.skills.used}/{d.points.skills.max}</b></div>
        <div className="stat"><span>知識点</span><b>{d.points.knowledge.used}/{d.points.knowledge.max}</b></div>
        <div className="stat"><span>コネクト</span><b>{d.contact_points?.used || 0}/{d.contact_points?.free || 0}{(d.contact_points?.paid || 0) > 0 ? ` +${d.contact_points?.paid}` : ""}</b></div>
        <div className="stat"><span>武道</span><b>{d.martial_art_points?.styles || 0}/{d.martial_art_points?.style_max || 1}流派 ・ {d.martial_art_points?.techniques || 0}/{d.martial_art_points?.technique_max || 5}技{(d.martial_art_points?.karma || 0) > 0 ? ` / ${d.martial_art_points?.karma}K` : ""}</b></div>
        {d.enabled_tabs.includes("initiation") ? (
          <div className="stat"><span>イニシエーション</span><b>等級 {d.initiation?.grade || 0}{(d.initiation?.karma || 0) > 0 ? ` / ${d.initiation?.karma}K` : ""}</b></div>
        ) : null}
        {d.enabled_tabs.includes("submersion") ? (
          <div className="stat"><span>サブマージョン</span><b>等級 {d.submersion?.grade || 0}{(d.submersion?.karma || 0) > 0 ? ` / ${d.submersion?.karma}K` : ""}</b></div>
        ) : null}
        {d.enabled_tabs.includes("adept") ? (
          <div className="stat"><span>パワー点</span><b>{formatPoints(d.power_points?.used || 0)}/{formatPoints(d.power_points?.max || 0)}</b></div>
        ) : null}
        {d.enabled_tabs.includes("spells") ? (
          <div className="stat"><span>術式</span><b>{d.spell_points?.used || 0}/{d.spell_points?.free || 0}{(d.spell_points?.paid || 0) > 0 ? ` +${d.spell_points?.paid}` : ""}</b></div>
        ) : null}
        {d.enabled_tabs.includes("spirits") ? (
          <div className="stat"><span>精霊</span><b>{d.spirits?.length || 0}</b></div>
        ) : null}
        {d.enabled_tabs.includes("foci") ? (
          <div className="stat"><span>フォーカス</span><b>{d.focus_limits?.count || 0}/{d.focus_limits?.count_max || 0}</b></div>
        ) : null}
        {d.enabled_tabs.includes("complexforms") ? (
          <div className="stat"><span>複合体</span><b>{d.complex_form_points?.used || 0}/{d.complex_form_points?.free || 0}{(d.complex_form_points?.paid || 0) > 0 ? ` +${d.complex_form_points?.paid}` : ""}</b></div>
        ) : null}
        {d.enabled_tabs.includes("sprites") ? (
          <div className="stat"><span>スプライト</span><b>{d.sprites?.length || 0}</b></div>
        ) : null}
        {d.living_persona ? (
          <div className="stat"><span>リビングペルソナ</span><b>DR{d.living_persona.device_rating} / {d.living_persona.attack}/{d.living_persona.sleaze}/{d.living_persona.dataprocessing}/{d.living_persona.firewall}{(d.living_persona.matrix_initiative_dice || 0) > 0 ? ` / マトリクスInit+${d.living_persona.matrix_initiative_dice}d6` : ""}</b></div>
        ) : null}
        {d.tradition ? <div className="stat"><span>伝統</span><b>{tr(d.tradition.name)}</b></div> : null}
        {d.needs_mentor && d.mentor ? <div className="stat"><span>メンター</span><b>{tr(d.mentor.name)}</b></div> : null}
        {(d.damage_resistance || 0) > 0 ? <div className="stat"><span>ダメージ抵抗</span><b>+{d.damage_resistance}</b></div> : null}
        {(d.unarmed_dv || 0) > 0 ? <div className="stat"><span>非武装DV</span><b>+{d.unarmed_dv}</b></div> : null}
        <h3>属性</h3>
        {ATTRS.map((k) => {
          const hidden = (k === "MAG" && !d.enabled_tabs.includes("MAG")) || (k === "RES" && !d.enabled_tabs.includes("RES"));
          if (hidden) return null;
          return (
            <div className="stat" key={k}>
              <span>{ATTR_JA[k]}</span>
              <b>
                {d.totals[k] ?? "-"}
                {(d.ware_attr_bonus?.[k] || 0) !== 0 ? (
                  <span className="muted"> ウェア+{d.ware_attr_bonus![k]}</span>
                ) : null}
                {d.limb_replace && (k === "STR" || k === "AGI") ? (
                  <span className="muted"> リム平均</span>
                ) : null}
              </b>
            </div>
          );
        })}
        {d.unimplemented_bonuses.length > 0 && (
          <p className="warn">未実装ボーナス {d.unimplemented_bonuses.length} 件（無視して継続）</p>
        )}
      </aside>
    </div>
  );
}
