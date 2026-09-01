import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";

export function DrugsSection(s: SheetData) {
  const { tr, d, drugs, drugChildren } = s;
  return (
    <Section title="ドラッグ／毒物" empty={!drugs.length && !(d.active_drugs || []).length}>
      {(d.active_drugs || []).length ? (
        <div className="sheet-block">
          <h4>使用中（能力値・判定に反映済み）</h4>
          <ul className="sheet-list sheet-list-compact">
            {(d.active_drugs || []).map((drug, i) => (
              <li key={`${drug.name}-${i}`}>
                <b>{tr(drug.name)}</b>
                {drug.effect ? ` ・ ${drug.effect}` : ""}
                {drug.duration ? ` ・ 持続 ${drug.duration}` : ""}
                {drug.vectors?.length ? ` ・ 経路 ${drug.vectors.join("・")}` : ""}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      <ul className="sheet-list sheet-list-compact">
        {drugs.map((item) => {
          const grades = drugChildren(item.id);
          return (
            <li key={item.id}>
              {item.active ? "▶ " : ""}
              {tr(item.name)}
              {(item.qty || 1) > 1 ? ` ×${item.qty}` : ""}
              {grades.length ? `（${grades.map((g) => tr(g.name)).join("、")}）` : ""}
              {item.drug_effect ? (
                <span className="sheet-dim">{` ・ ${item.drug_effect}`}</span>
              ) : (
                ""
              )}
            </li>
          );
        })}
      </ul>
    </Section>
  );
}
