// Armor, weapons, matrix devices, gear and drugs: row shapes listed in `Derived` (../derived.ts).

import type { Notice } from "@/lib/engine-notices";

export interface SpecialArmor {
  fire?: number;
  cold?: number;
  electricity?: number;
  radiation?: number;
  sonic?: number;
  toxin_contact?: number;
  toxin_ingestion?: number;
  toxin_inhalation?: number;
  toxin_injection?: number;
  pathogen_contact?: number;
  pathogen_ingestion?: number;
  pathogen_inhalation?: number;
  pathogen_injection?: number;
  immunities?: {
    toxin_contact?: boolean;
    toxin_inhalation?: boolean;
    pathogen_contact?: boolean;
    pathogen_inhalation?: boolean;
  };
}

export interface LimitModifier {
  limit: "physical" | "mental" | "social" | string;
  value: number;
  condition?: string;
  condition_label?: Notice | null;
  source?: string;
}

export interface InstalledArmorMod {
  id: string;
  mod_id: string;
  name: string;
  category?: string;
  parent_id?: string | null;
  included?: boolean;
  rating: number;
  rating_max: number;
  nuyen: number;
  capacity_cost?: number;
  armor?: string;
  unique?: string;
  wireless?: boolean;
  has_wireless?: boolean;
  avail?: string;
  source?: string;
  special_armor?: SpecialArmor;
  limit_modifiers?: LimitModifier[];
  /** Custom Fit (Stack) `<selectarmor>`: the mod names an armor to stack with */
  select_armor?: boolean;
  stack_with?: string;
}

export interface InstalledArmor {
  /** `Variable(lo-hi)`: the range the player prices it within. */
  cost_range?: [number, number] | null;
  id: string;
  armor_id: string;
  name: string;
  category: string;
  armor: string;
  armor_value: number;
  additive: boolean;
  /** `+N` a Custom Fit (Stack) piece adds to the armor it stacks with */
  armoroverride?: string;
  rating: number;
  rating_max: number;
  equipped: boolean;
  wireless?: boolean;
  has_wireless?: boolean;
  nuyen: number;
  avail?: string;
  source?: string;
  contributes?: number;
  armorcapacity?: string;
  addmodcategories?: string[];
  mods?: InstalledArmorMod[];
  /** gear carried in it (a Holster, a Medkit) */
  gear?: InstalledGear[];
  capacity_used?: number;
  capacity_max?: number;
}

export interface InstalledWeapon {
  id: string;
  weapon_id: string;
  name: string;
  category: string;
  type: string;
  weapon_type?: string;
  accuracy: string;
  /** `Physical` / `Physical-1` before the engine put the limit in. */
  accuracy_formula?: string;
  /** `({STR}+5)P` before the engine put the body's STR in. */
  damage_formula?: string;
  reach: string;
  damage: string;
  ap: string;
  mode: string;
  ammo: string;
  rc?: string;
  rc_total?: number;
  conceal?: string;
  range?: string;
  alt_range?: string;
  mounts?: string[];
  qty: number;
  nuyen: number;
  accessories?: InstalledWeaponAccessory[];
  ammo_gear?: InstalledGear[];
  loaded_ammo_id?: string;
  from_gear?: boolean;
  source_gear_id?: string;
  from_ware?: boolean;
  source_ware_id?: string;
  /** Which ware tab owns the implant that grants it: "cyberware" or "bioware". */
  ware_kind?: string;
  /** A shield: armour that is also a weapon, deleted by dropping the armour. */
  from_armor?: boolean;
  source_armor_id?: string;
  /** Born with it (a `<naturalweapon>` grant) — nothing to buy, install or drop. */
  natural?: boolean;
  natural_source?: string;
  useskill?: string;
  limb_str?: number | null;
  limb_agi?: number | null;
  mounted_on?: string;
  mounted_label?: string;
  focus_dice?: number;
  category_dice?: number;
  avail?: string;
  source?: string;
}

export interface InstalledWeaponAccessory {
  id: string;
  accessory_id: string;
  name: string;
  parent_id?: string | null;
  included?: boolean;
  mount?: string;
  rating?: number;
  rating_max?: number;
  nuyen: number;
  accuracy?: string;
  rc?: string;
  avail?: string;
  source?: string;
  specialmodification?: boolean;
  special_modification_cost?: number;
}

export interface InstalledCommlink {
  id: string;
  gear_id: string;
  name: string;
  category?: string;
  rating: number;
  rating_max: number;
  qty?: number;
  device_rating: number;
  /** from a plugged-in Attack / Stealth Dongle (DT p.61); 0 on a bare commlink */
  attack?: number;
  sleaze?: number;
  dataprocessing: number;
  firewall: number;
  nuyen: number;
  apps?: InstalledProgram[];
  avail?: string;
  source?: string;
}

export interface InstalledMatrixDevice {
  id: string;
  gear_id: string;
  name: string;
  category?: string;
  rating: number;
  rating_max: number;
  device_rating: number;
  attack?: number;
  sleaze?: number;
  dataprocessing: number;
  firewall: number;
  programs?: number;
  program_used?: number;
  program_max?: number;
  nuyen: number;
  avail?: string;
  source?: string;
  array?: number[];
  array_order?: string[];
  can_reorder?: boolean;
}

export interface InstalledOptics {
  id: string;
  gear_id: string;
  name: string;
  category: string;
  rating: number;
  rating_max: number;
  parent_id?: string | null;
  included?: boolean;
  plugin?: boolean;
  nuyen: number;
  capacity_cost?: number;
  capacity_used?: number;
  capacity_max?: number;
  /** what it takes of the armor it is carried in */
  armor_capacity?: number;
  /** on a row carried in armor: the list it lives in */
  bucket?: "gear" | "optics" | "sensors";
  addoncategories?: string[];
  requireparent?: boolean;
  device_rating?: number;
  avail?: string;
  source?: string;
}

export interface InstalledGear extends InstalledOptics {
  /** `Variable(lo-hi)`: the range the player prices it within. */
  cost_range?: [number, number] | null;
  /** a Custom Item's own name */
  custom_name?: string;
  label?: string;
  qty: number;
  extra?: string;
  needs_extra?: boolean;
  extra_kind?: string;
  /** the translation kind of a pick — see `gear_extra_skill_kind` */
  extra_skill_kind?: "skill" | "knowledge_skill" | "";
  required_names?: string[];
  required_categories?: string[];
  ammo_weapon_types?: string[];
  costfor?: number;
  add_weapon?: string;
  add_weapon_id?: string;
  loaded?: boolean;
  is_drug?: boolean;
  active?: boolean;
  drug_speed?: string;
  drug_vectors?: string[];
  drug_duration?: string;
  drug_effect?: Notice[];
  /** `<addgear>`: the quality that handed this row over (Dead SIN). */
  granted_by?: string;
}

export interface InstalledProgram {
  /** `Variable(lo-hi)`: the range the player prices it within. */
  cost_range?: [number, number] | null;
  id: string;
  gear_id: string;
  name: string;
  category: string;
  rating: number;
  rating_max: number;
  parent_id?: string | null;
  /** came with its host (a Nixdorf Sekretar's Agent): free */
  included?: boolean;
  extra?: string;
  label?: string;
  needs_extra?: boolean;
  extra_kind?: string;
  /** the translation kind of a pick — see `gear_extra_skill_kind` */
  extra_skill_kind?: "skill" | "knowledge_skill" | "";
  nuyen: number;
  program_host?: string;
  avail?: string;
  source?: string;
}

export interface ActiveDrug {
  name: string;
  category: string;
  speed?: string;
  vectors?: string[];
  duration?: Notice | null;
  effect?: Notice[];
}

export interface CustomDrugComponentRow {
  component_id: string;
  name: string;
  category: string;
  level: number;
}

/** A mixed drug as the engine resolved it: the totals a bought drug would read
 *  off its catalog entry, summed from the components instead. */
export interface CustomDrug {
  id: string;
  name: string;
  grade: string;
  qty: number;
  active: boolean;
  nuyen: number;
  avail: string;
  addiction_rating: number;
  addiction_threshold: number;
  crash_damage: number;
  /** Onset in seconds; under 3 is immediate (a Combat Turn). */
  speed: number;
  /** Duration in seconds; 0 when no component gives one. */
  duration: number;
  infos: string[];
  components: CustomDrugComponentRow[];
  effect?: Notice[];
  source?: string;
  page?: string;
}
