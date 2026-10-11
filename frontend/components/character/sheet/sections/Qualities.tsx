import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { useUiText } from "@/lib/i18n";
import { critterPowerRow } from "@/lib/spell-terms";

export function QualitiesSection(s: SheetData) {
  const { tr, d, qualities } = s;
  const { ui } = useUiText();
  return (
    <Section title="sheet.qualities" empty={!qualities.length && !d.metatype_info.powers?.length}>
      <ul className="sheet-list">
        {qualities.map((q, idx) => (
          <li key={`${q.id}-${idx}`}>
            <b>
              {tr(q.name)}
              {q.level != null ? ` Lv${q.level}` : ""}
            </b>
            {q.extra ? `（${tr(q.extra)}）` : ""}
            {q.side
              ? `（${
                  q.side === "Left"
                    ? ui("common.left")
                    : q.side === "Right"
                      ? ui("common.right")
                      : q.side
                }）`
              : ""}
            <span className="sheet-dim">
              {" "}
              {q.category === "Negative"
                ? ui("sheet.qualityNegative")
                : ui("sheet.qualityPositive")}{" "}
              {q.karma > 0 ? `+${q.karma}` : q.karma}K
              {q.origin === "Metatype"
                ? ` / ${ui("meta.innate", { name: tr(q.origin_name || s.character.metatype) })}`
                : ""}
            </span>
          </li>
        ))}
      </ul>
      {d.metatype_info.powers?.length ? (
        <>
          <h4>{ui("meta.innatePowers")}</h4>
          <ul className="sheet-list">
            {d.metatype_info.powers.map((power, index) => (
              <li key={`${power.id}-${index}`}>
                {critterPowerRow(power, tr, ui)}
                {power.select ? ` / ${power.select}` : ""}
                {power.rating ? ` / ${power.rating}` : ""}
                <span className="sheet-dim">
                  {" "}
                  / {power.source} p.{power.page}
                </span>
              </li>
            ))}
          </ul>
        </>
      ) : null}
      {d.metagenic &&
      (d.metagenic.limit > 0 || d.metagenic.positive > 0 || d.metagenic.negative > 0) ? (
        <p className="sheet-dim">
          {ui("sheet.metagenic", {
            positive: d.metagenic.positive,
            negative: d.metagenic.negative,
          })}
          {d.metagenic.limit > 0 ? ui("sheet.metagenicLimit", { limit: d.metagenic.limit }) : ""}
        </p>
      ) : null}
    </Section>
  );
}
