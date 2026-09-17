"use client";

import { useId, useState, type ReactNode } from "react";

/** One line of a tooltip: a caption and, optionally, a value on the right. */
export type HelpLine = { label: string; value?: string | number; strong?: boolean };

/**
 * A label with a small "?" that explains it. The explanation opens on hover,
 * on keyboard focus and on tap (a phone has no hover), and the button points
 * at it with `aria-describedby` so a screen reader reads it too — which a
 * bare `title=` attribute does not do reliably and never does on touch.
 */
export function HelpTip({
  children,
  label,
  lines,
}: {
  children: ReactNode;
  /** Accessible name of the "?" button, e.g. "物理リミット の説明". */
  label: string;
  lines: HelpLine[];
}) {
  const id = useId();
  const [open, setOpen] = useState(false);
  return (
    <span className="help-tip" data-open={open || undefined} onMouseLeave={() => setOpen(false)}>
      <span className="help-tip-label">{children}</span>
      <button
        type="button"
        className="help-tip-button"
        aria-label={label}
        aria-describedby={id}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
        onBlur={() => setOpen(false)}
        onKeyDown={(e) => {
          if (e.key === "Escape") setOpen(false);
        }}
      >
        ?
      </button>
      <span role="tooltip" id={id} className="help-tip-body">
        {lines.map((line, i) => (
          <span key={i} className={line.strong ? "help-tip-line strong" : "help-tip-line"}>
            <span>{line.label}</span>
            {line.value !== undefined ? <b>{line.value}</b> : null}
          </span>
        ))}
      </span>
    </span>
  );
}
