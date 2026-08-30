"use client";

import type { InstalledAdeptPower } from "@/lib/types";
import { attrLabel, type TFn } from "@/lib/ui-strings";

export function selectLabel(kind?: string | null) {
  if (kind === "skill") return "技能";
  if (kind === "attribute") return "能力値";
  if (kind === "spell") return "呪文";
  return "対象";
}

export function ExtraSelect({
  item,
  tr,
  t,
  onChange,
}: {
  item: InstalledAdeptPower;
  tr: (name: string) => string;
  t: TFn;
  onChange: (extra: string) => void;
}) {
  if (!item.select) return null;
  return (
    <label>
      {selectLabel(item.select)}
      <select value={item.extra || ""} onChange={(e) => onChange(e.target.value)}>
        <option value="">選択してください</option>
        {item.options.map((name) => (
          <option key={name} value={name}>{item.select === "attribute" ? attrLabel(name, t) : tr(name)}</option>
        ))}
      </select>
    </label>
  );
}
