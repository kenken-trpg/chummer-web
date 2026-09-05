"use client";
import { RangeInput } from "@/components/character/RangeInput";
import type { TabPanelProps } from "@/components/character/types";
import { ATTRS } from "@/lib/character/constants";
import { attrLabel } from "@/lib/ui-strings";

export function AttrsTab({ character: ch, d, t, ui, patch, setCharacter }: TabPanelProps) {
  const spec = d.metatype_info.attributes;

  return (
    <div className="card">
      {ATTRS.map((key) => {
        const hidden =
          (key === "MAG" && !d.enabled_tabs.includes("MAG")) ||
          (key === "RES" && !d.enabled_tabs.includes("RES"));
        if (hidden) return null;
        const range = spec[key] || { min: 1, max: 6, aug: 6 };
        // A rating below the metatype's racial minimum is not a cheaper
        // character, it is an invalid one — the engine raises it to the floor
        // on the next compute anyway. Show it already there, so the slider and
        // the number beside it never disagree.
        const rating = Math.max(range.min, ch.attributes[key] ?? range.min);
        const commit = (value: number) => patch({ attributes: { ...ch.attributes, [key]: value } });
        return (
          <div className="attr-row" key={key}>
            <span title={ui("attrs.rowHint", { min: range.min, max: range.max, aug: range.aug })}>
              {attrLabel(key, t)}
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
            <b>
              {d.totals[key]} <span className="muted">/{range.max}</span>
              {(d.ware_attr_bonus?.[key] || 0) !== 0 ? (
                <span className="muted">
                  {ui("attrs.wareBonus", { bonus: d.ware_attr_bonus![key] })}
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
      <p className="muted">{ui("attrs.minNote")}</p>
    </div>
  );
}
