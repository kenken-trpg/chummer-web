"use client";
import type { UiFn } from "@/lib/i18n";

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
    <label title={ui("gear.priceHint", { lo: lo.toLocaleString(), hi: hi.toLocaleString() })}>
      {ui("gear.price")}
      <input
        type="number"
        aria-label={`${label}: ${ui("gear.price")}`}
        min={lo}
        max={hi}
        value={value}
        onChange={(e) => onChange(Math.max(lo, Math.min(hi, Number(e.target.value) || 0)))}
      />
    </label>
  );
}
