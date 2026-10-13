"use client";

import type { ReactNode } from "react";
import type { QualityExtras } from "@/lib/character/quality-extras";

/** Several controls for one quality, wrapping on a narrow screen. */
export function ExtraRow({ children }: { children: ReactNode }) {
  return (
    <div className="option-row" style={{ flexWrap: "wrap", gap: 8 }}>
      {children}
    </div>
  );
}

/**
 * One dropdown for a quality's target.
 *
 * `prompt` is both the placeholder option and the accessible name, because the
 * placeholder is the only visible cue: without the name, a character with a
 * dozen qualities that take a target announces a dozen identical comboboxes.
 */
export function ExtraSelect({
  extras,
  storeKey,
  prompt,
  named,
  options,
  label,
  /** Whether a value the option list does not contain counts as unselected.
   *  True where a free-text box shares the key: what was typed is not one of
   *  the options, and the select must not claim it is. */
  strict,
}: {
  extras: QualityExtras;
  storeKey: string;
  prompt: string;
  named: (prompt: string) => string;
  options: string[];
  label: (name: string) => string;
  strict?: boolean;
}) {
  const current = extras.read(storeKey);
  return (
    <select
      aria-label={named(prompt)}
      value={strict && !options.includes(current) ? "" : current}
      onChange={(e) => extras.commit(storeKey, e.target.value)}
    >
      <option value="">{prompt}</option>
      {options.map((name) => (
        <option key={name} value={name}>
          {label(name)}
        </option>
      ))}
    </select>
  );
}

/**
 * A free-text box beside a dropdown, for the targets the catalog does not
 * enumerate — an allergen, a code of honour, a Matrix action from a book we
 * have no list for.
 *
 * It drafts while typing and commits on blur: patching per keystroke would
 * re-render the whole panel from the engine between letters.
 */
export function ExtraText({
  extras,
  storeKey,
  placeholder,
  name,
}: {
  extras: QualityExtras;
  storeKey: string;
  placeholder: string;
  /** The accessible name, already qualified by the quality. */
  name: string;
}) {
  return (
    <input
      type="text"
      placeholder={placeholder}
      aria-label={name}
      value={extras.read(storeKey)}
      onChange={(e) => extras.draft(storeKey, e.target.value)}
      onBlur={(e) => extras.commit(storeKey, e.target.value)}
    />
  );
}
