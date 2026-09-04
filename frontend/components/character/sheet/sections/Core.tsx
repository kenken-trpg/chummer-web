import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { ATTRS } from "@/lib/character/constants";
import { attrShort } from "@/lib/ui-strings";
import { lifeIncrement } from "@/lib/character/format";
import { useUiText } from "@/lib/i18n";

export function CoreSection(s: SheetData) {
  const { tr, t, d, totals, enabled, specialArmor } = s;
  const { ui } = useUiText();
  return (
    <Section title="sheet.core">
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
            <span>{ui("common.initiative")}</span>
            <b>
              {d.initiative.value}+{d.initiative.dice}d6
            </b>
          </div>
          <div>
            <span>{ui("common.condition")}</span>
            <b>
              P{d.condition_monitor.physical} / S{d.condition_monitor.stun}
            </b>
          </div>
          <div>
            <span>{ui("sheet.limits")}</span>
            <b>
              {d.limits.physical} / {d.limits.mental} / {d.limits.social}
            </b>
          </div>
          <div>
            <span>{ui("sheet.movement")}</span>
            <b>{ui("sheet.movementValue", { walk: d.movement.walk, run: d.movement.run })}</b>
          </div>
          {(d.damage_resistance || 0) > 0 ? (
            <div>
              <span>{ui("sheet.damageResist")}</span>
              <b>+{d.damage_resistance}</b>
            </div>
          ) : null}
          {(d.unarmed_dv || 0) > 0 ? (
            <div>
              <span>{ui("sheet.unarmedDv")}</span>
              <b>+{d.unarmed_dv}</b>
            </div>
          ) : null}
          {(d.unarmed_reach || 0) > 0 ? (
            <div>
              <span>{ui("sheet.unarmedReach")}</span>
              <b>+{d.unarmed_reach}</b>
            </div>
          ) : null}
          {(d.unarmed_ap ?? 0) !== 0 ? (
            <div>
              <span>{ui("sheet.unarmedAp")}</span>
              <b>{(d.unarmed_ap ?? 0) > 0 ? `+${d.unarmed_ap}` : d.unarmed_ap}</b>
            </div>
          ) : null}
          {d.lifestyle ? (
            <div>
              <span>{ui("sheet.lifestyle")}</span>
              <b>
                {tr(d.lifestyle.name)} {d.lifestyle.months}
                {lifeIncrement(d.lifestyle.increment)}
                {d.lifestyle.lp_max
                  ? ui("sheet.lifestyleLp", {
                      used: d.lifestyle.lp_used || 0,
                      max: d.lifestyle.lp_max,
                    })
                  : ""}
              </b>
              {(d.lifestyle.qualities || []).length ? (
                <em>
                  {(d.lifestyle.qualities || [])
                    .map((q) => `${tr(q.name)}${q.extra ? `:${q.extra}` : ""}`)
                    .join(ui("common.listSep"))}
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
              <span>{ui("sheet.limitMod")}</span>
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
