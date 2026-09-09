import type { Character } from "@/lib/types";

/** What an unlearned skill can still be rolled at, if anything.
 *
 *  SR5 p.130: a skill you have no rating in rolls its linked attribute − 1,
 *  unless the skill is one that cannot be defaulted at all. `free` is the
 *  Reflex Recorder Optimization case (CF p.165): the recorder's skill and its
 *  whole group default without the −1.
 */
export type SkillDefault =
  { blocked: true } | { blocked: false; pool: number; free: boolean; attribute: string };

/** The defaulting penalty every unlearned skill pays (SR5 p.130). */
export const DEFAULT_PENALTY = 1;

export function skillDefault(
  skill: { name: string; attribute: string; category: string; default?: boolean },
  d: Character["derived"],
): SkillDefault {
  const blockedCategories = d.blocked_default_categories || [];
  if (skill.default === false || blockedCategories.includes(skill.category)) {
    return { blocked: true };
  }
  const free = (d.no_default_penalty_skills || []).includes(skill.name);
  const attr = d.totals?.[skill.attribute] || 0;
  const bonus = d.skill_bonus?.[skill.name] || 0;
  // A pool cannot go below zero: at that point there are no dice to roll.
  const pool = Math.max(0, attr + bonus - (free ? 0 : DEFAULT_PENALTY));
  return { blocked: false, pool, free, attribute: skill.attribute };
}
