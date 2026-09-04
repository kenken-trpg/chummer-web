"use client";

import type { SkillPickSlot } from "@/lib/types";
import { useUiText } from "@/lib/i18n";

export function SkillPickSelects(props: {
  slots: SkillPickSlot[];
  tr: (name: string) => string;
  onPick: (key: string, skill: string) => void;
}) {
  const { ui } = useUiText();
  if (!props.slots.length) return null;
  return (
    <div className="skill-picks">
      {props.slots.map((slot) => (
        <label key={slot.key}>
          {ui("pick.skillOf", { source: props.tr(slot.source) })}
          {slot.bonus ? ` ${slot.bonus > 0 ? "+" : ""}${slot.bonus}` : ""}
          {slot.max ? ui("pick.max", { max: slot.max }) : ""}
          <select value={slot.picked} onChange={(e) => props.onPick(slot.key, e.target.value)}>
            <option value="">{ui("common.choose")}</option>
            {slot.options.map((name) => (
              <option key={name} value={name}>
                {props.tr(name)}
              </option>
            ))}
          </select>
        </label>
      ))}
    </div>
  );
}
