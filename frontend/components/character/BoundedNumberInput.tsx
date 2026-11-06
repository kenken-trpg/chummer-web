"use client";

import { useState, type InputHTMLAttributes } from "react";

/**
 * A number box for a value the server clamps to `[min, max]`.
 *
 * The value shown is usually the computed one (`derived`), so a plain
 * controlled `<input type="number">` that patches on every keystroke loses the
 * edit halfway: clearing the box sends 0, the server answers with the minimum,
 * and the next digit lands beside it — "1" then "3" is 13, clamped to the
 * maximum. Only the minimum and the maximum could be typed in.
 *
 * Here the text being typed stays the box's own while it has focus. A text
 * that reads as a whole number inside the range is sent straight away, so the
 * spinner and a single digit act as before; anything else (empty, out of
 * range) waits, and leaving the box sends it clamped, or puts the value back.
 */
export function BoundedNumberInput({
  min,
  max,
  value,
  onCommit,
  ...rest
}: {
  min: number;
  max: number;
  value: number;
  onCommit: (value: number) => void;
} & Omit<InputHTMLAttributes<HTMLInputElement>, "min" | "max" | "value" | "onChange" | "type">) {
  const [draft, setDraft] = useState<string | null>(null);
  const lo = Math.min(min, max);
  const hi = Math.max(min, max);
  const parse = (text: string) => {
    if (!/^-?\d+$/.test(text.trim())) return null;
    return Number(text);
  };
  return (
    <input
      {...rest}
      type="number"
      min={lo}
      max={hi}
      value={draft ?? value}
      onChange={(e) => {
        const text = e.target.value;
        setDraft(text);
        const n = parse(text);
        if (n !== null && n >= lo && n <= hi && n !== value) onCommit(n);
      }}
      onBlur={(e) => {
        const n = parse(draft ?? "");
        setDraft(null);
        if (n !== null) {
          const clamped = Math.min(hi, Math.max(lo, n));
          if (clamped !== value) onCommit(clamped);
        }
        rest.onBlur?.(e);
      }}
    />
  );
}
