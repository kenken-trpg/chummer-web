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
  group?: boolean;
  ordeal?: boolean;
  schooling?: boolean;
}

export interface SubmersionChoice {
  id?: string;
  grade: number;
  echo_id: string;
  extra?: string | null;
  group?: boolean;
  ordeal?: boolean;
  schooling?: boolean;
}

export interface ExoticSkillInstall {
  id?: string;
  skill_name: string;
  extra?: string;
  rating?: number;
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
  wireless?: boolean;
}

export interface ArmorModInstall {
  id?: string;
  mod_id: string;
  parent_id?: string | null;
  included?: boolean;
  rating?: number;
  wireless?: boolean;
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
  active?: boolean;
}

export interface LifestyleInstall {
  id?: string;
  lifestyle_id: string;
  months?: number;
  quality_ids?: string[];
  quality_extras?: Record<string, string>;
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

export interface QiFocusInstall {
  id?: string;
  rating: number;
  power_id: string;
  extra?: string | null;
  power_rating?: number;
}

export interface MentorChoice {
  name: string;
  set: string;
  audience: string;
  selected: boolean;
  extra: string;
  extra_options: string[];
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

export type PriorityCategory = "Heritage" | "Attributes" | "Talent" | "Skills" | "Resources";
