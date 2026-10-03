import type { MsgKey } from "@/lib/i18n";

/**
 * What a free-text quality pick is asking for.
 *
 * 107 qualities in `qualities.xml` carry a bare `<selecttext>` — Chummer opens
 * a blank box and the player types what the quality is about. The box had one
 * placeholder for all of them, and it named Allergy's examples ("花粉、日光")
 * — so 依存症 (軽度) asked for a pollen and 行動規範 did too.
 *
 * Chummer has nothing to read here: `<selecttext>` carries no prompt, and the
 * book's wording lives in the rules text, not the data. So the families whose
 * subject is unambiguous from the quality's own name are listed, and anything
 * else gets a prompt that asks for the content without inventing an example.
 * A family is listed only where the answer is not in doubt; guessing a wrong
 * example would put this back where it started.
 */
const FAMILIES: [RegExp, MsgKey][] = [
  // the drug or the habit, e.g. ノヴァコーク / BTL
  [/^(Addiction|Dry Addict)\b/, "quality.ph.addiction"],
  [/^Allergy\b/, "quality.ph.allergy"],
  [/^Phobia\b/, "quality.ph.phobia"],
  // who the character is for or against — a metatype, a corp, the Awakened
  [/^(Prejudiced|Favored)\b/, "quality.ph.group"],
  [/^Code of Honor\b/, "quality.ph.code"],
  [/^Day Job\b/, "quality.ph.dayJob"],
  // which authority issued the SIN
  [/^SINner\b/, "quality.ph.sinIssuer"],
  [/^Rank\b/, "quality.ph.rank"],
  [/^(Home Ground|Location Attunement)\b/, "quality.ph.place"],
  [/^Poor Self Control\b/, "quality.ph.compulsion"],
  [/^Brand Loyalty\b/, "quality.ph.brand"],
  // who is after the character
  [/^(Vendetta|Wanted)\b/, "quality.ph.pursuer"],
];

/** The placeholder for `name`'s free-text box. Falls back to a prompt that
 *  asks for the content and leaves the examples to the quality's rules text. */
export function qualityPlaceholder(name: string): MsgKey {
  for (const [pattern, key] of FAMILIES) if (pattern.test(name)) return key;
  return "quality.targetPlaceholder";
}
