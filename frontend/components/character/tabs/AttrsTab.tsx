"use client";
import { RangeInput } from "@/components/character/RangeInput";
import { HelpTip } from "@/components/help/HelpTip";
import type { TabPanelProps } from "@/components/character/types";
import { ATTRS, attrShown } from "@/lib/character/constants";
import { attrLabel } from "@/lib/ui-strings";

export function AttrsTab({ character: ch, d, t, tr, ui, patch, setCharacter }: TabPanelProps) {
  const spec = d.metatype_info.attributes;
  // Priority / Sum-to-Ten creation only: a Karma build buys every level with
  // karma already, and after creation raises are billed from the baseline.
  const splitKarma = !ch.career && !d.karma_chargen?.enabled;
  const karmaSplit = d.attribute_karma;
  const form = d.metatype_info.metahuman_form;
  // the sliders are the animal's, so the number beside them is too, whichever
  // form `totals` is in
  const animalTotals = d.metatype_info.animal_form?.totals;

  return (
    <div className="card">
      {form ? (
        <label className="option-row">
          <HelpTip
            label={ui("help.open", { label: ui("attrs.activeForm") })}
            lines={[{ label: ui("attrs.activeFormHint") }]}
          >
            {ui("attrs.activeForm")}
          </HelpTip>{" "}
          <select
            aria-label={ui("attrs.activeForm")}
            value={d.metatype_info.active_form || "animal"}
            onChange={(e) => patch({ shapeshifter_form: e.target.value })}
          >
            <option value="animal">
              {ui("sheet.form.animal", { name: tr(d.metatype_info.parent || "") })}
            </option>
            <option value="metahuman">{ui("sheet.form.metahuman", { name: tr(form.name) })}</option>
          </select>
        </label>
      ) : null}
      {ATTRS.map((key) => {
        if (!attrShown(key, d.enabled_tabs)) return null;
        const range: (typeof spec)[string] = spec[key] || { min: 1, max: 6, aug: 6 };
        // An A.I. has no body: its BOD to STR are 0 and nothing raises them.
        if (range.max === 0) return null;
        // A rating below the metatype's racial minimum is not a cheaper
        // character, it is an invalid one — the engine raises it to the floor
        // on the next compute anyway. Show it already there, so the slider and
        // the number beside it never disagree.
        const rating = Math.max(range.min, ch.attributes[key] ?? range.min);
        // MAG / RES / DEP under essence loss: the slider stays on what was
        // bought, and the range the loss left is shown beside the total
        const essMax = range.ess_max;
        const showKarma = splitKarma && !!karmaSplit && key in karmaSplit.floors;
        const commit = (value: number) => patch({ attributes: { ...ch.attributes, [key]: value } });
        return (
          <div className={showKarma ? "attr-row has-karma" : "attr-row"} key={key}>
            <span>
              <HelpTip
                label={ui("help.open", { label: attrLabel(key, t) })}
                lines={[
                  { label: ui(`help.attr.${key}`) },
                  {
                    label: ui("attrs.rowHint", { min: range.min, max: range.max, aug: range.aug }),
                  },
                  ...(essMax !== undefined ? [{ label: ui("attrs.essenceRangeHint") }] : []),
                ]}
              >
                {attrLabel(key, t)}
              </HelpTip>
            </span>
            <RangeInput
              min={range.min}
              max={range.max}
              value={rating}
              floor={range.min}
              label={attrLabel(key, t)}
              title={ui("attrs.rowHint", { min: range.min, max: range.max, aug: range.aug })}
              onDraft={(value) =>
                setCharacter({ ...ch, attributes: { ...ch.attributes, [key]: value } })
              }
              onCommit={commit}
            />
            {showKarma && karmaSplit ? (
              <label className="attr-karma" title={ui("attrs.karmaHint")}>
                {ui("attrs.karmaLevels")}
                <input
                  type="number"
                  aria-label={`${attrLabel(key, t)} ${ui("attrs.karmaLevels")}`}
                  min={0}
                  max={Math.max(0, rating - karmaSplit.floors[key])}
                  value={karmaSplit.levels[key] ?? 0}
                  onChange={(e) =>
                    patch({
                      attribute_karma: {
                        ...(ch.attribute_karma || {}),
                        [key]: Math.max(0, Number(e.target.value) || 0),
                      },
                    })
                  }
                />
              </label>
            ) : null}
            <b>
              {animalTotals?.[key] ?? d.totals[key]}{" "}
              <span className="muted">/{essMax ?? range.max}</span>
              {essMax !== undefined ? (
                <span className="muted">
                  {ui("attrs.essenceRange", {
                    min: range.ess_min ?? 0,
                    max: essMax,
                  })}
                </span>
              ) : null}
              {(d.ware_attr_bonus?.[key] || 0) !== 0 ? (
                <span className="muted">
                  {ui("attrs.wareBonus", { bonus: d.ware_attr_bonus![key] })}
                </span>
              ) : null}
              {form?.attributes[key] ? (
                <span className="muted">
                  {ui("attrs.formValue", { value: form.attributes[key].total })}
                </span>
              ) : null}
              {d.limb_replace && (key === "STR" || key === "AGI") ? (
                <span className="muted">
                  {ui("attrs.meat", {
                    value: key === "STR" ? d.limb_replace.meat_str : d.limb_replace.meat_agi,
                  })}
                </span>
              ) : null}
            </b>
          </div>
        );
      })}
      <p className="muted">
        {ui("attrs.points", {
          used: d.points.attributes.used,
          max: d.points.attributes.max,
          specialUsed: d.points.special.used,
          specialMax: d.points.special.max,
        })}
      </p>
      {splitKarma && karmaSplit && karmaSplit.karma > 0 ? (
        <p className="muted">{ui("attrs.karmaSpent", { karma: karmaSplit.karma })}</p>
      ) : null}
      <p className="muted">{ui("attrs.minNote")}</p>
      {form ? (
        <p className="muted">
          {ui("attrs.formNote", {
            animal: tr(d.metatype_info.parent || ""),
            form: tr(form.name),
          })}
        </p>
      ) : null}
      {/* Infected / Quadriplegic: these are no longer the metatype's ranges. */}
      {(d.metatype_info.attributes_replaced_by || []).length ? (
        <p className="muted">
          {ui("attrs.replacedRanges", {
            list: (d.metatype_info.attributes_replaced_by || []).map((name) => tr(name)).join("、"),
          })}
        </p>
      ) : null}
    </div>
  );
}
