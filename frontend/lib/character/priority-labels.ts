import type { MsgKey, UiFn } from "@/lib/i18n";

/**
 * The priority table's cell names, as Japanese.
 *
 * They arrive from the vendored Chummer data as English sentences —
 * "Human or Elf", "24 (12) Attributes" — and the tab used to print them raw,
 * so the one table that decides the whole character was the only English thing
 * on the page.
 *
 * They are not entity names, so `tr` cannot reach them: "Magician or
 * Technomancer" is a phrase, and the Japanese for it deliberately spells out
 * what Priority A actually grants (Magician *or* Mystic Adept). The
 * number-bearing rows are patterns rather than fixed strings, so they are
 * rewritten by shape instead of looked up.
 */
const CELL_KEYS: Record<string, MsgKey> = {
  // Heritage
  "Any metatype": "prio.cell.anyMetatype",
  "Human, Dwarf, Elf, Ork, or A.I.": "prio.cell.humanDwarfElfOrkAi",
  "Human or Elf": "prio.cell.humanOrElf",
  Human: "prio.cell.human",
  // Talent
  "Magician or Technomancer": "prio.cell.magicianOrTechnomancer",
  "Adept, Magician, or Technomancer": "prio.cell.adeptMagicianTechnomancer",
  "Adept or Aspected Magician": "prio.cell.adeptOrAspectedMagician",
};

const ATTRIBUTES = /^(\d+) \((\d+)\) Attributes$/;
const SKILLS = /^(\d+) Skills\/(\d+) Skill Groups$/;

/**
 * One priority cell, localised. Anything unrecognised is returned as it came —
 * a house rule or a supplement row still renders, in English, rather than
 * vanishing.
 */
export function priorityCellLabel(name: string, ui: UiFn): string {
  const key = CELL_KEYS[name];
  if (key) return ui(key);

  const attrs = ATTRIBUTES.exec(name);
  if (attrs) return ui("prio.cell.attributes", { points: attrs[1], special: attrs[2] });

  const skills = SKILLS.exec(name);
  if (skills) return ui("prio.cell.skills", { skills: skills[1], groups: skills[2] });

  return name;
}

/** The three build methods, as the buttons and the sidebar name them. */
export function buildMethodLabel(method: string | undefined, ui: UiFn): string {
  if (method === "Karma") return ui("prio.method.karma");
  if (method === "SumToTen") return ui("prio.method.sumToTen");
  return ui("prio.method.priority");
}
