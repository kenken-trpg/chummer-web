"use client";

import type { InstalledAdeptPower } from "@/lib/types";
import { attrLabel, type TFn } from "@/lib/ui-strings";
import { limitLabel } from "@/lib/character/format";
import { type MsgKey, useUiText } from "@/lib/i18n";

/** What the power is choosing. Returns the key, not the sentence, so a
 *  caller that already has `ui` can render it in its own locale. */
export function selectLabel(kind?: string | null): MsgKey {
  if (kind === "skill") return "common.skill";
  if (kind === "attribute") return "common.attribute";
  if (kind === "spell") return "spell.kind.spell";
  if (kind === "limit") return "common.limit";
  return "common.target";
}

/** How one option in the dropdown reads: an attribute and a limit are our own
 *  vocabulary, everything else is a data name the glossary translates. */
export function optionLabel(
  name: string,
  kind: string | null | undefined,
  tr: (name: string) => string,
  t: TFn,
  ui: (key: MsgKey) => string,
): string {
  if (kind === "attribute") return attrLabel(name, t);
  if (kind === "limit") return limitLabel(name, ui);
  return tr(name);
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
            {optionLabel(name, item.select, tr, t, ui)}
          </option>
        ))}
      </select>
    </label>
  );
}
