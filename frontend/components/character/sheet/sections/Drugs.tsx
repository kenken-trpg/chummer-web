import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { useUiText } from "@/lib/i18n";

export function DrugsSection(s: SheetData) {
  const { tr, d, drugs, drugChildren } = s;
  const { ui } = useUiText();
  return (
    <Section title="sheet.drugs" empty={!drugs.length && !(d.active_drugs || []).length}>
      {(d.active_drugs || []).length ? (
        <div className="sheet-block">
          <h4>{ui("sheet.drugsActive")}</h4>
          <ul className="sheet-list sheet-list-compact">
            {(d.active_drugs || []).map((drug, i) => (
              <li key={`${drug.name}-${i}`}>
                <b>{tr(drug.name)}</b>
                {drug.effect ? ` ・ ${drug.effect}` : ""}
                {drug.duration ? ui("sheet.drugDuration", { duration: drug.duration }) : ""}
                {drug.vectors?.length
                  ? ui("sheet.drugVector", {
                      list: drug.vectors.join(ui("common.termSep")),
                    })
                  : ""}
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
              {grades.length
                ? `（${grades.map((g) => tr(g.name)).join(ui("common.listSep"))}）`
                : ""}
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
