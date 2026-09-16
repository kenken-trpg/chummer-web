import type { Notice } from "@/lib/engine-notices";
import type { MentorChoice, SkillPickSlot } from "./installs";

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

/** One power a spirit or sprite comes with, and what SR5 p.394 gives it.
 *  `type` is `M` / `P`; the rest are the words the data file uses (`Complex`,
 *  `LOS`, `Sustained`, …), or a formula the table spells out. */
export interface CritterPower {
  name: string;
  type?: string;
  action?: string;
  range?: string;
  duration?: string;
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
  powers?: CritterPower[];
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
  drug_effect?: Notice[];
  /** `<addgear>`: the quality that handed this row over (Dead SIN). */
  granted_by?: string;
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
  /** Points bought above the lifestyle's own, and how far each may go. */
  raised?: Record<"comforts" | "area" | "security", number>;
  raise_max?: Record<"comforts" | "area" | "security", number>;
  dice?: number;
  qualities?: InstalledLifestyleQuality[];
  source?: string;
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
  slot_tracks?: { category: string; used: number; max: number }[];
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
  role_label?: Notice | null;
  force: number;
  force_max: number;
  services: number;
  nuyen: number;
  bound?: boolean;
  hits?: number | null;
  opposed_hits?: number | null;
  test?: MagicTestInfo;
  attributes?: Record<string, number>;
  powers?: CritterPower[];
  optionalpowers?: CritterPower[];
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
  notes?: Notice[];
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
  /** `<addware>`: the quality that came with this implant (Busted Cyberware). */
  granted_by?: string;
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
  /** `<selectcyberware>`: this implant is keyed to another one, named in `extra`. */
  select_ware?: boolean;
  select_ware_category?: string;
  extra?: string;
  avail?: string;
  device_rating?: number;
  source?: string;
}

/** The engine's output — what `compute()` publishes back beside the state.
 *
 * The Python side types the top-level key set as
 * `app.engine.compute.derived_types.DerivedDict`; the row lists there are
 * `list[dict[str, Any]]`, so this half stays hand-written and
 * `tests/test_derived_contract.py` keeps the two key sets honest.
 */
export interface Derived {
  errors: Notice[];
  warnings?: Notice[];
  build_method?: string;
  career?: boolean;
  karma_earned?: number;
  nuyen_earned?: number;
  karma_adjust?: number;
  nuyen_adjust?: number;
  nuyen_pool?: number;
  career_advancement_karma?: number;
  career_advancement_lines?: { kind?: string; notice: Notice; amount: number }[];
  karma_spend_breakdown?: { kind?: string; notice: Notice; amount: number }[];
  nuyen_spend_breakdown?: { kind?: string; notice: Notice; amount: number }[];
  reward_log?: { id: string; label: string; karma: number; nuyen: number }[];
  expense_log?: { id: string; label: string; karma: number; nuyen: number }[];
  street_cred?: number;
  /** the part of `street_cred` earned from karma (SR5 p.372) */
  street_cred_earned?: number;
  /** karma per point of it: 10, raised by Consummate Professional */
  street_cred_divisor?: number;
  street_cred_burnt?: number;
  notoriety_quality?: number;
  notoriety_bonus?: number;
  nuyen_amt?: number;
  nuyen_karma_max?: number;
  trustfund?: number;
  trustfund_label?: Notice | null;
  ambidextrous?: boolean;
  erased?: boolean;
  excon?: boolean;
  overclocker?: boolean;
  special_modification_limit?: { used: number; max: number };
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
  knowledge_rating_max?: number;
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
  condition_monitor: {
    physical: number;
    stun: number;
    /** Boxes per −1 wound modifier (3 by default, SR5 p.169). */
    threshold?: number;
    /** Boxes ignored before the first −1 (High Pain Tolerance, a drug). */
    threshold_offset?: number;
  };
  initiative: { value: number; dice: number };
  /** INT×2 + the settings' astral dice (3 in Standard); absent without Magic. */
  astral_initiative?: { value: number; dice: number } | null;
  /** Ground walk / run in metres, sprint in metres per hit (Chummer's
   *  `CalculatedMovement("Ground")`). */
  movement: { walk: string; run: string; sprint: string; sprint_bonus: number };
  essence: number;
  armor: number;
  special_armor?: SpecialArmor;
  worn_armor?: string;
  armor_items?: InstalledArmor[];
  armor_mods?: InstalledArmorMod[];
  weapons?: InstalledWeapon[];
  weapon_accessories?: InstalledWeaponAccessory[];
  recoil?: { str: number; str_rc: number; free: number };
  active_drugs?: ActiveDrug[];
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
  custom_drugs?: CustomDrug[];
  lifestyles?: InstalledLifestyle[];
  commlink?: InstalledCommlink | null;
  cyberdeck?: InstalledMatrixDevice | null;
  rcc?: InstalledMatrixDevice | null;
  /** VR initiative for the persona worth running: Data Processing + INT,
   *  three dice cold sim / four hot (SR5 p.229). AR keeps meat initiative. */
  matrix_initiative?: {
    device: string;
    dataprocessing: number;
    value: number;
    cold_dice: number;
    hot_dice: number;
  } | null;
  lifestyle?: InstalledLifestyle | null;
  nuyen: number;
  nuyen_spent?: number;
  ware_attr_bonus?: Record<string, number>;
  karma: {
    pool: number;
    spent: number;
    remaining: number;
    negative?: { used: number; max: number | null };
  };
  points: {
    attributes: { used: number; max: number };
    special: { used: number; max: number };
    skills: { used: number; max: number };
    skill_groups: { used: number; max: number };
    knowledge: { used: number; max: number };
    contacts: { used: number; max: number };
  };
  /** Levels bought with karma, the rating each sits above, and their karma. */
  attribute_karma?: {
    levels: Record<string, number>;
    floors: Record<string, number>;
    karma: number;
  };
  /** Skill levels bought with karma (active / knowledge) and their karma. */
  skill_karma?: {
    levels: Record<string, number>;
    knowledge_levels: Record<string, number>;
    karma: number;
    knowledge_karma: number;
  };
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
  contact_points?: {
    used: number;
    free: number;
    paid: number;
    karma?: number;
    karma_per_point?: number;
    /** Free points per unaugmented CHA — 3, or what the settings file says. */
    free_mult?: number;
  };
  martial_arts?: InstalledMartialArt[];
  martial_art_points?: {
    styles: number;
    style_max: number;
    techniques: number;
    technique_max: number;
    karma: number;
  };
  skill_spec_options?: Record<string, string[]>;
  unarmed_reach?: number;
  unarmed_ap?: number;
  unarmed_physical?: boolean;
  reach?: number;
  throw_str?: number;
  throw_range_str?: number;
  lifestyle_cost_mod?: number;
  notoriety?: number;
  fame?: number;
  public_awareness?: number;
  fatigue_resist?: number;
  spell_resistance?: number;
  spell_defense?: {
    general: number;
    direct_mana: number;
    detection: number;
    mental_manipulation: number;
    mana_illusion: number;
    physical_illusion: number;
    decrease: Record<string, number>;
  };
  spell_dice_pool?: { name: string; id?: string; bonus: number; source?: string }[];
  action_dice_pools?: {
    category?: string;
    name: string;
    bonus: number;
    source?: string;
    /** a Matrix action still to be chosen; gone once it is */
    needs_action?: boolean;
  }[];
  test_mods?: {
    memory?: number;
    composure?: number;
    judge_intentions?: number;
    judge_intentions_defense?: number;
    judge_intentions_offense?: number;
    dodge?: number;
    surprise?: number;
    addiction_physiological_first?: number;
    addiction_physiological_addicted?: number;
    addiction_psychological_first?: number;
    addiction_psychological_addicted?: number;
  };
  cm_recovery?: { physical: number; stun: number };
  essence_penalty?: number;
  attribute_max_bonus?: Record<string, number>;
  disabled_skills?: string[];
  disabled_skill_groups?: string[];
  blocked_default_categories?: string[];
  disabled_cyberware_grades?: string[];
  adapsin?: boolean;
  disabled_bioware_grades?: string[];
  limit_spell_categories?: string[];
  limit_spirit_categories?: string[];
  allow_spell_categories?: string[];
  allow_spell_ranges?: string[];
  spell_range_gated?: boolean;
  block_spell_descriptors?: string[];
  extra_spirits?: string[];
  add_spirit_picks?: {
    quality_id: string;
    quality_name?: string;
    index: number;
    key: string;
    value?: string;
    options?: string[];
    skill?: string;
  }[];
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
      group?: boolean;
      ordeal?: boolean;
      schooling?: boolean;
      source?: string;
      page?: string;
      /** `<metamagiclimit>`: the only metamagics this grade may take (empty = free choice). */
      allowed_metamagics?: string[];
    }[];
    metamagics: {
      id: string;
      metamagic_id: string;
      name: string;
      grade: number;
      free?: boolean;
      source_quality?: string;
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
    /** `<quickeningmetamagic>`: sustained spells can be quickened with karma. */
    quickening?: boolean;
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
      group?: boolean;
      ordeal?: boolean;
      schooling?: boolean;
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
  skill_expertises?: {
    skill: string;
    spec: string;
    bonus: number;
    free?: boolean;
    source?: string;
  }[];
  exotic_skills?: InstalledExoticSkill[];
  skillsoft?: Record<string, number>;
  skillwires?: number;
  skilljack?: number;
  skill_bonus?: Record<string, number>;
  skill_group_bonus?: Record<string, number>;
  skill_category_bonus?: Record<string, number>;
  skill_bonus_notes?: Record<string, string[]>;
  /** `<swapskillattribute>`: the skill rolls off `attribute` instead of its
   *  printed one — with a `spec`, only for tests using that specialization. */
  skill_attribute_swaps?: { skill: string; attribute: string; spec: string; source: string }[];
  skill_max_bonus?: Record<string, number>;
  skill_pick_slots?: SkillPickSlot[];
  /** Skills that default without the −1 (Reflex Recorder Optimization). */
  no_default_penalty_skills?: string[];
  power_points?: { used: number; max: number };
  metagenic?: {
    limit: number;
    positive: number;
    negative: number;
    balanced: boolean;
    count: number;
  } | null;
  adept_powers?: InstalledAdeptPower[];
  mystic_pp?: number;
  way_discount?: { used: number; max: number };
  mentor?: MentorInfo | null;
  needs_mentor?: boolean;
  needs_paragon?: boolean;
  qi_foci?: InstalledQiFocus[];
  foci?: InstalledFocus[];
  focus_limits?: { count: number; count_max: number; force: number; force_max: number };
  spirits?: InstalledSpirit[];
  complex_forms?: InstalledComplexForm[];
  complex_form_points?: { used: number; free: number; paid: number };
  sprites?: InstalledSprite[];
  stream?: {
    id: string;
    name: string;
    drain: string;
    drain_attrs: string[];
    sprites?: string[];
    source?: string;
    page?: string;
  } | null;
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
  spell_points?: {
    used: number;
    free: number;
    paid: number;
    karma?: number;
    spell_karma?: number;
  };
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
    spirit_extra?: string;
    extra_kind?: string | null;
    select_options?: string[];
    spirit_options?: string[];
    expertise_skill?: string;
    add_spirit_count?: number;
    selectside?: boolean;
    side?: string | null;
    free?: boolean;
    /** the table karma, when a `<costdiscount>` condition changed it */
    karma_base?: number | null;
    /** the ware that switches this quality off (`<disablequality>`, RF p.148) */
    disabled_by?: string;
    /** taken after chargen: what it cost (SR5 p.107: positive ×2, negative 0) */
    career_cost?: number;
    /** the Infected's powers (RF p.126), the optional one included once picked */
    critter_powers?: CritterPower[];
    /** the list the one optional power comes from, and the pick */
    optional_powers?: string[];
    optional_power?: string;
  }[];
  /** held at chargen, gone in career: the buy-off cost (0 for a positive one) */
  qualities_removed?: { id: string; name: string; category: string; karma: number }[];
  /** career with a recorded chargen quality list, so the career prices apply */
  quality_career_pricing?: boolean;
  cyberware: InstalledWare[];
  bioware?: InstalledWare[];
  essence_lost?: number;
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
    /** the base metatype, for a metavariant */
    parent: string | null;
    source: string | null;
    attributes: Record<string, { min: number; max: number; aug: number }>;
    /** `<replaceattributes>`: the qualities these ranges come from instead of
     *  the metatype (the Infected qualities, Quadriplegic). */
    attributes_replaced_by?: string[];
  };
  talent?: {
    name: string;
    label?: string;
    value?: number;
    magic?: number;
    resonance?: number;
    spells?: number;
    cfp?: number;
  };
  translations?: Record<string, string>;
}
