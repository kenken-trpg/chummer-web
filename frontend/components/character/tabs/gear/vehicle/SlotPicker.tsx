"use client";
import type { TabPanelProps } from "@/components/character/types";

/** The "pick one, press 装着" control the vehicle panel repeats for mods,
 *  weapon mounts, sensor functions and interior gear.
 *
 *  All four kept their own copy of the same twenty lines: a `<select>` bound
 *  to `slotPick[key]`, an option list filtered to the core books, a button
 *  disabled until something is picked, and a handler that adds the row and
 *  clears the pick. Only the label, the options and what to add differ, so
 *  those are the props. */
export function SlotPicker<T extends { id: string; name: string; cost?: string | number }>({
  pickKey,
  rowName,
  label,
  options,
  onAdd,
  tr,
  ui,
  slotPick,
  setSlotPick,
}: Pick<TabPanelProps, "tr" | "ui"> & {
  pickKey: string;
  rowName: string;
  label: string;
  options: T[];
  onAdd: (picked: T) => void;
  slotPick: Record<string, string>;
  setSlotPick: (next: (cur: Record<string, string>) => Record<string, string>) => void;
}) {
  if (!options.length) return null;
  const picked = slotPick[pickKey] || "";
  return (
    <div className="cyber-controls">
      <select
        aria-label={`${rowName}: ${label}`}
        value={picked}
        onChange={(e) => setSlotPick((cur) => ({ ...cur, [pickKey]: e.target.value }))}
      >
        <option value="">{label}</option>
        {options.map((opt) => (
          <option key={opt.id} value={opt.id}>
            {tr(opt.name)} ({opt.cost}¥)
          </option>
        ))}
      </select>
      <button
        className="btn"
        disabled={!picked}
        onClick={() => {
          const spec = options.find((opt) => opt.id === picked);
          if (!spec) return;
          onAdd(spec);
          setSlotPick((cur) => ({ ...cur, [pickKey]: "" }));
        }}
      >
        {ui("common.install")}
      </button>
    </div>
  );
}
