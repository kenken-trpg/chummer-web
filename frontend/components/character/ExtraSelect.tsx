"use client";

import type { InstalledAdeptPower } from "@/lib/types";
import { ATTR_JA } from "@/lib/character/constants";

export function selectLabel(kind?: string | null) {
  if (kind === "skill") return "スキル";
  if (kind === "attribute") return "属性";
  if (kind === "spell") return "呪文";
  return "対象";
}

export function ExtraSelect({
  item,
  tr,
  onChange,
}: {
  item: InstalledAdeptPower;
  tr: (name: string) => string;
  onChange: (extra: string) => void;
}) {
  if (!item.select) return null;
  return (
    <label>
      {selectLabel(item.select)}
      <select value={item.extra || ""} onChange={(e) => onChange(e.target.value)}>
        <option value="">選択してください</option>
        {item.options.map((name) => (
          <option key={name} value={name}>{item.select === "attribute" ? (ATTR_JA[name] || name) : tr(name)}</option>
        ))}
      </select>
    </label>
  );
}
