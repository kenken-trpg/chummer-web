// Magic and resonance: row shapes listed in `Derived` (../derived.ts).

import type { MentorChoice } from "../installs";
import type { Notice } from "@/lib/engine-notices";

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
