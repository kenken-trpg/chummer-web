import type { SheetData } from "@/lib/character/sheet-data";
import { ATTRS } from "@/lib/character/constants";
import { attrShort } from "@/lib/ui-strings";
import { lifeIncrement } from "@/lib/character/sheet-format";

/** Page-1 "stat block" for the print layout: attributes (base + augment),
 * limits, initiative, movement, and the derived defense / soak pools a table
 * needs at a glance. Replaces `CoreSection` in print order, so it also carries
 * the lifestyle / unarmed / special-armor / conditional-limit lines Core shows.
 * Pure `(s: SheetData) => JSX`; the pool sums are composed from `totals` / `d`,
 * no new rules. */
export function PrintStatBlock(s: SheetData) {
  const { tr, t, d, totals, enabled, specialArmor } = s;

  const attrs = ATTRS.filter(
    (key) => !((key === "MAG" && !enabled.has("MAG")) || (key === "RES" && !enabled.has("RES"))),
  );

  const rea = totals.REA || 0;
  const int = totals.INT || 0;
  const bod = totals.BOD || 0;
  const wil = totals.WIL || 0;
  const cha = totals.CHA || 0;

  const defensePool = rea + int + (d.test_mods?.dodge || 0);
  const soakPool = bod + (d.armor || 0) + (d.damage_resistance || 0);
  const composure = wil + cha + (d.test_mods?.composure || 0);
  const judge = int + cha + (d.test_mods?.judge_intentions || 0);
  const memory = (totals.LOG || 0) + wil + (d.test_mods?.memory || 0);

  const stats: { label: string; value: string }[] = [
    { label: "物理リミット", value: String(d.limits.physical) },
    { label: "精神リミット", value: String(d.limits.mental) },
    { label: "社会リミット", value: String(d.limits.social) },
    { label: "イニシアチブ", value: `${d.initiative.value} + ${d.initiative.dice}d6` },
    { label: "移動 (歩/走)", value: `${d.movement.walk} / ${d.movement.run}` },
    { label: "防御プール", value: String(defensePool) },
    { label: "ダメージ抵抗", value: String(soakPool) },
    { label: "エッセンス", value: d.essence.toFixed(2) },
    { label: "沈着", value: String(composure) },
    { label: "意図看破", value: String(judge) },
    { label: "記憶", value: String(memory) },
  ];
  if ((d.unarmed_dv || 0) > 0) stats.push({ label: "非武装DV", value: `+${d.unarmed_dv}` });
  if ((d.unarmed_reach || 0) > 0)
    stats.push({ label: "非武装リーチ", value: `+${d.unarmed_reach}` });
  if ((d.unarmed_ap ?? 0) !== 0)
    stats.push({
      label: "非武装AP",
      value: (d.unarmed_ap ?? 0) > 0 ? `+${d.unarmed_ap}` : String(d.unarmed_ap),
    });
  for (const row of specialArmor) stats.push({ label: row.label, value: row.value });
  for (const mod of d.limit_modifiers || [])
    stats.push({
      label: `条件リミット (${mod.limit})`,
      value: `${mod.value > 0 ? `+${mod.value}` : mod.value}${
        mod.condition_label || mod.condition ? `／${mod.condition_label || mod.condition}` : ""
      }`,
    });

  return (
    <section className="sheet-section sheet-section--print print-statblock">
      <h3>ステータス</h3>
      <div className="print-attr-row">
        {attrs.map((key) => {
          const ware = d.ware_attr_bonus?.[key] || 0;
          return (
            <div className="print-attr" key={key}>
              <span>{attrShort(key, t)}</span>
              <b>{totals[key] ?? "-"}</b>
              {ware ? <em>+{ware}</em> : null}
            </div>
          );
        })}
      </div>
      <div className="print-stat-grid">
        {stats.map((row) => (
          <div className="print-stat" key={row.label}>
            <span>{row.label}</span>
            <b>{row.value}</b>
          </div>
        ))}
      </div>
      {d.lifestyle ? (
        <p className="sheet-note">
          ライフスタイル: {tr(d.lifestyle.name)} {d.lifestyle.months}
          {lifeIncrement(d.lifestyle.increment)}
          {d.lifestyle.lp_max ? `（LP ${d.lifestyle.lp_used || 0}/${d.lifestyle.lp_max}）` : ""}
          {(d.lifestyle.qualities || []).length
            ? ` ・ ${(d.lifestyle.qualities || [])
                .map((q) => `${tr(q.name)}${q.extra ? `:${q.extra}` : ""}`)
                .join("、")}`
            : ""}
        </p>
      ) : null}
    </section>
  );
}
