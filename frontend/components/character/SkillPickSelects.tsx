"use client";

import type { SkillPickSlot } from "@/lib/types";

export function SkillPickSelects(props: {
  slots: SkillPickSlot[];
  tr: (name: string) => string;
  onPick: (key: string, skill: string) => void;
}) {
  if (!props.slots.length) return null;
  return (
    <div className="skill-picks">
      {props.slots.map((slot) => (
        <label key={slot.key}>
          {props.tr(slot.source)} の技能
          {slot.bonus ? ` ${slot.bonus > 0 ? "+" : ""}${slot.bonus}` : ""}
          {slot.max ? ` 上限+${slot.max}` : ""}
          <select value={slot.picked} onChange={(e) => props.onPick(slot.key, e.target.value)}>
            <option value="">選択してください</option>
            {slot.options.map((name) => (
              <option key={name} value={name}>{props.tr(name)}</option>
            ))}
          </select>
        </label>
      ))}
    </div>
  );
}
