"use client";

import { useCallback, useId, useRef, useState, type ReactNode } from "react";

/** One line of a tooltip: a caption and, optionally, a value on the right. */
export type HelpLine = { label: string; value?: string | number; strong?: boolean };

const NBSP = "\u00a0";

/**
 * Spaces that are not break opportunities.
 *
 * The box is as wide as the sidebar (304px) and no wider, so these lines wrap;
 * the question is only where. Japanese wraps between any two characters, which
 * `word-break: auto-phrase` pulls back to phrase boundaries — but the ASCII
 * spaces inside a formula or a page citation are still fair game to the
 * browser, and that is where the remaining breaks landed:
 *
 *     物理リミット = (BOD×2 + AGI + REA + STR) ÷
 *     3（切り上げ）
 *     …数えられる上限（SR5
 *     p.47）
 *
 * An operator belongs with its operand and a citation is one token, so those
 * particular spaces are made non-breaking here. This is layout, not wording:
 * doing it in the dictionaries would put `\u00a0` escapes through every
 * formula and leave the next translator to maintain them.
 */
const KEEP_TOGETHER: [RegExp, string][] = [
  // a rulebook citation reads as one unit: "SR5 p.47"
  [/\b(SR5) (p\.)/g, `$1${NBSP}$2`],
  // a binary operator with an operand on each side: "8 + BOD", ") ÷ 3"
  [/ ([+÷×−]) /g, `${NBSP}$1${NBSP}`],
  // and one that only has the operand after it: "（+ 修正）"
  [/([+÷×−]) (?=\S)/g, `$1${NBSP}`],
];

/** A caption with its unbreakable runs bound together. Exported for its test. */
export function bindRuns(text: string): string {
  return KEEP_TOGETHER.reduce((acc, [pattern, repl]) => acc.replace(pattern, repl), text);
}

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
  /** Accessible name of the "?" button, e.g. "身体リミット の説明". */
  label: string;
  lines: HelpLine[];
}) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const [style, setStyle] = useState<{ left: number; maxWidth: number }>();
  const body = useRef<HTMLSpanElement>(null);
  /** Put the box where it can actually be read. It hangs off the left edge of
   *  its label, and the sidebar it usually sits in both ends at the window's
   *  right edge and scrolls (`overflow: auto`), so the overflow is clipped,
   *  not merely off-screen. Measure against the nearest scrolling ancestor
   *  when the box is about to show: cap the width to what that ancestor
   *  shows, then slide the box left until it fits inside it. CSS cannot ask
   *  how much room is left. */
  const place = useCallback(() => {
    const el = body.current;
    const anchor = el?.parentElement;
    if (!el || !anchor) return;
    let bounds = new DOMRect(0, 0, window.innerWidth, window.innerHeight);
    for (let node: HTMLElement | null = anchor; node; node = node.parentElement) {
      const overflow = getComputedStyle(node).overflow;
      if (overflow && overflow !== "visible") {
        bounds = node.getBoundingClientRect();
        break;
      }
    }
    const maxWidth = Math.max(120, Math.min(352, bounds.width - 16));
    const width = Math.min(el.offsetWidth || maxWidth, maxWidth);
    const anchorLeft = anchor.getBoundingClientRect().left;
    const wanted = Math.min(anchorLeft, bounds.right - 8 - width);
    const left = Math.max(bounds.left + 8, wanted) - anchorLeft;
    setStyle({ left, maxWidth });
  }, []);
  return (
    <span
      className="help-tip"
      data-open={open || undefined}
      onMouseEnter={place}
      onFocus={place}
      onMouseLeave={() => setOpen(false)}
    >
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
      <span ref={body} role="tooltip" id={id} className="help-tip-body" style={style}>
        {lines.map((line, i) => (
          <span key={i} className={line.strong ? "help-tip-line strong" : "help-tip-line"}>
            <span>{bindRuns(line.label)}</span>
            {line.value !== undefined ? <b>{line.value}</b> : null}
          </span>
        ))}
      </span>
    </span>
  );
}
