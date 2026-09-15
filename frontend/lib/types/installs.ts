/** The hand-written half of the state types.
 *
 * Everything that mirrors a Pydantic model lives in `generated.ts` and is
 * re-exported from here, so the browser keeps importing these names from one
 * place. What is left below has no Python counterpart: shapes the engine
 * publishes as plain dicts, and two unions the browser types more tightly
 * than `str`.
 */
export * from "./generated";

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
  /** `<hardwires>`: the rating the ware fixes the picked skill at (0 otherwise). */
  rating: number;
  options: string[];
  knowledgeskills: boolean;
  /** Reflex Recorder Optimization: this pick's skill group defaults with no −1. */
  default_free?: boolean;
  /** `<weaponskillaccuracy>` (Cyberlimb Optimization): Accuracy on the picked
   *  skill's weapons, not dice. */
  accuracy?: number;
}

/** A pick a power the choice grants asks for on its own, because the choice's
 *  own `extra` is already spent on *which* power it grants. */
export interface MentorPowerTarget {
  power: string;
  key: string;
  kind: string;
  extra: string;
  options: string[];
}

export interface MentorChoice {
  name: string;
  set: string;
  audience: string;
  selected: boolean;
  extra: string;
  extra_options: string[];
  power_targets?: MentorPowerTarget[];
}

export type PriorityLetter = "A" | "B" | "C" | "D" | "E";

export type PriorityCategory = "Heritage" | "Attributes" | "Talent" | "Skills" | "Resources";
