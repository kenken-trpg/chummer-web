import type { SheetData } from "@/lib/character/sheet-data";
import { GradeList, Section } from "@/components/character/sheet/blocks";
import { formatPoints } from "@/lib/character/format";
import { spellDescriptors, spellDuration, spellRange, spellType } from "@/lib/spell-terms";
import { useUiText } from "@/lib/i18n";

export function MagicSection(s: SheetData) {
  const { tr, d, enabled } = s;
  const { ui } = useUiText();
  return (
    <Section
      title="sheet.magic"
      empty={
        !enabled.has("adept") &&
        !enabled.has("spells") &&
        !enabled.has("spirits") &&
        !enabled.has("foci") &&
        !enabled.has("initiation")
      }
    >
      {enabled.has("adept") && (d.adept_powers || []).length ? (
        <div className="sheet-block">
          <h4>
            {ui("sheet.adeptPowers", {
              used: formatPoints(d.power_points?.used || 0),
              max: formatPoints(d.power_points?.max || 0),
            })}
          </h4>
          <ul className="sheet-list">
            {(d.adept_powers || []).map((item) => (
              <li key={item.id}>
                <b>{tr(item.name)}</b>
                {item.rating > 1 ? ` R${item.total_rating ?? item.rating}` : ""}
                {item.extra
                  ? `（${item.select === "attribute" ? item.extra : tr(item.extra)}）`
                  : ""}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {enabled.has("spells") && (d.spells || []).length ? (
        <div className="sheet-block">
          <h4>
            {ui("sheet.spells")}
            {d.drain_resist
              ? ui("sheet.drainResist", {
                  pool: d.drain_resist.pool,
                  attrs: d.drain_resist.attrs,
                })
              : ""}
          </h4>
          <ul className="sheet-list">
            {(d.spells || []).map((item) => (
              <li key={item.id}>
                <b>{tr(item.name)}</b>
                {item.kind && item.kind !== "spell"
                  ? `〔${item.kind === "ritual" ? ui("sheet.ritual") : ui("sheet.enchantment")}〕`
                  : ""}
                {" ・ "}
                {[
                  tr(item.category || ""),
                  spellType(item.type),
                  spellRange(item.range),
                  spellDuration(item.duration),
                  item.damage ? ui("sheet.spellDamage", { damage: item.damage }) : "",
                  ui("sheet.spellDrain", { dv: item.dv }),
                ]
                  .filter(Boolean)
                  .join(" / ")}
                {item.descriptor ? `（${spellDescriptors(item.descriptor)}）` : ""}
                {item.page ? (
                  <span className="sheet-dim">
                    {" "}
                    {item.source || ""} p.{item.page}
                  </span>
                ) : null}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {enabled.has("spirits") && (d.spirits || []).length ? (
        <div className="sheet-block">
          <h4>{ui("sheet.spirits")}</h4>
          <ul className="sheet-list">
            {(d.spirits || []).map((item) => (
              <li key={item.id}>
                <b>{tr(item.name)}</b>
                {" ・ "}F{item.force}
                {item.services != null ? ui("sheet.services", { services: item.services }) : ""}
                {item.bound ? ui("sheet.bound") : ""}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {enabled.has("foci") && ((d.foci || []).length || (d.qi_foci || []).length) ? (
        <div className="sheet-block">
          <h4>{ui("sheet.foci")}</h4>
          <ul className="sheet-list">
            {(d.foci || []).map((item) => (
              <li key={item.id}>
                <b>{tr(item.name)}</b>
                {" ・ "}F{item.force}
                {item.weapon_name ? `（${tr(item.weapon_name)}）` : ""}
              </li>
            ))}
            {(d.qi_foci || []).map((item) => (
              <li key={item.id}>
                <b>{ui("sheet.qiFocus", { name: tr(item.name) })}</b>
                {" ・ "}R{item.rating}
                {item.extra
                  ? `（${item.select === "attribute" ? item.extra : tr(item.extra)}）`
                  : ""}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {enabled.has("initiation") && (d.initiation?.grade || 0) > 0 ? (
        <div className="sheet-block">
          <h4>{ui("sheet.initiation", { grade: d.initiation?.grade ?? 0 })}</h4>
          {(d.initiation?.choices || []).length ? (
            <GradeList items={d.initiation?.choices || []} tr={tr} />
          ) : (
            <p className="sheet-note">{ui("sheet.noMetamagic")}</p>
          )}
        </div>
      ) : null}
    </Section>
  );
}
