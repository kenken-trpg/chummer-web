"use client";
import type { UiFn } from "@/lib/i18n";
import { HelpTip } from "@/components/help/HelpTip";
import { BoundedNumberInput } from "@/components/character/BoundedNumberInput";

/**
 * The price of an item the rules leave to the player — `Variable(lo-hi)` in
 * Chummer's data: a Custom Item, Clothing, a Commlink App. Nothing to show
 * for a fixed price.
 */
export function PriceField({
  range,
  value,
  label,
  ui,
  onChange,
}: {
  range: [number, number] | null | undefined;
  value: number;
  label: string;
  ui: UiFn;
  onChange: (cost: number) => void;
}) {
  if (!range) return null;
  const [lo, hi] = range;
  return (
    <HelpTip
      label={ui("help.open", { label: `${label}: ${ui("gear.price")}` })}
      lines={[
        { label: ui("help.gear.price", { lo: lo.toLocaleString(), hi: hi.toLocaleString() }) },
      ]}
    >
      <label>
        {ui("gear.price")}
        <BoundedNumberInput
          aria-label={`${label}: ${ui("gear.price")}`}
          min={lo}
          max={hi}
          value={value}
          onCommit={onChange}
        />
      </label>
    </HelpTip>
  );
}
