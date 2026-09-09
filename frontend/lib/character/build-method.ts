import type { Character } from "@/lib/types";
import { CATS, DEFAULT_PRIORITIES } from "@/lib/character/constants";

/**
 * The patch that switches a character to `method`.
 *
 * Only Priority carries a condition: it needs the five categories to hold A-E
 * exactly once, and Sum-to-Ten / Karma leave letters behind that do not. So
 * switching *to* Priority from a spread that is not a permutation resets the
 * table rather than landing the character on an invalid one; a spread that
 * already is a permutation is kept, since the user chose it.
 *
 * Shared by the Priority tab's three buttons and the settings pulldown, which
 * changes the method as a side effect of picking a preset.
 */
export function buildMethodPatch(method: string, ch: Character): Record<string, unknown> {
  if (method === "Karma") return { build_method: "Karma", talent: ch.talent || "Mundane" };
  if (method !== "Priority") return { build_method: method };
  const letters = CATS.map((c) => ch.priorities[c.key]);
  const unique = [...letters].sort().join("") === "ABCDE";
  return unique
    ? { build_method: "Priority" }
    : { build_method: "Priority", priorities: { ...DEFAULT_PRIORITIES }, talent: "Mundane" };
}
