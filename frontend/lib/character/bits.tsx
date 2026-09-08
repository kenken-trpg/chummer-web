import type { UiFn } from "@/lib/i18n";

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
      {ui("skills.specBit", { bonus })}
    </span>
  );
}
