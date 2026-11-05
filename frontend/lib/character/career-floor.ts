import type { Character } from "@/lib/types";

type RatedField = "attributes" | "skills" | "skill_groups" | "knowledge_skills" | "exotic_skills";

/**
 * The lowest a rating may go in career: the one it had on entering career.
 *
 * Chummer has no way to lower an attribute or skill after creation, nor to
 * delete one bought then, so the karma chargen paid for it can never come
 * back. This app works karma out again from the ratings held, so a rating
 * lowered under its chargen value gave that karma back; the editors stop at
 * it instead. 0 outside career, and for anything the baseline does not hold
 * (a skill first learned in career, an older save without a baseline).
 * Exotic skills are keyed by row id, as the baseline records them.
 */
export function careerFloor(ch: Character, field: RatedField, key: string): number {
  if (!ch.career) return 0;
  return Math.max(0, ch.career_baseline?.[field]?.[key] ?? 0);
}
