import type { SheetData } from "@/lib/character/sheet-data";
import { GradeList, Section } from "@/components/character/sheet/blocks";
import { cfDuration, cfTarget } from "@/lib/character/format";
import { useUiText } from "@/lib/i18n";

export function ResonanceSection(s: SheetData) {
  const { tr, d, enabled } = s;
  const { ui } = useUiText();
  return (
    <Section
      title="sheet.resonance"
      empty={!enabled.has("complexforms") && !enabled.has("sprites") && !enabled.has("submersion")}
    >
      {enabled.has("complexforms") && (d.complex_forms || []).length ? (
        <div className="sheet-block">
          <h4>
            {ui("sheet.complexForms")}
            {d.fade_resist
              ? ui("sheet.fadeResist", {
                  pool: d.fade_resist.pool,
                  attrs: d.fade_resist.attrs,
                })
              : ""}
          </h4>
          <ul className="sheet-list">
            {(d.complex_forms || []).map((item) => (
              <li key={item.id}>
                <b>{tr(item.label || item.name)}</b>
                {ui("sheet.cfLine", {
                  target: cfTarget(item.target, ui),
                  duration: cfDuration(item.duration, ui),
                  level: item.level,
                  fv: item.fv,
                })}
                {item.fade != null
                  ? ui("sheet.fade", { fade: `${item.fade}${item.fade_code || ""}` })
                  : ""}
                {item.physical ? ui("sheet.physical") : ""}
                {item.extra ? `（${tr(item.extra)}）` : ""}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {enabled.has("sprites") && (d.sprites || []).length ? (
        <div className="sheet-block">
          <h4>{ui("sheet.sprites")}</h4>
          <ul className="sheet-list">
            {(d.sprites || []).map((item) => (
              <li key={item.id}>
                <b>{tr(item.name)}</b>
                {" ・ "}L{item.level}
                {item.services != null ? ui("sheet.services", { services: item.services }) : ""}
                {item.registered ? ui("sheet.registered") : ui("sheet.compiled")}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {enabled.has("submersion") && (d.submersion?.grade || 0) > 0 ? (
        <div className="sheet-block">
          <h4>{ui("sheet.submersion", { grade: d.submersion?.grade ?? 0 })}</h4>
          {(d.submersion?.echoes || []).length ? (
            <GradeList items={d.submersion?.echoes || []} tr={tr} />
          ) : (
            <p className="sheet-note">{ui("sheet.noEcho")}</p>
          )}
        </div>
      ) : null}
    </Section>
  );
}
