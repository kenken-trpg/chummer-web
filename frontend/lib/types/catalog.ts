import type { Notice } from "@/lib/engine-notices";
import type { PriorityCategory, PriorityLetter, QualityReqNode } from "./installs";
import type { TraditionInfo } from "./derived";

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
  has_wireless?: boolean;
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
  has_wireless?: boolean;
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
  range?: string;
  alt_range?: string;
  mounts?: string[];
  avail: string;
  cost: string;
  source: string;
  page: string;
  from_gear?: boolean;
  add_gear_id?: string;
}

/** ranges.xml band formulas — literal integers or `{STR}`-scaled strings. */
export interface WeaponRangeBands {
  min: string;
  short: string;
  medium: string;
  long: string;
  extreme: string;
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
  specialmodification?: boolean;
  special_modification_cost?: number;
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
  speed?: string;
  vectors?: string[];
  duration?: string;
  effect?: Notice[];
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

/** One rulebook: the `<source>` code items carry, and its English title.
 *  `tr(name)` renders it — book names live in the normal translation map. */
export interface BookInfo {
  code: string;
  name: string;
}

/** A ruleset the user can pick from the settings pulldown. */
export interface SettingsPreset {
  id: string;
  name: string;
  build_method: string;
  /** Enabled `<source>` codes. Empty means the preset restricts nothing. */
  books: string[];
  sum_to_ten: number;
}

export type PriorityCell = {
  name: string;
  attribute_points?: number;
  skill_points?: number;
  skill_group_points?: number;
  nuyen?: number;
  metatypes: { name: string; special: number; variants: { name: string }[] }[];
  talents: { name: string; label?: string; value: number; spells?: number }[];
};

export type PriorityTable = Record<PriorityCategory, Record<PriorityLetter, PriorityCell>>;

export interface Catalog {
  metatypes: {
    name: string;
    id: string;
    category: string;
    karma?: number;
    attributes: Record<string, { min: number; max: number; aug: number }>;
    metavariants: {
      name: string;
      karma?: number;
      attributes: Record<string, { min: number; max: number; aug: number }>;
    }[];
    source: string;
  }[];
  skills: {
    groups: string[];
    /** English group name -> Japanese. Separate from `translations`
     *  because the group names collide with spells and knowledge
     *  skills there; see loaders/translations.py. */
    group_names?: Record<string, string>;
    /** Active-skill categories in the rulebook's chapter order (Combat,
     *  Physical, Social, Magical, Resonance, Technical, Vehicle). The skill
     *  list itself comes out of the vendored file in a different order, so the
     *  Skills tab sorts by this. */
    active_categories?: string[];
    skills: {
      id: string;
      name: string;
      attribute: string;
      category: string;
      skillgroup: string | null;
      source: string;
      exotic?: boolean;
      /** False for the skills SR5 p.130 says cannot be defaulted at all. */
      default?: boolean;
      specs?: string[];
    }[];
    knowledge: {
      name: string;
      category: string;
      attribute: string;
      source?: string;
      specs?: string[];
    }[];
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
    metagenic?: boolean;
    needs_extra?: boolean;
    extra_kind?: string | null;
    select_options?: string[];
    spirit_options?: string[];
    expertise_skill?: string;
    add_spirit_count?: number;
    max_takes?: number | null;
    /** siblings counted toward the same limit (Indomitable) */
    include_in_limit?: string[];
    /** that shared cap when it differs from max_takes (Tough as Nails: 4); 0 = max_takes */
    limit_with_inclusions?: number;
    chargenonly?: boolean;
    required_tree?: QualityReqNode[];
    forbidden_tree?: QualityReqNode[];
  }[];
  priority_table: PriorityTable;
  /** Per non-default `<prioritytable>`, only the cells that table replaces.
   *  The catalog is shared by every character, so it carries the Standard
   *  table and the differences; `priorityTableFor` puts them together. */
  priority_table_overrides?: Record<
    string,
    Partial<Record<PriorityCategory, Partial<PriorityTable[PriorityCategory]>>>
  >;
  /** Every rulebook `source` can name, in `books.xml` order. The settings
   *  pulldown lists these; nothing here is filtered by them — the client
   *  narrows its own pick lists (see `lib/character/books.ts`). */
  books: BookInfo[];
  /** Chummer's shipped settings files, projected to the parts this app can
   *  apply. Presets whose build method the engine has no support for are
   *  dropped by the loader, so every entry here is selectable. */
  settings_presets: SettingsPreset[];
  translations: Record<string, string>;
  /** `{locale: {key: text}}` — narrowed by the backend to what the app reads. */
  ui_strings: Record<string, Record<string, string>>;
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
  /** Paragons (KC p.103) — the technomancer's mentor spirits, same shape. */
  paragons?: { id: string; name: string; source: string; page: string; advantage: string }[];
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
  qi_focus?: {
    id: string;
    name: string;
    maxrating: number;
    cost: string;
    source: string;
    page: string;
  } | null;
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
  weapon_ranges?: Record<string, WeaponRangeBands>;
  lifestyles?: LifestyleCatalogItem[];
  lifestyle_qualities?: LifestyleQualityCatalogItem[];
  drugs?: GearCatalogItem[];
  drug_grades?: GearCatalogItem[];
  drug_components?: DrugComponentCatalogItem[];
  drug_component_grades?: DrugComponentGradeCatalogItem[];
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
  grades: { name: string; ess: number; ess_adapsin: number; cost: number }[];
  items: WareCatalogItem[];
}

/** One level of a drug component: what it does, and what it costs you when the
 *  drug wears off. A component with a single level only has level 0. */
export interface DrugComponentLevel {
  level: number;
  effect?: Notice[];
  crash_damage: number;
  speed: number;
  duration: number;
  info: string;
}

/** A part a custom drug is mixed from (CF p.190): Foundation, Block or
 *  Enhancer. `limit` is how many one drug may hold, 0 meaning unlimited. */
export interface DrugComponentCatalogItem {
  id: string;
  name: string;
  category: string;
  cost: string;
  avail: string;
  addiction_rating: number;
  addiction_threshold: number;
  limit: number;
  levels: DrugComponentLevel[];
  source?: string;
  page?: string;
}

/** The quality a custom drug is cooked to. */
export interface DrugComponentGradeCatalogItem {
  id: string;
  name: string;
  cost_multiplier: number;
  addiction_threshold: number;
  source?: string;
}
