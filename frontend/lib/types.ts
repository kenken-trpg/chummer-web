export interface QualityReqNode {
  tag: string;
  name?: string;
  val?: number;
  type?: string;
  value?: number;
  children?: QualityReqNode[];
}

export interface SkillPickSlot {
  key: string;
  source: string;
  source_kind: string;
  source_id: string;
  picked: string;
  bonus: number;
  max: number;
  options: string[];
  knowledgeskills: boolean;
}

export interface AdeptPowerInstall {
  id?: string;
  power_id: string;
  rating: number;
  extra?: string | null;
  discounted?: boolean;
  force?: number | null;
}

export interface SpellInstall {
  id?: string;
  spell_id: string;
  force?: number | null;
}

export interface ComplexFormInstall {
  id?: string;
  form_id: string;
  level?: number | null;
  extra?: string | null;
}

export interface SpriteInstall {
  id?: string;
  sprite_id: string;
  level?: number;
  services?: number;
  registered?: boolean;
  hits?: number | null;
  opposed_hits?: number | null;
}

export interface ContactInstall {
  id?: string;
  name: string;
  role?: string | null;
  connection?: number;
  loyalty?: number;
  group?: boolean;
  free?: boolean;
  forced_loyalty?: number | null;
  force_group?: boolean;
  source_quality_id?: string | null;
  free_connection?: number;
  free_loyalty?: number;
}

export interface MartialArtInstall {
  id?: string;
  art_id: string;
  techniques?: string[];
  free?: boolean;
  source_quality_id?: string | null;
}

export interface InitiationChoice {
  id?: string;
  grade: number;
  kind: "metamagic" | "art" | string;
  option_id: string;
}

export interface SubmersionChoice {
  id?: string;
  grade: number;
  echo_id: string;
  extra?: string | null;
}

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

export interface MartialArtCatalogItem {
  id: string;
  name: string;
  cost: number;
  techniques: string[];
  source?: string;
  page?: string;
  is_quality?: boolean;
  all_techniques?: boolean;
  spec_options?: { skill: string; spec: string }[];
}

export interface ExoticSkillInstall {
  id?: string;
  skill_name: string;
  extra?: string;
  rating?: number;
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
  required?: string[];
  source?: string;
  page?: string;
  free: boolean;
  karma: number;
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

export interface SpiritInstall {
  id?: string;
  spirit_id: string;
  force?: number;
  services?: number;
  bound?: boolean;
  hits?: number | null;
  opposed_hits?: number | null;
}

export interface FocusInstall {
  id?: string;
  gear_id: string;
  force?: number;
  crafted?: boolean;
  formula_bought?: boolean;
  hits?: number | null;
  opposed_hits?: number | null;
  extra?: string | null;
}

export interface ArmorInstall {
  id?: string;
  armor_id: string;
  rating?: number;
  equipped?: boolean;
}

export interface ArmorModInstall {
  id?: string;
  mod_id: string;
  parent_id?: string | null;
  included?: boolean;
  rating?: number;
}

export interface WeaponInstall {
  id?: string;
  weapon_id: string;
  qty?: number;
  loaded_ammo_id?: string | null;
}

export interface WeaponAccessoryInstall {
  id?: string;
  accessory_id: string;
  parent_id?: string | null;
  included?: boolean;
  rating?: number;
  mount?: string;
}

export interface CommlinkInstall {
  id?: string;
  gear_id: string;
  rating?: number;
}

export interface GearInstall {
  id?: string;
  gear_id: string;
  rating?: number;
  qty?: number;
  parent_id?: string | null;
  included?: boolean;
  capacity_override?: string | null;
  array_order?: string[];
  extra?: string | null;
}

export interface LifestyleInstall {
  id?: string;
  lifestyle_id: string;
  months?: number;
  quality_ids?: string[];
  quality_extras?: Record<string, string>;
}

export interface LifestyleQualityCatalogItem {
  id: string;
  name: string;
  category: string;
  lp: number;
  cost: number;
  multiplier: number;
  allowed: string[];
  allow_multiple?: boolean;
  needs_extra?: boolean;
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
  conceal?: string;
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

export interface ArmorCatalogItem {
  id: string;
  name: string;
  category: string;
  armor: string;
  armorcapacity: string;
  avail: string;
  cost: string;
  minrating: number;
  maxrating: number;
  additive: boolean;
  addmodcategories?: string[];
  source: string;
  page: string;
}

export interface ArmorModCatalogItem {
  id: string;
  name: string;
  category: string;
  armor: string;
  armorcapacity: string;
  avail: string;
  cost: string;
  minrating: number;
  maxrating: number;
  purchasable?: boolean;
  unique?: string;
  required_names?: string[];
  required_mods?: string[];
  source: string;
  page: string;
}

export interface WeaponCatalogItem {
  id: string;
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
  conceal?: string;
  mounts?: string[];
  avail: string;
  cost: string;
  source: string;
  page: string;
  from_gear?: boolean;
  add_gear_id?: string;
}

export interface WeaponAccessoryCatalogItem {
  id: string;
  name: string;
  mounts: string[];
  avail: string;
  cost: string;
  purchasable?: boolean;
  accuracy?: string;
  rc?: string;
  minrating: number;
  maxrating: number;
  required?: {
    names?: string[];
    categories?: string[];
    types?: string[];
    conceal_lte?: number | null;
    accessories?: string[];
  };
  forbidden?: {
    names?: string[];
    categories?: string[];
    types?: string[];
    conceal_lte?: number | null;
    accessories?: string[];
  };
  source: string;
  page: string;
}

export interface CommlinkCatalogItem {
  id: string;
  name: string;
  category?: string;
  cost: string;
  avail: string;
  minrating: number;
  maxrating: number;
  devicerating: string;
  dataprocessing: string;
  firewall: string;
  source: string;
  page: string;
}

export interface MatrixDeviceCatalogItem extends CommlinkCatalogItem {
  category?: string;
  attack?: string;
  sleaze?: string;
  attributearray?: string;
  programs?: string;
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

export interface ProgramCatalogItem {
  id: string;
  name: string;
  category: string;
  cost: string;
  avail: string;
  minrating: number;
  maxrating: number;
  requireparent?: boolean;
  program_host?: "cyberdecks" | "rccs";
  needs_extra?: boolean;
  extra_kind?: string;
  extra_options?: string[];
  source: string;
  page: string;
}

export interface OpticsCatalogItem {
  id: string;
  name: string;
  category: string;
  cost: string;
  avail: string;
  minrating: number;
  maxrating: number;
  capacity?: string;
  plugin?: boolean;
  requireparent?: boolean;
  addoncategories?: string[];
  source: string;
  page: string;
}

export interface GearCatalogItem extends OpticsCatalogItem {
  needs_extra?: boolean;
  extra_kind?: string;
  extra_options?: string[];
  required_names?: string[];
  required_categories?: string[];
  ammo_weapon_types?: string[];
  costfor?: number;
  weapon_details?: string;
  add_weapon?: string;
  add_weapon_id?: string;
}

export interface LifestyleCatalogItem {
  id: string;
  name: string;
  cost: number;
  dice: number;
  lp?: number;
  multiplier?: number;
  increment: string;
  freegrids?: { name: string; select?: string }[];
  source: string;
  page: string;
}

export interface DroneCatalogItem {
  id: string;
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
  avail: string;
  cost: string;
  source: string;
  page: string;
}

export interface VehicleModInstall {
  id?: string;
  mod_id: string;
  parent_id?: string | null;
  included?: boolean;
  rating?: number;
}

export interface WeaponMountInstall {
  id?: string;
  parent_id?: string | null;
  size_id: string;
  visibility_id?: string;
  flexibility_id?: string;
  control_id?: string;
  included?: boolean;
  weapon_install_id?: string | null;
  allowedweapons?: string;
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

export interface VehicleModCatalogItem {
  id: string;
  name: string;
  category: string;
  cost: string;
  slots: string;
  avail: string;
  minrating: number;
  maxrating: number;
  purchasable?: boolean;
  capacity?: string;
  subsystems?: string[];
  required?: {
    names?: string[];
    category_contains?: string[];
    category_equals?: string[];
    body_lte?: number | null;
    body_gte?: number | null;
  };
  forbidden?: {
    names?: string[];
    category_contains?: string[];
    category_equals?: string[];
    body_lte?: number | null;
    body_gte?: number | null;
  };
  source: string;
  page: string;
}

export interface WeaponMountCatalogItem {
  id: string;
  name: string;
  category: string;
  cost: string;
  slots: string;
  avail: string;
  required?: {
    names?: string[];
    category_contains?: string[];
    category_equals?: string[];
    body_lte?: number | null;
    body_gte?: number | null;
  };
  source: string;
  page: string;
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

export interface SpiritCatalogItem {
  id: string;
  name: string;
  attributes?: Record<string, string>;
  powers?: string[];
  optionalpowers?: string[];
  skills?: { name: string; attribute?: string }[];
  weaknesses?: string[];
  source?: string;
  page?: string;
}

export interface FocusCatalogItem {
  id: string;
  name: string;
  maxrating: number;
  cost: string;
  effect?: string;
  needs_weapon?: boolean;
  weapon_type?: string;
  formula?: { id?: string; name?: string; cost?: string } | null;
  source?: string;
  page?: string;
}

export interface QiFocusInstall {
  id?: string;
  rating: number;
  power_id: string;
  extra?: string | null;
  power_rating?: number;
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
  force: number;
  force_min: number;
  force_max: number;
  drain: number | null;
  drain_code: "S" | "P" | null;
  physical: boolean;
  resist: number;
  resist_attrs: string;
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

export interface MentorChoice {
  name: string;
  set: string;
  audience: string;
  selected: boolean;
  extra: string;
  extra_options: string[];
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

export interface PowerCatalogItem {
  id: string;
  name: string;
  points: number;
  levels: boolean;
  maxlevels: number;
  extrapointcost: number;
  source: string;
  page: string;
  select?: "skill" | "attribute" | "spell" | null;
  required: string[];
  adeptway?: number;
  adeptwayrequires?: string[];
}

export interface WareInstall {
  id: string;
  ware_id: string;
  rating: number;
  grade: string;
  wireless: boolean;
  parent_id?: string | null;
  included?: boolean;
  side?: string | null;
}

export type PriorityLetter = "A" | "B" | "C" | "D" | "E";

export type PriorityCategory =
  | "Heritage"
  | "Attributes"
  | "Talent"
  | "Skills"
  | "Resources";

export interface Character {
  id: string;
  name: string;
  build_method?: "Priority" | "SumToTen" | "Karma" | string;
  priorities: Record<PriorityCategory, PriorityLetter>;
  metatype: string;
  metavariant: string | null;
  talent: string;
  attributes: Record<string, number>;
  skills: Record<string, number>;
  skill_groups: Record<string, number>;
  skill_specializations?: Record<string, string>;
  exotic_skills?: ExoticSkillInstall[];
  knowledge_skills: Record<string, number>;
  native_languages?: string[];
  knowledge_categories?: Record<string, string>;
  quality_ids: string[];
  quality_extras?: Record<string, string>;
  skill_picks?: Record<string, string>;
  cyberware: WareInstall[];
  bioware?: WareInstall[];
  adept_powers?: AdeptPowerInstall[];
  mystic_pp?: number;
  mentor_id?: string | null;
  mentor_choices?: string[];
  mentor_extras?: Record<string, string>;
  adept_enhancements?: string[];
  qi_foci?: QiFocusInstall[];
  spells?: SpellInstall[];
  spirits?: SpiritInstall[];
  complex_forms?: ComplexFormInstall[];
  sprites?: SpriteInstall[];
  foci?: FocusInstall[];
  armor?: ArmorInstall[];
  armor_mods?: ArmorModInstall[];
  weapons?: WeaponInstall[];
  weapon_accessories?: WeaponAccessoryInstall[];
  commlinks?: CommlinkInstall[];
  cyberdecks?: GearInstall[];
  rccs?: GearInstall[];
  optics?: GearInstall[];
  programs?: GearInstall[];
  apps?: GearInstall[];
  sensors?: GearInstall[];
  drones?: GearInstall[];
  vehicles?: GearInstall[];
  gear?: GearInstall[];
  vehicle_mods?: VehicleModInstall[];
  weapon_mounts?: WeaponMountInstall[];
  lifestyles?: LifestyleInstall[];
  contacts?: ContactInstall[];
  martial_arts?: MartialArtInstall[];
  initiate_grade?: number;
  initiations?: InitiationChoice[];
  submersion_grade?: number;
  submersions?: SubmersionChoice[];
  karma_nuyen?: number;
  career?: boolean;
  karma_earned?: number;
  nuyen_earned?: number;
  street_cred?: number;
  notoriety_bonus?: number;
  reward_log?: { id?: string; label?: string; karma?: number; nuyen?: number }[];
  career_baseline?: {
    attributes?: Record<string, number>;
    skills?: Record<string, number>;
    skill_groups?: Record<string, number>;
    knowledge_skills?: Record<string, number>;
    skill_specializations?: string[];
    exotic_skills?: Record<string, number>;
  } | null;
  tradition_id?: string | null;
  stream_id?: string | null;
  options?: {
    redliner_torso: boolean;
    redliner_skull: boolean;
  };
  derived: {
    errors: string[];
    warnings?: string[];
    build_method?: string;
    career?: boolean;
    karma_earned?: number;
    nuyen_earned?: number;
    nuyen_pool?: number;
    career_advancement_karma?: number;
    career_advancement_lines?: { kind?: string; label: string; amount: number }[];
    karma_spend_breakdown?: { kind?: string; label: string; amount: number }[];
    nuyen_spend_breakdown?: { kind?: string; label: string; amount: number }[];
    reward_log?: { id: string; label: string; karma: number; nuyen: number }[];
    street_cred?: number;
    notoriety_quality?: number;
    notoriety_bonus?: number;
    nuyen_amt?: number;
    nuyen_karma_max?: number;
    trustfund?: number;
    trustfund_label?: string;
    ambidextrous?: boolean;
    overclocker?: boolean;
    friends_in_high_places?: boolean;
    made_man?: boolean;
    black_market_discount?: boolean;
    black_market_category?: string;
    black_market_contact_id?: string;
    black_market_avail_bonus?: number;
    dealer_connection_categories?: string[];
    cyberware_ess_multiplier?: number;
    bioware_ess_multiplier?: number;
    skill_rating_max?: number;
    skill_group_max?: number;
    avail_limit?: number | null;
    device_rating_limit?: number | null;
    ware_attr_limit?: number | null;
    sum_to_ten?: {
      used: number;
      max: number;
      costs: Record<string, number>;
      unique?: boolean;
    };
    karma_chargen?: {
      enabled: boolean;
      pool: number;
      nuyen_karma: number;
      nuyen_karma_max: number;
      nuyen_per_karma: number;
      metatype: number;
      attributes: number;
      skills: number;
      knowledge: number;
      specializations: number;
      qualities: number;
      other: number;
    };
    totals: Record<string, number>;
    limits: { physical: number; mental: number; social: number };
    limit_modifiers?: LimitModifier[];
    condition_monitor: { physical: number; stun: number };
    initiative: { value: number; dice: number };
    movement: { walk: string; run: string; sprint: string };
    essence: number;
    armor: number;
    special_armor?: SpecialArmor;
    worn_armor?: string;
    armor_items?: InstalledArmor[];
    armor_mods?: InstalledArmorMod[];
    weapons?: InstalledWeapon[];
    weapon_accessories?: InstalledWeaponAccessory[];
    commlinks?: InstalledCommlink[];
    cyberdecks?: InstalledMatrixDevice[];
    rccs?: InstalledMatrixDevice[];
    optics?: InstalledOptics[];
    programs?: InstalledProgram[];
    apps?: InstalledProgram[];
    sensors?: InstalledOptics[];
    drones?: InstalledDrone[];
    vehicles?: InstalledDrone[];
    vehicle_mods?: InstalledVehicleMod[];
    weapon_mounts?: InstalledWeaponMount[];
    gear?: InstalledGear[];
    lifestyles?: InstalledLifestyle[];
    commlink?: InstalledCommlink | null;
    cyberdeck?: InstalledMatrixDevice | null;
    rcc?: InstalledMatrixDevice | null;
    lifestyle?: InstalledLifestyle | null;
    nuyen: number;
    nuyen_spent?: number;
    ware_attr_bonus?: Record<string, number>;
    karma: { pool: number; spent: number; remaining: number; negative?: { used: number; max: number | null } };
    points: Record<string, { used: number; max: number }>;
    knowledge_skills?: {
      name: string;
      category: string;
      attribute: string;
      rating: number;
      native: boolean;
      skillsoft?: number;
      spec?: string;
    }[];
    contacts?: InstalledContact[];
    contact_points?: { used: number; free: number; paid: number; karma?: number; karma_per_point?: number };
    martial_arts?: InstalledMartialArt[];
    martial_art_points?: {
      styles: number;
      style_max: number;
      techniques: number;
      technique_max: number;
      karma: number;
    };
    martial_spec_options?: Record<string, string[]>;
    unarmed_reach?: number;
    reach?: number;
    lifestyle_cost_mod?: number;
    notoriety?: number;
    fame?: number;
    public_awareness?: number;
    fatigue_resist?: number;
    spell_resistance?: number;
    spell_dice_pool?: { name: string; id?: string; bonus: number; source?: string }[];
    action_dice_pools?: { category?: string; name: string; bonus: number; source?: string }[];
    test_mods?: {
      memory?: number;
      composure?: number;
      judge_intentions?: number;
      judge_intentions_defense?: number;
      judge_intentions_offense?: number;
      dodge?: number;
      surprise?: number;
    };
    cm_recovery?: { physical: number; stun: number };
    essence_penalty?: number;
    attribute_max_bonus?: Record<string, number>;
    disabled_skills?: string[];
    disabled_skill_groups?: string[];
    blocked_default_categories?: string[];
    disabled_cyberware_grades?: string[];
    disabled_bioware_grades?: string[];
    native_language_limit?: number;
    prototype_transhuman_ess?: number;
    burnout_way?: boolean;
    initiate_grade?: number;
    initiation?: {
      grade: number;
      karma: number;
      choices: {
        id: string;
        grade: number;
        kind: string;
        option_id: string;
        name: string;
        karma: number;
        source?: string;
        page?: string;
      }[];
      metamagics: {
        id: string;
        metamagic_id: string;
        name: string;
        grade: number;
        adept?: boolean;
        magician?: boolean;
        source?: string;
        page?: string;
      }[];
      arts: {
        id: string;
        art_id: string;
        name: string;
        grade: number;
        source?: string;
        page?: string;
      }[];
    };
    submersion_grade?: number;
    submersion?: {
      grade: number;
      karma: number;
      choices: {
        id: string;
        grade: number;
        echo_id: string;
        name: string;
        extra?: string | null;
        karma: number;
        needs_extra?: boolean;
        source?: string;
        page?: string;
      }[];
      echoes: {
        id: string;
        echo_id: string;
        name: string;
        grade: number;
        extra?: string | null;
        source?: string;
        page?: string;
      }[];
    };
    skill_totals: Record<string, number>;
    skill_specializations?: Record<string, string>;
    exotic_skills?: InstalledExoticSkill[];
    skillsoft?: Record<string, number>;
    skillwires?: number;
    skilljack?: number;
    skill_bonus?: Record<string, number>;
    skill_group_bonus?: Record<string, number>;
    skill_category_bonus?: Record<string, number>;
    skill_bonus_notes?: Record<string, string[]>;
    skill_max_bonus?: Record<string, number>;
    skill_pick_slots?: SkillPickSlot[];
    power_points?: { used: number; max: number };
    adept_powers?: InstalledAdeptPower[];
    mystic_pp?: number;
    way_discount?: { used: number; max: number };
    mentor?: MentorInfo | null;
    needs_mentor?: boolean;
    qi_foci?: InstalledQiFocus[];
    foci?: InstalledFocus[];
    focus_limits?: { count: number; count_max: number; force: number; force_max: number };
    spirits?: InstalledSpirit[];
    complex_forms?: InstalledComplexForm[];
    complex_form_points?: { used: number; free: number; paid: number };
    sprites?: InstalledSprite[];
    stream?: { id: string; name: string; drain: string; drain_attrs: string[]; sprites?: string[]; source?: string; page?: string } | null;
    fade_resist?: { pool: number; attrs: string };
    living_persona?: {
      device_rating: number;
      attack: number;
      sleaze: number;
      dataprocessing: number;
      firewall: number;
      matrix_initiative_dice?: number;
    } | null;
    enhancements?: EnhancementInfo[];
    damage_resistance?: number;
    unarmed_dv?: number;
    unlock_skills?: string[];
    spells?: InstalledSpell[];
    spell_points?: { used: number; free: number; paid: number };
    tradition?: TraditionInfo | null;
    drain_resist?: { pool: number; attrs: string };
    enabled_tabs: string[];
    unimplemented_bonuses: { source: string; tag: string }[];
    qualities: {
      id: string;
      name: string;
      karma: number;
      category: string;
      source: string;
      needs_extra?: boolean;
      extra?: string;
      extra_kind?: string | null;
      select_options?: string[];
      selectside?: boolean;
      side?: string | null;
      free?: boolean;
    }[];
    native_language_limit?: number;
    blocked_default_categories?: string[];
    prototype_transhuman_ess?: number;
    burnout_way?: boolean;
    cyberware: InstalledWare[];
    bioware?: InstalledWare[];
    essence_lost_cyber?: number;
    essence_lost_bio?: number;
    ware_ranges?: Record<string, { min: number; max: number }>;
    limb_replace?: {
      count: number;
      parts: number;
      slots: { arm: number; leg: number; torso: number };
      str: number;
      agi: number;
      meat_str: number;
      meat_agi: number;
    } | null;
    limb_quality?: {
      count: number;
      pairs: number;
      limb_bonus: number;
      attribute_bonus: Record<string, number>;
      cm_physical: number;
      include?: string[];
    } | null;
    metatype_info: {
      name: string;
      attributes: Record<string, { min: number; max: number; aug: number }>;
    };
  };
}

export interface Catalog {
  metatypes: {
    name: string;
    id: string;
    category: string;
    karma?: number;
    attributes: Record<string, { min: number; max: number; aug: number }>;
    metavariants: { name: string; karma?: number; attributes: Record<string, { min: number; max: number; aug: number }> }[];
    source: string;
  }[];
  skills: {
    groups: string[];
    skills: {
      id: string;
      name: string;
      attribute: string;
      category: string;
      skillgroup: string | null;
      source: string;
      exotic?: boolean;
      specs?: string[];
    }[];
    knowledge: { name: string; category: string; attribute: string; source?: string; specs?: string[] }[];
  };
  qualities: {
    id: string;
    name: string;
    karma: number;
    category: string;
    source: string;
    page: string;
    bonus_tags: string[];
    forbidden_qualities?: string[];
    is_way?: boolean;
    needs_extra?: boolean;
    extra_kind?: string | null;
    select_options?: string[];
    chargenonly?: boolean;
    required_tree?: QualityReqNode[];
    forbidden_tree?: QualityReqNode[];
  }[];
  priority_table: Record<
    PriorityCategory,
    Record<
      PriorityLetter,
      {
        name: string;
        attribute_points?: number;
        skill_points?: number;
        skill_group_points?: number;
        nuyen?: number;
        metatypes: { name: string; special: number; variants: { name: string }[] }[];
        talents: { name: string; label?: string; value: number; spells?: number }[];
      }
    >
  >;
  translations: Record<string, string>;
  cyberware: WareCatalog;
  bioware: WareCatalog;
  powers?: PowerCatalogItem[];
  enhancements?: {
    id: string;
    name: string;
    power?: string | null;
    source: string;
    page: string;
    required?: { quality?: string[]; power?: string[] };
  }[];
  mentors?: { id: string; name: string; source: string; page: string; advantage: string }[];
  spells?: {
    id: string;
    name: string;
    category: string;
    dv: string;
    type?: string;
    range?: string;
    duration?: string;
    descriptor?: string;
    kind?: "spell" | "ritual" | "enchantment";
    useskill?: string;
    learnable?: boolean;
    required?: string[];
    source: string;
    page: string;
  }[];
  traditions?: TraditionInfo[];
  spirits?: SpiritCatalogItem[];
  complex_forms?: {
    id: string;
    name: string;
    target: string;
    duration: string;
    fv: string;
    needs_extra?: boolean;
    required?: string[];
    source: string;
    page: string;
  }[];
  streams?: {
    id: string;
    name: string;
    drain: string;
    drain_attrs: string[];
    sprites?: string[];
    source?: string;
    page?: string;
  }[];
  sprites?: SpiritCatalogItem[];
  foci?: FocusCatalogItem[];
  qi_focus?: { id: string; name: string; maxrating: number; cost: string; source: string; page: string } | null;
  armor?: ArmorCatalogItem[];
  armor_mods?: ArmorModCatalogItem[];
  weapons?: WeaponCatalogItem[];
  commlinks?: CommlinkCatalogItem[];
  cyberdecks?: MatrixDeviceCatalogItem[];
  rccs?: MatrixDeviceCatalogItem[];
  optics?: OpticsCatalogItem[];
  programs?: ProgramCatalogItem[];
  sensors?: OpticsCatalogItem[];
  gear?: GearCatalogItem[];
  drones?: DroneCatalogItem[];
  vehicles?: DroneCatalogItem[];
  vehicle_mods?: VehicleModCatalogItem[];
  weapon_mounts?: WeaponMountCatalogItem[];
  apps?: ProgramCatalogItem[];
  weapon_accessories?: WeaponAccessoryCatalogItem[];
  lifestyles?: LifestyleCatalogItem[];
  lifestyle_qualities?: LifestyleQualityCatalogItem[];
  drugs?: GearCatalogItem[];
  drug_grades?: GearCatalogItem[];
  martial_arts?: MartialArtCatalogItem[];
  martial_art_techniques?: { id: string; name: string; source?: string; page?: string }[];
  metamagics?: {
    id: string;
    name: string;
    adept: boolean;
    magician: boolean;
    repeatable: boolean;
    required: string[];
    source?: string;
    page?: string;
  }[];
  magic_arts?: { id: string; name: string; source?: string; page?: string }[];
  echoes?: {
    id: string;
    name: string;
    max_takes: number | null;
    needs_extra: boolean;
    source?: string;
    page?: string;
  }[];
  karma_talents?: { name: string; label: string; magic: number; resonance: number }[];
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
  selectside?: boolean;
  side?: string | null;
  avail?: string;
  device_rating?: number;
  source?: string;
}

export interface WareCatalogItem {
  id: string;
  name: string;
  category: string;
  ess: string;
  cost: string;
  capacity?: string;
  minrating: number;
  maxrating: number;
  minrating_expr?: string;
  maxrating_expr?: string;
  plugin: boolean;
  requireparent?: boolean;
  addtoparentess?: boolean;
  formula_rating?: boolean;
  allow_subsystems?: string[];
  has_wireless: boolean;
  forcegrade?: string | null;
  bannedgrades?: string[];
  required?: {
    bioware?: string[];
    cyberware?: string[];
    metatype?: string[];
    quality?: string[];
  };
  required_parent_names?: string[];
  limbslot?: string | null;
  selectside?: boolean;
  source: string;
  page: string;
}

export interface WareCatalog {
  grades: { name: string; ess: number; cost: number }[];
  items: WareCatalogItem[];
}
