import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { ATTRS } from "@/lib/character/constants";
import { attrShort } from "@/lib/ui-strings";
import { lifeIncrement } from "@/lib/character/sheet-format";

export function CoreSection(s: SheetData) {
  const { tr, t, d, totals, enabled, specialArmor } = s;
  return (
    <Section title="コア">
      <div className="sheet-core">
        <div className="sheet-attrs">
          {ATTRS.map((key) => {
            if ((key === "MAG" && !enabled.has("MAG")) || (key === "RES" && !enabled.has("RES")))
              return null;
            const ware = d.ware_attr_bonus?.[key] || 0;
            return (
              <div className="sheet-attr" key={key}>
                <span>{attrShort(key, t)}</span>
                <b>{totals[key] ?? "-"}</b>
                {ware ? <em>+{ware}</em> : null}
              </div>
            );
          })}
        </div>
        <div className="sheet-derived-grid">
          <div>
            <span>イニシアチブ</span>
            <b>
              {d.initiative.value}+{d.initiative.dice}d6
            </b>
          </div>
          <div>
            <span>コンディション</span>
            <b>
              P{d.condition_monitor.physical} / S{d.condition_monitor.stun}
            </b>
          </div>
          <div>
            <span>リミット</span>
            <b>
              {d.limits.physical} / {d.limits.mental} / {d.limits.social}
            </b>
          </div>
          <div>
            <span>移動</span>
            <b>
              歩{d.movement.walk} / 走{d.movement.run}
            </b>
          </div>
          {(d.damage_resistance || 0) > 0 ? (
            <div>
              <span>ダメージ抵抗</span>
              <b>+{d.damage_resistance}</b>
            </div>
          ) : null}
          {(d.unarmed_dv || 0) > 0 ? (
            <div>
              <span>非武装DV</span>
              <b>+{d.unarmed_dv}</b>
            </div>
          ) : null}
          {(d.unarmed_reach || 0) > 0 ? (
            <div>
              <span>非武装リーチ</span>
              <b>+{d.unarmed_reach}</b>
            </div>
          ) : null}
          {(d.unarmed_ap ?? 0) !== 0 ? (
            <div>
              <span>非武装AP</span>
              <b>{(d.unarmed_ap ?? 0) > 0 ? `+${d.unarmed_ap}` : d.unarmed_ap}</b>
            </div>
          ) : null}
          {d.lifestyle ? (
            <div>
              <span>ライフスタイル</span>
              <b>
                {tr(d.lifestyle.name)} {d.lifestyle.months}
                {lifeIncrement(d.lifestyle.increment)}
                {d.lifestyle.lp_max
                  ? `（LP ${d.lifestyle.lp_used || 0}/${d.lifestyle.lp_max}）`
                  : ""}
              </b>
              {(d.lifestyle.qualities || []).length ? (
                <em>
                  {(d.lifestyle.qualities || [])
                    .map((q) => `${tr(q.name)}${q.extra ? `:${q.extra}` : ""}`)
                    .join("、")}
                </em>
              ) : null}
            </div>
          ) : null}
          {specialArmor.map((row) => (
            <div key={row.label}>
              <span>{row.label}</span>
              <b>{row.value}</b>
            </div>
          ))}
          {(d.limit_modifiers || []).map((mod, idx) => (
            <div key={`${mod.limit}-${idx}`}>
              <span>条件リミット</span>
              <b>
                {mod.limit} {mod.value > 0 ? `+${mod.value}` : mod.value}
                {mod.condition_label || mod.condition
                  ? `（${mod.condition_label || mod.condition}）`
                  : ""}
              </b>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}
