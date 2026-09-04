"use client";

import { useState } from "react";

type Option = { id: string; name: string; cost?: string | number };

/**
 * The "pick a mod, press 装着" pair that hangs off an installed row.
 *
 * It owns its own selection. Every tab used to carry a
 * `Record<rowId, selectedId>` in state and reset the entry by hand after the
 * patch; the select is per-row and nothing else reads it, so it belongs here.
 *
 * `rowName` is what makes this accessible: on its own the control is an
 * unnamed combobox, and a sheet with a dozen of them announces "combobox"
 * twelve times. Naming it after the row it modifies ("サイバーアイ: 改造を追加")
 * is the difference between navigable and not.
 */
export function AddonSelect<T extends Option>({
  rowName,
  prompt,
  options,
  onAdd,
  tr,
  addLabel = "装着",
  optionLabel,
  extraFor,
}: {
  rowName: string;
  /** The empty-selection label, e.g. "改造を追加". */
  prompt: string;
  options: T[];
  onAdd: (option: T, extra?: string) => void;
  tr: (name: string) => string;
  addLabel?: string;
  /** Override the option text. The default is `name (cost¥)`; armor mods
   *  price relative to the parent and bring their own formatted string. */
  optionLabel?: (option: T) => string;
  /** Some options need a target chosen with them (an autosoft names the skill
   *  it covers). Return null for the ones that don't. `freeText` gets an input
   *  with the values as a datalist, for the targets that are not a closed set
   *  (a vehicle model, say). */
  extraFor?: (option: T) => { label: string; values: string[]; freeText?: boolean } | null;
}) {
  const [picked, setPicked] = useState("");
  const [extra, setExtra] = useState("");
  if (!options.length) return null;
  const label = `${rowName}: ${prompt}`;
  const selected = options.find((o) => o.id === picked);
  const extraSpec = selected && extraFor ? extraFor(selected) : null;
  return (
    <div className="cyber-controls">
      <select
        aria-label={label}
        value={picked}
        onChange={(e) => {
          setPicked(e.target.value);
          setExtra("");
        }}
      >
        <option value="">{prompt}</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {optionLabel
              ? optionLabel(option)
              : `${tr(option.name)}${option.cost === undefined ? "" : ` (${option.cost}¥)`}`}
          </option>
        ))}
      </select>
      {extraSpec?.freeText ? (
        <>
          <input
            list={`addon-extra-${rowName}`}
            aria-label={`${rowName}: ${extraSpec.label}`}
            placeholder={extraSpec.label}
            value={extra}
            onChange={(e) => setExtra(e.target.value)}
          />
          <datalist id={`addon-extra-${rowName}`}>
            {extraSpec.values.slice(0, 80).map((value) => (
              <option key={value} value={value} />
            ))}
          </datalist>
        </>
      ) : extraSpec ? (
        <select
          aria-label={`${rowName}: ${extraSpec.label}`}
          value={extra}
          onChange={(e) => setExtra(e.target.value)}
        >
          <option value="">{extraSpec.label}</option>
          {extraSpec.values.map((value) => (
            <option key={value} value={value}>
              {tr(value)}
            </option>
          ))}
        </select>
      ) : null}
      <button
        className="btn"
        disabled={!selected}
        aria-label={`${rowName}: ${addLabel}`}
        onClick={() => {
          if (!selected) return;
          onAdd(selected, extra || undefined);
          setPicked("");
          setExtra("");
        }}
      >
        {addLabel}
      </button>
    </div>
  );
}
