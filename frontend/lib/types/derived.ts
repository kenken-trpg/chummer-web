import type { MentorChoice } from "./installs";

export interface InstalledMartialArtTechnique {
  id: string;
  name: string;
  free: boolean;
  karma: number;
  source?: string;
  page?: string;
}

export interface InstalledMartialArt {
  id: string;
  art_id: string;
  name: string;
  source?: string;
  page?: string;
  style_karma: number;
  karma: number;
  free?: boolean;
  locked?: boolean;
  source_quality_id?: string | null;
  techniques: InstalledMartialArtTechnique[];
  technique_options: string[];
  technique_max?: number | null;
}

export interface InstalledContact {
  id: string;
  name: string;
  role?: string;
  connection: number;
  loyalty: number;
  cost: number;
  billable?: number;
  connection_max: number;
  loyalty_max: number;
  loyalty_min?: number;
  group?: boolean;
  free?: boolean;
  forced_loyalty?: number | null;
  source_quality_id?: string | null;
  locked?: boolean;
  black_market_pipeline?: boolean;
}

export interface InstalledExoticSkill {
  id: string;
  skill_name: string;
  extra: string;
  label: string;
  rating: number;
  rating_max: number;
  attribute: string;
  category: string;
  options: string[];
  source?: string;
}

export interface InstalledSpell {
  id: string;
  spell_id: string;
  name: string;
  category?: string;
  kind?: "spell" | "ritual" | "enchantment";
  useskill?: string;
  has_force?: boolean;
  type?: string;
  range?: string;
  duration?: string;
  descriptor?: string;
  dv: string;
  damage?: string;
  damage_mod?: number;
  required?: string[];
  source?: string;
  page?: string;
  free: boolean;
  karma: number;
  barehanded_adept?: boolean;
  alchemical?: boolean;
  granted?: boolean;
  focus_bonus?: number;
  spell?: SpellCastInfo | null;
}

export interface InstalledComplexForm {
  id: string;
  form_id: string;
  name: string;
  label?: string;
  target: string;
  duration: string;
  fv: string;
  extra?: string;
  needs_extra?: boolean;
  options?: string[];
  level: number;
  level_min: number;
  level_max: number;
  fade: number | null;
  fade_code?: "S" | "P" | null;
  physical?: boolean;
  resist: number;
  resist_attrs: string;
  free: boolean;
  karma: number;
  test?: MagicTestInfo;
  source?: string;
  page?: string;
}

export interface InstalledSprite {
  id: string;
  sprite_id: string;
  name: string;
  level: number;
  level_max: number;
  services: number;
  registered?: boolean;
  hits?: number | null;
  opposed_hits?: number | null;
  test?: MagicTestInfo;
  attributes?: Record<string, number>;
  matrix?: {
    attack: number;
    sleaze: number;
    dataprocessing: number;
    firewall: number;
    initiative: number;
  };
  powers?: string[];
  skills?: { name: string; attribute?: string; rating: number }[];
  source?: string;
  page?: string;
}

export interface TraditionInfo {
  id: string;
  name: string;
  drain: string;
  drain_attrs: string[];
  spirits?: Record<string, string>;
  source?: string;
  page?: string;
}

export interface InstalledLifestyleQuality {
  id: string;
  quality_id: string;
  name: string;
  category?: string;
  lp: number;
  cost: number;
  free?: boolean;
  from_freegrid?: boolean;
  multiplier?: number;
  extra?: string;
  needs_extra?: boolean;
  source?: string;
  page?: string;
}

export interface SpecialArmor {
  fire?: number;
  cold?: number;
  electricity?: number;
  radiation?: number;
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
  condition_label?: string;
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
}

export interface InstalledArmor {
  id: string;
  armor_id: string;
  name: string;
  category: string;
  armor: string;
  armor_value: number;
  additive: boolean;
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
  device_rating: number;
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
  addoncategories?: string[];
  requireparent?: boolean;
  device_rating?: number;
  avail?: string;
  source?: string;
}

export interface InstalledGear extends InstalledOptics {
  label?: string;
  qty: number;
  extra?: string;
  needs_extra?: boolean;
  extra_kind?: string;
  extra_options?: string[];
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
  drug_effect?: string;
}

export interface InstalledLifestyle {
  id: string;
  lifestyle_id: string;
  name: string;
  months: number;
  increment: string;
  monthly: number;
  base_monthly?: number;
  quality_monthly?: number;
  multiplier_pct?: number;
  nuyen: number;
  lp_used?: number;
  lp_max?: number;
  dice?: number;
  qualities?: InstalledLifestyleQuality[];
  source?: string;
}

export interface InstalledProgram {
  id: string;
  gear_id: string;
  name: string;
  category: string;
  rating: number;
  rating_max: number;
  parent_id?: string | null;
  extra?: string;
  label?: string;
  needs_extra?: boolean;
  extra_kind?: string;
  extra_options?: string[];
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
  duration?: string;
  effect?: string;
}

export interface InstalledVehicleMod {
  id: string;
  mod_id: string;
  name: string;
  category: string;
  parent_id?: string | null;
  included?: boolean;
  rating: number;
  rating_max: number;
  slots: number;
  nuyen: number;
  avail?: string;
  source?: string;
  capacity_used?: number;
  capacity_max?: number;
  subsystems?: string[];
  cyberware?: InstalledWare[];
}

export interface InstalledWeaponMount {
  id: string;
  parent_id?: string | null;
  size_id: string;
  visibility_id?: string;
  flexibility_id?: string;
  control_id?: string;
  included?: boolean;
  name: string;
  label: string;
  slots: number;
  nuyen: number;
  weapon_install_id?: string | null;
  weapon_name?: string;
  allowedweapons?: string;
  source?: string;
}

export interface InstalledDrone {
  id: string;
  gear_id: string;
  name: string;
  category: string;
  handling: string;
  speed: string;
  accel: string;
  body: string;
  armor: string;
  pilot: string;
  sensor: string;
  seats?: string;
  nuyen: number;
  slots_used?: number;
  slots_max?: number;
  slot_tracks?: { category: string; label: string; used: number; max: number }[];
  mods?: InstalledVehicleMod[];
  weapon_mounts?: InstalledWeaponMount[];
  sensors?: InstalledOptics[];
  gear?: InstalledGear[];
  avail?: string;
  source?: string;
}

export interface MagicTestInfo {
  skill: string;
  rating: number;
  attr: string;
  attr_value: number;
  bonus: number;
  pool: number;
  defaulted?: boolean;
  missing?: boolean;
  force: number;
  limit: number;
  limit_name?: string;
  vs: number;
  hits?: number | null;
  opposed_hits?: number | null;
  net?: number | null;
  drain?: number | null;
  drain_code?: "S" | "P" | null;
  physical?: boolean;
  days?: number | null;
}

export interface InstalledSpirit {
  id: string;
  spirit_id: string;
  name: string;
  role?: string;
  role_label?: string;
  force: number;
  force_max: number;
  services: number;
  nuyen: number;
  bound?: boolean;
  hits?: number | null;
  opposed_hits?: number | null;
  test?: MagicTestInfo;
  attributes?: Record<string, number>;
  powers?: string[];
  optionalpowers?: string[];
  skills?: { name: string; attribute?: string; rating: number }[];
  weaknesses?: string[];
  source?: string;
  page?: string;
}

export interface InstalledFocus {
  id: string;
  gear_id: string;
  name: string;
  force: number;
  force_max: number;
  nuyen: number;
  karma: number;
  crafted?: boolean;
  formula_bought?: boolean;
  formula_nuyen?: number;
  reagent_nuyen?: number;
  retail_nuyen?: number;
  hits?: number | null;
  opposed_hits?: number | null;
  test?: MagicTestInfo;
  formula_test?: MagicTestInfo;
  effect?: string;
  formula?: { id?: string; name?: string; cost?: string } | null;
  needs_weapon?: boolean;
  weapon_type?: string;
  weapon_id?: string;
  weapon_name?: string;
  weapon_dice?: number;
  weapon_options?: { id: string; name: string }[];
  source?: string;
  page?: string;
}

export interface InstalledAdeptPower {
  id: string;
  power_id: string;
  name: string;
  rating: number;
  total_rating?: number;
  free_levels?: number;
  rating_min: number;
  rating_max: number;
  extra: string;
  cost: number;
  full_cost?: number;
  discounted?: boolean;
  can_discount?: boolean;
  select?: "skill" | "attribute" | "spell" | null;
  options: string[];
  source?: string;
  page?: string;
  notes?: string[];
  free_only?: boolean;
  spell?: SpellCastInfo | null;
}

export interface SpellCastInfo {
  spell_id: string;
  name: string;
  category?: string;
  type?: string;
  range?: string;
  duration?: string;
  descriptor?: string;
  dv: string;
  damage?: string;
  damage_mod?: number;
  drain_mod?: number;
  force: number;
  force_min: number;
  force_max: number;
  drain: number | null;
  drain_code: "S" | "P" | null;
  physical: boolean;
  resist: number;
  resist_attrs: string;
  barehanded_adept?: boolean;
}

export interface InstalledQiFocus {
  id: string;
  rating: number;
  rating_min: number;
  rating_max: number;
  power_id: string;
  name: string;
  power_rating: number;
  power_rating_max: number;
  extra: string;
  select?: "skill" | "attribute" | "spell" | null;
  options: string[];
  nuyen: number;
  karma: number;
  source?: string;
}

export interface MentorInfo {
  id: string;
  name: string;
  advantage: string;
  disadvantage: string;
  source?: string;
  choices: MentorChoice[];
}

export interface EnhancementInfo {
  id: string;
  name: string;
  power?: string | null;
  karma: number;
  source?: string;
  page?: string;
  ok?: boolean;
}

export interface InstalledWare {
  id: string;
  ware_id: string;
  name: string;
  category: string;
  rating: number;
  grade: string;
  wireless: boolean;
  parent_id?: string | null;
  included?: boolean;
  essence: number;
  nuyen: number;
  capacity_used?: number;
  capacity_max?: number;
  rating_min?: number;
  rating_max?: number;
  limb_str?: number;
  limb_agi?: number;
  limb_armor?: number;
  selectside?: boolean;
  side?: string | null;
  avail?: string;
  device_rating?: number;
  source?: string;
}
