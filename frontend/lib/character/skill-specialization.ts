import type { Character } from "@/lib/types";

/** Loss of Confidence suppresses the effect, including granted Expertise,
 *  without deleting a specialization or refunding its cost. */
export function specializationBonus(d: Character["derived"], skill: string): number {
  if (d.skill_specializations_disabled?.includes(skill)) return 0;
  return d.skill_expertises?.find((row) => row.skill === skill)?.bonus ?? 2;
}
