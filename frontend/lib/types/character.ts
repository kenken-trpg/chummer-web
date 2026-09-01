import type {
  AdeptPowerInstall,
  ArmorInstall,
  ArmorModInstall,
  CommlinkInstall,
  ComplexFormInstall,
  ContactInstall,
  ExoticSkillInstall,
  FocusInstall,
  GearInstall,
  InitiationChoice,
  LifestyleInstall,
  MartialArtInstall,
  PriorityCategory,
  PriorityLetter,
  QiFocusInstall,
  SkillPickSlot,
  SpellInstall,
  SpiritInstall,
  SpriteInstall,
  SubmersionChoice,
  VehicleModInstall,
  WareInstall,
  WeaponAccessoryInstall,
  WeaponInstall,
  WeaponMountInstall,
} from "./installs";
import type {
  ActiveDrug,
  EnhancementInfo,
  InstalledAdeptPower,
  InstalledArmor,
  InstalledArmorMod,
  InstalledCommlink,
  InstalledComplexForm,
  InstalledContact,
  InstalledDrone,
  InstalledExoticSkill,
  InstalledFocus,
  InstalledGear,
  InstalledLifestyle,
  InstalledMartialArt,
  InstalledMatrixDevice,
  InstalledOptics,
  InstalledProgram,
  InstalledQiFocus,
  InstalledSpell,
  InstalledSpirit,
  InstalledSprite,
  InstalledVehicleMod,
  InstalledWare,
  InstalledWeapon,
  InstalledWeaponAccessory,
  InstalledWeaponMount,
  LimitModifier,
  MentorInfo,
  SpecialArmor,
  TraditionInfo,
} from "./derived";

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
  notes?: string;
  age?: string;
  sex?: string;
  height?: string;
  weight?: string;
  eyes?: string;
  hair?: string;
  skin?: string;
  appearance?: string;
  background?: string;
  concept?: string;
  portrait?: string;
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
    lifestyles?: InstalledLifestyle[];
    commlink?: InstalledCommlink | null;
    cyberdeck?: InstalledMatrixDevice | null;
    rcc?: InstalledMatrixDevice | null;
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
    contact_points?: {
      used: number;
      free: number;
      paid: number;
      karma?: number;
      karma_per_point?: number;
    };
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
    unarmed_ap?: number;
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
    skill_max_bonus?: Record<string, number>;
    skill_pick_slots?: SkillPickSlot[];
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
    }[];
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
