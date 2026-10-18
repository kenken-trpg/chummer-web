import type { UiFn } from "@/lib/i18n";
import { critterPowerParts } from "@/lib/spell-terms";

/** A spirit's or a critter's power on screen: the name, then the table's
 *  terms in brackets kept in one piece, so a narrow column wraps before the
 *  bracket rather than in the middle of a word. */
export function CritterPowerRow({
  power,
  tr,
  ui,
}: {
  power: Parameters<typeof critterPowerParts>[0];
  tr: (name: string) => string;
  ui: UiFn;
}) {
  const { name, detail } = critterPowerParts(power, tr, ui);
  if (!detail) return <>{name}</>;
  const gap = detail.match(/^\s*/)![0];
  return (
    <>
      {name}
      {gap}
      <span className="term-group">{detail.slice(gap.length)}</span>
    </>
  );
}
