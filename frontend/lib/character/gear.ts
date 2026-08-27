import type { WareCatalogItem, WareInstall } from "@/lib/types";
import { DEFAULT_ARRAY_ORDER, VEHICLE_INTERIOR_CATS } from "@/lib/character/constants";
import { removeWareTree } from "@/lib/character/ware";

export function swapMatrixOrder(order: string[] | undefined, fromKey: string, toPos: number): string[] {
  const next = [...(order && order.length === 4 ? order : DEFAULT_ARRAY_ORDER)];
  const fromPos = next.indexOf(fromKey);
  if (fromPos < 0 || toPos < 0 || toPos >= next.length || fromPos === toPos) return next;
  [next[fromPos], next[toPos]] = [next[toPos], next[fromPos]];
  return next;
}

export function vehicleFits(
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

export function vehicleForbidden(
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

export function dropDrone(ch: {
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

export function dropTree<T extends { id?: string; parent_id?: string | null }>(rows: T[], id: string): T[] {
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

export function vehicleInteriorFits(
  mod: { category: string; required_categories?: string[] },
) {
  if (VEHICLE_INTERIOR_CATS.has(mod.category)) return true;
  return (mod.required_categories || []).some((cat) => cat && cat !== "Custom" && cat === "Commlinks");
}

export function miscFits(
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
export function weaponDetailsMatch(
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

export function weaponLine(item: { type?: string; accuracy?: string; damage?: string; ap?: string; mode?: string; ammo?: string; reach?: string; rc?: string }) {
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
export function accessoryFits(
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
