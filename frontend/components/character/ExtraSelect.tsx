"use client";

import type { InstalledAdeptPower } from "@/lib/types";
import { attrLabel, type TFn } from "@/lib/ui-strings";
import { type MsgKey, useUiText } from "@/lib/i18n";

/** What the power is choosing. Returns the key, not the sentence, so a
 *  caller that already has `ui` can render it in its own locale. */
export function selectLabel(kind?: string | null): MsgKey {
  if (kind === "skill") return "common.skill";
  if (kind === "attribute") return "common.attribute";
  if (kind === "spell") return "spell.kind.spell";
  return "common.target";
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
  const { ui } = useUiText();
  if (!item.select) return null;
  return (
    <label>
      {ui(selectLabel(item.select))}
      <select value={item.extra || ""} onChange={(e) => onChange(e.target.value)}>
        <option value="">{ui("common.choose")}</option>
        {item.options.map((name) => (
          <option key={name} value={name}>
            {item.select === "attribute" ? attrLabel(name, t) : tr(name)}
          </option>
        ))}
      </select>
    </label>
  );
}
