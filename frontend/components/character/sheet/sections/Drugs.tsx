import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { useUiText } from "@/lib/i18n";
import { renderNotice, renderNotices } from "@/lib/engine-notices";

export function DrugsSection(s: SheetData) {
  const { tr, d, drugs, drugChildren } = s;
  const { ui } = useUiText();
  const mixed = d.custom_drugs || [];
  return (
    <Section
      title="sheet.drugs"
      empty={!drugs.length && !mixed.length && !(d.active_drugs || []).length}
    >
      {(d.active_drugs || []).length ? (
        <div className="sheet-block">
          <h4>{ui("sheet.drugsActive")}</h4>
          <ul className="sheet-list sheet-list-compact">
            {(d.active_drugs || []).map((drug, i) => (
              <li key={`${drug.name}-${i}`}>
                <b>{tr(drug.name)}</b>
                {drug.effect?.length ? ` ・ ${renderNotices(drug.effect, ui, tr)}` : ""}
                {drug.duration
                  ? ui("sheet.drugDuration", {
                      duration: renderNotice(drug.duration, ui, tr),
                    })
                  : ""}
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
      {mixed.length ? (
        <ul className="sheet-list sheet-list-compact">
          {mixed.map((drug) => (
            <li key={drug.id}>
              {drug.active ? "▶ " : ""}
              {drug.name || ui("customDrug.unnamed")}
              {drug.qty > 1 ? ` ×${drug.qty}` : ""}
              {`（${tr(drug.grade)}${ui("common.listSep")}${drug.components
                .map((part) => tr(part.name))
                .join(ui("common.listSep"))}）`}
              {drug.effect?.length ? (
                <span className="sheet-dim">{` ・ ${renderNotices(drug.effect, ui, tr)}`}</span>
              ) : (
                ""
              )}
            </li>
          ))}
        </ul>
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
              {item.drug_effect?.length ? (
                <span className="sheet-dim">{` ・ ${renderNotices(item.drug_effect, ui, tr)}`}</span>
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
