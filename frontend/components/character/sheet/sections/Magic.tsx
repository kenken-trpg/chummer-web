import type { SheetData } from "@/lib/character/sheet-data";
import { GradeList, Section } from "@/components/character/sheet/blocks";
import { formatPoints } from "@/lib/character/format";
import { spellDescriptors, spellDuration, spellRange, spellType } from "@/lib/spell-terms";

export function MagicSection(s: SheetData) {
  const { tr, d, enabled } = s;
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
            アデプトパワー（{formatPoints(d.power_points?.used || 0)}/
            {formatPoints(d.power_points?.max || 0)}）
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
            術式
            {d.drain_resist
              ? ` ・ ドレイン抵抗 ${d.drain_resist.pool}（${d.drain_resist.attrs}）`
              : ""}
          </h4>
          <ul className="sheet-list">
            {(d.spells || []).map((item) => (
              <li key={item.id}>
                <b>{tr(item.name)}</b>
                {item.kind && item.kind !== "spell"
                  ? `〔${item.kind === "ritual" ? "儀式" : "付与"}〕`
                  : ""}
                {" ・ "}
                {[
                  tr(item.category || ""),
                  spellType(item.type),
                  spellRange(item.range),
                  spellDuration(item.duration),
                  item.damage ? `ダメージ ${item.damage}` : "",
                  `ドレイン ${item.dv}`,
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
          <h4>精霊</h4>
          <ul className="sheet-list">
            {(d.spirits || []).map((item) => (
              <li key={item.id}>
                <b>{tr(item.name)}</b>
                {" ・ "}F{item.force}
                {item.services != null ? ` ・ サービス ${item.services}` : ""}
                {item.bound ? " ・ 結合" : ""}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {enabled.has("foci") && ((d.foci || []).length || (d.qi_foci || []).length) ? (
        <div className="sheet-block">
          <h4>フォーカス</h4>
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
                <b>気フォーカス {tr(item.name)}</b>
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
          <h4>イニシエーション 等級 {d.initiation?.grade}</h4>
          {(d.initiation?.choices || []).length ? (
            <GradeList items={d.initiation?.choices || []} tr={tr} />
          ) : (
            <p className="sheet-note">メタマジック未選択</p>
          )}
        </div>
      ) : null}
    </Section>
  );
}
