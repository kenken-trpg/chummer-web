import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { ATTRS, attrShown } from "@/lib/character/constants";
import { attrShort } from "@/lib/ui-strings";
import { cmSummary, cmThresholdNote, lifeIncrement, limitLabel } from "@/lib/character/format";
import { useUiText } from "@/lib/i18n";
import { renderNotice } from "@/lib/engine-notices";
import { otherMovementRows } from "@/lib/character/movement";

export function CoreSection(s: SheetData) {
  const { tr, t, d, totals, enabled, specialArmor } = s;
  const { ui } = useUiText();
  const form = d.metatype_info.metahuman_form;
  return (
    <Section title="sheet.core">
      <div className="sheet-core">
        {/* one grid cell: both bodies' rows stay in the attribute column */}
        <div>
          {form ? (
            <p className="sheet-note">
              {ui("sheet.form.animal", { name: tr(d.metatype_info.parent || "") })}
            </p>
          ) : null}
          <div className="sheet-attrs">
            {ATTRS.map((key) => {
              if (!attrShown(key, enabled)) return null;
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
          {form ? (
            <>
              <p className="sheet-note">{ui("sheet.form.metahuman", { name: tr(form.name) })}</p>
              <div className="sheet-attrs" data-form="metahuman">
                {ATTRS.filter((key) => form.attributes[key]).map((key) => (
                  <div className="sheet-attr" key={key}>
                    <span>{attrShort(key, t)}</span>
                    <b>{form.attributes[key].total}</b>
                  </div>
                ))}
              </div>
            </>
          ) : null}
        </div>
        <div className="sheet-derived-grid">
          <div>
            <span>{ui("common.initiative")}</span>
            <b>
              {d.initiative.value}+{d.initiative.dice}d6
            </b>
          </div>
          {d.astral_initiative ? (
            <div>
              <span>{ui("common.astralInitiative")}</span>
              <b>
                {d.astral_initiative.value}+{d.astral_initiative.dice}d6
              </b>
            </div>
          ) : null}
          <div>
            <span>{ui("common.condition")}</span>
            <b>{cmSummary(d.condition_monitor, ui)}</b>
            {cmThresholdNote(d.condition_monitor, ui) ? (
              <span className="sheet-dim">{cmThresholdNote(d.condition_monitor, ui)}</span>
            ) : null}
          </div>
          <div>
            <span>{ui("sheet.limits")}</span>
            <b>
              {d.limits.physical} / {d.limits.mental} / {d.limits.social}
            </b>
          </div>
          <div>
            <span>{ui("sheet.movement")}</span>
            <b>
              {ui("sheet.movementValue", {
                walk: d.movement.walk,
                run: d.movement.run,
                sprint: d.movement.sprint,
              })}
            </b>
          </div>
          {form?.movement ? (
            <div>
              <span>{ui("sheet.form.movement")}</span>
              <b>
                {ui("sheet.movementValue", {
                  walk: form.movement.walk,
                  run: form.movement.run,
                  sprint: form.movement.sprint,
                })}
              </b>
            </div>
          ) : null}
          {otherMovementRows(d.movement, ui).map((row) => (
            <div key={row.label}>
              <span>{row.label}</span>
              <b>{row.value}</b>
            </div>
          ))}
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
                {lifeIncrement(d.lifestyle.increment, ui)}
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
                    .map((q) => `${tr(q.name)}${q.extra ? `:${tr(q.extra)}` : ""}`)
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
                {limitLabel(mod.limit, ui)} {mod.value > 0 ? `+${mod.value}` : mod.value}
                {mod.condition_label || mod.condition
                  ? `（${mod.condition_label ? renderNotice(mod.condition_label, ui) : mod.condition}）`
                  : ""}
              </b>
            </div>
          ))}
        </div>
      </div>
    </Section>
  );
}
