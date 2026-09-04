import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { useUiText } from "@/lib/i18n";

export function QualitiesSection(s: SheetData) {
  const { tr, d, qualities } = s;
  const { ui } = useUiText();
  return (
    <Section title="sheet.qualities" empty={!qualities.length}>
      <ul className="sheet-list">
        {qualities.map((q) => (
          <li key={q.id}>
            <b>{tr(q.name)}</b>
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
            </span>
          </li>
        ))}
      </ul>
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
