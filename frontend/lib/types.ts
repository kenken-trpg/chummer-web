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
  priorities: Record<PriorityCategory, PriorityLetter>;
  metatype: string;
  metavariant: string | null;
  talent: string;
  attributes: Record<string, number>;
  skills: Record<string, number>;
  skill_groups: Record<string, number>;
  knowledge_skills: Record<string, number>;
  quality_ids: string[];
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
  options?: {
    redliner_torso: boolean;
    redliner_skull: boolean;
  };
  derived: {
    errors: string[];
    warnings?: string[];
    totals: Record<string, number>;
    limits: { physical: number; mental: number; social: number };
    condition_monitor: { physical: number; stun: number };
    initiative: { value: number; dice: number };
    movement: { walk: string; run: string; sprint: string };
    essence: number;
    armor: number;
    nuyen: number;
    karma: { pool: number; spent: number; remaining: number };
    points: Record<string, { used: number; max: number }>;
    skill_totals: Record<string, number>;
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
    enhancements?: EnhancementInfo[];
    damage_resistance?: number;
    unarmed_dv?: number;
    unlock_skills?: string[];
    enabled_tabs: string[];
    unimplemented_bonuses: { source: string; tag: string }[];
    qualities: { id: string; name: string; karma: number; category: string; source: string }[];
    cyberware: InstalledWare[];
    bioware?: InstalledWare[];
    nuyen_spent?: number;
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
    attributes: Record<string, { min: number; max: number; aug: number }>;
    metavariants: { name: string; attributes: Record<string, { min: number; max: number; aug: number }> }[];
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
    }[];
    knowledge: { name: string; category: string; attribute: string }[];
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
        talents: { name: string; label?: string; value: number }[];
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
  spells?: { id: string; name: string; category: string; dv: string; source: string; page: string }[];
  qi_focus?: { id: string; name: string; maxrating: number; cost: string; source: string; page: string } | null;
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
  limbslot?: string | null;
  selectside?: boolean;
  source: string;
  page: string;
}

export interface WareCatalog {
  grades: { name: string; ess: number; cost: number }[];
  items: WareCatalogItem[];
}
