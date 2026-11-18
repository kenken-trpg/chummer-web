import type { UiFn } from "@/lib/i18n";
import type { SkillDefault } from "@/lib/character/skill-default";

/** The "· softR3" tail on a skill whose rating comes from a skillsoft. */
export function skillsoftBit(rating: number | undefined, ui: UiFn) {
  if (!rating) return null;
  return <span className="muted"> {ui("skills.softBit", { rating })}</span>;
}

/** The "· spec+2" tail on a specialized skill. `label` is the translated
 *  specialization name, shown on hover. */
export function specBit(
  spec: string | null | undefined,
  label: string | undefined,
  ui: UiFn,
  bonus: number = 2,
) {
  if (!spec) return null;
  return (
    <span className="muted" title={label || spec}>
      {" "}
      {bonus === 0 ? ui("skills.specDisabled") : ui("skills.specBit", { bonus })}
    </span>
  );
}

/** What an unlearned skill rolls at: the defaulting pool, or that it cannot be
 *  defaulted at all (SR5 p.130). `free` marks a pool that keeps its whole
 *  attribute — Reflex Recorder Optimization, CF p.165. */
export function defaultBit(info: SkillDefault, ui: UiFn) {
  if (info.blocked) return <span className="muted">{ui("skills.defaultBlocked")}</span>;
  const key = info.free ? "skills.defaultFree" : "skills.default";
  return (
    // the rule behind the pool is in the skill name's "?", which a keyboard
    // and a finger can open; a `title=` here only reached a mouse
    <span className="muted">{ui(key, { pool: info.pool })}</span>
  );
}
