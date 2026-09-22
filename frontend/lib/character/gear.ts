import type {
  WareCatalogItem,
  WareInstall,
  WeaponConstraints,
  WeaponDetailsNode,
} from "@/lib/types";
import { DEFAULT_ARRAY_ORDER, VEHICLE_INTERIOR_CATS } from "@/lib/character/constants";
import { removeWareTree } from "@/lib/character/ware";
import type { UiFn } from "@/lib/i18n";

export function swapMatrixOrder(
  order: string[] | undefined,
  fromKey: string,
  toPos: number,
): string[] {
  const next = [...(order && order.length === 4 ? order : DEFAULT_ARRAY_ORDER)];
  const fromPos = next.indexOf(fromKey);
  if (fromPos < 0 || toPos < 0 || toPos >= next.length || fromPos === toPos) return next;
  [next[fromPos], next[toPos]] = [next[toPos], next[fromPos]];
  return next;
}

export function vehicleFits(
  cons:
    | {
        names?: string[];
        category_contains?: string[];
        category_equals?: string[];
        body_lte?: number | null;
        body_gte?: number | null;
      }
    | undefined,
  vehicle: { name: string; category?: string; body?: string },
) {
  if (!cons) return true;
  const names = cons.names || [];
  const contains = cons.category_contains || [];
  const equals = cons.category_equals || [];
  if (
    !names.length &&
    !contains.length &&
    !equals.length &&
    cons.body_lte == null &&
    cons.body_gte == null
  )
    return true;
  if (names.length && !names.includes(vehicle.name)) return false;
  const category = vehicle.category || "";
  if (contains.length && !contains.some((part) => category.includes(part))) return false;
  if (equals.length && !equals.includes(category)) return false;
  const body = Number(String(vehicle.body || "0").split("/")[0]) || 0;
  if (cons.body_lte != null && body > cons.body_lte) return false;
  if (cons.body_gte != null && body < cons.body_gte) return false;
  return true;
}

export function vehicleForbidden(
  cons:
    | {
        names?: string[];
        category_contains?: string[];
        category_equals?: string[];
        body_lte?: number | null;
        body_gte?: number | null;
      }
    | undefined,
  vehicle: { name: string; category?: string; body?: string },
) {
  if (!cons) return false;
  const has = Boolean(
    (cons.names || []).length ||
    (cons.category_contains || []).length ||
    (cons.category_equals || []).length ||
    cons.body_lte != null ||
    cons.body_gte != null,
  );
  return has && vehicleFits(cons, vehicle);
}

export function dropDrone(
  ch: {
    drones?: { id?: string }[];
    vehicles?: { id?: string }[];
    vehicle_mods?: { id?: string; parent_id?: string | null }[];
    weapon_mounts?: { parent_id?: string | null; weapon_install_id?: string | null }[];
    sensors?: { id?: string; parent_id?: string | null }[];
    gear?: { id?: string; parent_id?: string | null }[];
    programs?: { id?: string; parent_id?: string | null }[];
    cyberware?: WareInstall[];
  },
  id: string,
  listKey: "drones" | "vehicles" = "drones",
) {
  let sensors = ch.sensors || [];
  const roots = sensors
    .filter((row) => row.parent_id === id && row.id)
    .map((row) => row.id as string);
  for (const sid of roots) sensors = dropTree(sensors, sid);
  sensors = sensors.filter((row) => row.parent_id !== id);
  const removedModIds = (ch.vehicle_mods || [])
    .filter((row) => row.parent_id === id && row.id)
    .map((row) => row.id as string);
  let cyberware = ch.cyberware || [];
  for (const mid of removedModIds) cyberware = removeWareTree(cyberware, mid);
  return {
    drones: listKey === "drones" ? (ch.drones || []).filter((row) => row.id !== id) : ch.drones,
    vehicles:
      listKey === "vehicles" ? (ch.vehicles || []).filter((row) => row.id !== id) : ch.vehicles,
    vehicle_mods: (ch.vehicle_mods || []).filter((row) => row.parent_id !== id),
    weapon_mounts: (ch.weapon_mounts || []).filter((row) => row.parent_id !== id),
    sensors,
    gear: dropTree(ch.gear || [], id),
    programs: (ch.programs || []).filter((row) => row.parent_id !== id),
    cyberware,
  };
}

export function dropTree<T extends { id?: string; parent_id?: string | null }>(
  rows: T[],
  id: string,
): T[] {
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

export function vehicleInteriorFits(mod: { category: string; required_categories?: string[] }) {
  if (VEHICLE_INTERIOR_CATS.has(mod.category)) return true;
  return (mod.required_categories || []).some(
    (cat) => cat && cat !== "Custom" && cat === "Commlinks",
  );
}

/** Whether a plugin the host already carries should stay off its "slot
 *  something in" list.
 *
 *  A second Vision Magnification in the same optic does nothing, so these
 *  lists hide what is already there. But an item that names *what it is for*
 *  (`needs_extra`: the Fake License's license, an autosoft's model) is a
 *  different item every time it is bought — and a Fake SIN carries several
 *  licenses, which the flat rule made impossible after the first. */
export function alreadySlotted(
  mod: { id: string; needs_extra?: boolean },
  siblings: { gear_id?: string }[],
) {
  if (mod.needs_extra) return false;
  return siblings.some((row) => row.gear_id === mod.id);
}

export function miscFits(
  parent: { name: string; category: string; addoncategories?: string[] },
  child: {
    category: string;
    requireparent?: boolean;
    required_names?: string[];
    required_categories?: string[];
  },
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

export function wareFitsVehicleMod(
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
export function weaponDetailsMatch(weapon: { name: string; ammo?: string }, expr: string) {
  const ammo = weapon.ammo || "";
  const name = weapon.name || "";
  let text = expr;
  text = text.replace(/contains\(\s*ammo\s*,\s*'([^']*)'\s*\)/g, (_, needle: string) =>
    ammo.includes(needle) ? "true" : "false",
  );
  text = text.replace(/contains\(\s*ammo\s*,\s*"([^"]*)"\s*\)/g, (_, needle: string) =>
    ammo.includes(needle) ? "true" : "false",
  );
  text = text.replace(/name\s*!=\s*'([^']*)'/g, (_, value: string) =>
    name !== value ? "true" : "false",
  );
  text = text.replace(/name\s*=\s*'([^']*)'/g, (_, value: string) =>
    name === value ? "true" : "false",
  );
  if (!/^(true|false|and|or|\(|\)|\s)+$/i.test(text)) return false;
  try {
    return Function(
      `"use strict"; return (${text.replace(/\band\b/g, "&&").replace(/\bor\b/g, "||")});`,
    )();
  } catch {
    return false;
  }
}

export function ammoFits(
  ammo: { category?: string; ammo_weapon_types?: string[]; weapon_details?: string },
  weapon: { name: string; ammo?: string; weapon_type?: string },
) {
  if (ammo.category !== "Ammunition") return false;
  if (ammo.weapon_details) return weaponDetailsMatch(weapon, ammo.weapon_details);
  const types = ammo.ammo_weapon_types || [];
  if (!types.length) return false;
  return types.includes(weapon.weapon_type || "");
}

export function weaponLine(
  item: {
    type?: string;
    accuracy?: string;
    damage?: string;
    ap?: string;
    mode?: string;
    ammo?: string;
    reach?: string;
    rc?: string;
  },
  ui: UiFn,
) {
  const bits: string[] = [];
  if (item.type) bits.push(ui(item.type === "Melee" ? "fmt.melee" : "fmt.ranged"));
  if (item.accuracy && item.accuracy !== "0") bits.push(`Acc ${item.accuracy}`);
  if (item.damage) bits.push(item.damage);
  if (item.ap && item.ap !== "-" && item.ap !== "0") bits.push(`AP ${item.ap}`);
  if (item.rc && item.rc !== "0") bits.push(`RC ${item.rc}`);
  if (item.mode && item.mode !== "0") bits.push(item.mode);
  if (item.ammo && item.ammo !== "0") bits.push(item.ammo);
  if (item.reach && item.reach !== "0") bits.push(`Reach ${item.reach}`);
  return bits.join(" / ");
}
const DETAIL_GROUPS: Record<string, [boolean, boolean]> = {
  OR: [true, false],
  NOR: [true, true],
  AND: [false, false],
  NAND: [false, true],
};
const LESS_OPS = ["LESSTHANEQUALS", "LESSTHANEQUALTO", "LESSTHANOREQUALS", "LESSTHANOREQUALTO"];
const GTE_OPS = [
  "GREATERTHANEQUALS",
  "GREATERTHANOREQUALS",
  "GREATERTHANEQUALTO",
  "GREATERTHANOREQUALTO",
  ">=",
];

type DetailFields = Record<string, unknown>;

const asInt = (text: string) => (/^[+-]?\d+$/.test(text) ? Number(text) : null);

function detailLeafMet(node: WeaponDetailsNode, fields: DetailFields): boolean {
  let invert = node.not;
  const raw = fields[node.tag];
  if (node.children) {
    return (
      raw != null &&
      typeof raw === "object" &&
      !Array.isArray(raw) &&
      weaponDetailsMet(node.children, raw as DetailFields, Boolean(node.or)) !== invert
    );
  }
  if (Array.isArray(raw)) return raw.some((item) => detailLeafMet(node, { [node.tag]: item }));
  const target = raw == null ? "" : String(raw).trim();
  let op = node.op || "==";
  if (op === "exists") return Boolean(target) !== invert;
  // no such field to test: Chummer's loop over it finds nothing
  if (!target) return false;
  const want = (node.value || "").trim();
  if (!want) return invert;
  op = op.toUpperCase();
  if (["DOESNOTEQUAL", "NOTEQUALS", "!=", "<>"].includes(op)) return (target === want) === invert;
  if (op === "LIKE" || op === "CONTAINS")
    return target.toLowerCase().includes(want.toLowerCase()) !== invert;
  if (op === "LESSTHAN" || LESS_OPS.includes(op)) {
    invert = !invert;
    op = op === "LESSTHAN" ? ">=" : ">";
  }
  const t = asInt(target);
  const w = asInt(want);
  if (op === "GREATERTHAN" || op === ">") return (t !== null && w !== null && t > w) !== invert;
  if (GTE_OPS.includes(op)) return (t !== null && w !== null && t >= w) !== invert;
  return (target === want) !== invert;
}

/** Whether a weapon (its catalog fields) passes a `<weapondetails>` tree, the
 *  way Chummer's `ProcessFilterOperationNode` reads it; mirrors
 *  `weapon_details_met` on the server. */
export function weaponDetailsMet(
  nodes: WeaponDetailsNode[],
  fields: DetailFields,
  isOr = false,
): boolean {
  for (const node of nodes) {
    const group = DETAIL_GROUPS[node.tag.toUpperCase()];
    let result: boolean;
    if (group) {
      result = weaponDetailsMet(node.children || [], fields, group[0]) !== (node.not !== group[1]);
    } else if (node.tag.toUpperCase() === "NONE") {
      result = node.not;
    } else {
      result = detailLeafMet(node, fields);
    }
    if (isOr && result) return true;
    if (!isOr && !result) return false;
  }
  return !isOr;
}

export function accessoryFits(
  acc: {
    mounts?: string[];
    purchasable?: boolean;
    specialmodification?: boolean;
    special_modification_cost?: number;
    required?: WeaponConstraints;
    forbidden?: WeaponConstraints;
  },
  weapon: DetailFields & { mounts?: string[] },
  installedNames: string[],
  specialMod?: { used?: number; max?: number },
) {
  const isSpecial = Boolean(acc.specialmodification);
  if (acc.purchasable === false && !isSpecial) return false;
  if (isSpecial) {
    const max = Number(specialMod?.max || 0);
    const used = Number(specialMod?.used || 0);
    const cost = Math.max(1, Number(acc.special_modification_cost || 1));
    if (max <= 0 || used + cost > max) return false;
  }
  const mounts = acc.mounts || [];
  const weaponMounts = new Set(weapon.mounts || []);
  if (mounts.length && !mounts.some((mount) => weaponMounts.has(mount) || mount === "Internal"))
    return false;
  const installed = new Set(installedNames);
  if (acc.forbidden?.accessories?.some((name) => installed.has(name))) return false;
  const fields = { ...weapon, accessorymounts: { mount: weapon.mounts || [] } };
  const required = acc.required?.details || [];
  if (required.length && !weaponDetailsMet(required, fields)) return false;
  const forbidden = acc.forbidden?.details || [];
  if (forbidden.length && weaponDetailsMet(forbidden, fields)) return false;
  return true;
}

export function armorModFits(
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

const optionIndex = new WeakMap<object, Map<string, string[]>>();

/** What a bought row's pick can be — the skills a skillsoft covers, the models
 *  a `[Model]` autosoft is for. Taken from the catalog entry by id rather
 *  than carried on every derived row: one Maneuvering Autosoft's model list is
 *  ~9 KB, and it used to come back on every recompute, once per copy owned. */
export function catalogExtraOptions(
  list: readonly { id: string; extra_options?: string[] }[] | undefined,
  id: string,
): string[] {
  if (!list) return [];
  let index = optionIndex.get(list);
  if (!index) {
    index = new Map(list.map((row) => [row.id, row.extra_options || []]));
    optionIndex.set(list, index);
  }
  return index.get(id) || [];
}
