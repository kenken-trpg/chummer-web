import type { SkillPickSlot } from "./installs";
import type { Notice } from "@/lib/engine-notices";
import type { InstalledContact, InstalledExoticSkill, InstalledMartialArt } from "./rows/character";
import type {
  ActiveDrug,
  CustomDrug,
  InstalledArmor,
  InstalledArmorMod,
  InstalledCommlink,
  InstalledGear,
  InstalledMatrixDevice,
  InstalledOptics,
  InstalledProgram,
  InstalledWeapon,
  InstalledWeaponAccessory,
  LimitModifier,
  SpecialArmor,
} from "./rows/gear";
import type { InstalledLifestyle } from "./rows/lifestyle";
import type {
  CritterPower,
  EnhancementInfo,
  InstalledAdeptPower,
  InstalledComplexForm,
  InstalledFocus,
  InstalledQiFocus,
  InstalledSpell,
  InstalledSpirit,
  InstalledSprite,
  MentorInfo,
  TraditionInfo,
} from "./rows/magic";
import type { InstalledDrone, InstalledVehicleMod, InstalledWeaponMount } from "./rows/vehicles";
import type { InstalledWare } from "./rows/ware";

export type * from "./rows/character";
export type * from "./rows/magic";
export type * from "./rows/gear";
export type * from "./rows/lifestyle";
export type * from "./rows/vehicles";
export type * from "./rows/ware";

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
  /** Per sidebar value (`limit_physical`, `initiative`, …), what each named
   *  source added — before non-stacking bonuses are resolved. */
  stat_sources?: Record<string, { source: string; value: number }[]>;
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
    group_levels: Record<string, number>;
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
  /** The priority talent's free skills (a group, for an Aspected Magician). */
  talent_skills?: {
    qty: number;
    /** the free rating each pick gets */
    rating: number;
    /** an Aspected Magician's pick is a skill group */
    group: boolean;
    options: string[];
    picked: string[];
  } | null;
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
