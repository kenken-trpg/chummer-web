import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";

export function QualitiesSection(s: SheetData) {
  const { tr, d, qualities } = s;
  return (
    <Section title="資質" empty={!qualities.length}>
      <ul className="sheet-list">
        {qualities.map((q) => (
          <li key={q.id}>
            <b>{tr(q.name)}</b>
            {q.extra ? `（${tr(q.extra)}）` : ""}
            {q.side ? `（${q.side === "Left" ? "左" : q.side === "Right" ? "右" : q.side}）` : ""}
            <span className="sheet-dim">
              {" "}
              {q.category === "Negative" ? "不利な資質" : "有利な資質"}{" "}
              {q.karma > 0 ? `+${q.karma}` : q.karma}K
            </span>
          </li>
        ))}
      </ul>
      {d.metagenic &&
      (d.metagenic.limit > 0 || d.metagenic.positive > 0 || d.metagenic.negative > 0) ? (
        <p className="sheet-dim">
          メタジェネティック: 有利 {d.metagenic.positive} ／ 不利 {d.metagenic.negative}
          {d.metagenic.limit > 0 ? ` ／ 上限 ${d.metagenic.limit}` : ""}
        </p>
      ) : null}
    </Section>
  );
}
