import type { MsgKey, UiFn } from "@/lib/i18n";

/**
 * The talent options, as Japanese.
 *
 * The catalog hands these over as one pre-formatted English string —
 * "Magician - 6 Magic/10 Spells" — so the name and the ratings have to be
 * split apart before either can be translated. The name is looked up; the
 * ratings tail is a pattern, so it is rewritten by shape.
 *
 * Only the core SR5 talents are named in Japanese. Apprentice, Aware,
 * Enchanter and Explorer are Run Faster's, and this project shows Run Faster
 * entries under their English names.
 */
const TALENT_KEYS: Record<string, MsgKey> = {
  Magician: "talent.magician",
  "Mystic Adept": "talent.mysticAdept",
  Adept: "talent.adept",
  "Aspected Magician": "talent.aspectedMagician",
  Technomancer: "talent.technomancer",
  Mundane: "talent.mundane",
};

/** "6 Magic/10 Spells", "4 Magic", "6 Resonance/7 Complex Forms". */
const MAGIC_SPELLS = /^(\d+) Magic\/(\d+) Spells$/;
const MAGIC = /^(\d+) Magic$/;
const RESONANCE = /^(\d+) Resonance\/(\d+) Complex Forms$/;

function ratingsLabel(tail: string, ui: UiFn): string {
  const ms = MAGIC_SPELLS.exec(tail);
  if (ms) return ui("talent.magicSpells", { magic: ms[1], spells: ms[2] });

  const m = MAGIC.exec(tail);
  if (m) return ui("talent.magic", { magic: m[1] });

  const r = RESONANCE.exec(tail);
  if (r) return ui("talent.resonanceForms", { resonance: r[1], forms: r[2] });

  return tail;
}

/**
 * One talent dropdown option, localised.
 *
 * `label` is what the catalog ships ("Adept - 6 Magic"); `name` is the bare
 * talent ("Adept"), which is what the option's value is keyed on. Anything
 * unrecognised falls through in English rather than vanishing — a house rule
 * or a supplement talent still reads.
 */
export function talentLabel(name: string, label: string | undefined, ui: UiFn): string {
  const shipped = label || name;
  if (!shipped.startsWith(name)) return shipped;

  const key = TALENT_KEYS[name];
  const head = key ? ui(key) : name;
  const tail = shipped.slice(name.length).replace(/^\s*-\s*/, "");
  return tail ? `${head} - ${ratingsLabel(tail, ui)}` : head;
}
