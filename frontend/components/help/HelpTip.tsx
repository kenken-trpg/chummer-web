"use client";

import {
  useCallback,
  useEffect,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type ReactNode,
} from "react";

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
 *     身体リミット = (STR×2 + BOD + REA) ÷
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

/** A box on screen, in viewport coordinates. */
export type Box = { left: number; top: number; right: number; bottom: number };

/** Space between the label and the box, and between the box and an edge. */
const GAP = 4;
const MARGIN = 8;

/** How wide the box may get inside `bounds`. */
export function widthCap(bounds: Box): number {
  return Math.max(120, Math.min(352, bounds.right - bounds.left - 2 * MARGIN));
}

/**
 * Where a box of `width` × `height` goes under (or over) `anchor` so it stays
 * inside `bounds`. `left` is relative to the anchor's left edge. The box hangs
 * below its label and slides left until it fits; it goes above only when it
 * does not fit below and there is more room above — near the bottom of the
 * sidebar, which scrolls and clips what runs past it.
 */
export function fitBox(
  anchor: Box,
  bounds: Box,
  width: number,
  height: number,
): { left: number; above: boolean } {
  const wanted = Math.min(anchor.left, bounds.right - MARGIN - width);
  const left = Math.max(bounds.left + MARGIN, wanted) - anchor.left;
  const below = bounds.bottom - anchor.bottom - GAP - MARGIN;
  const above = anchor.top - bounds.top - GAP - MARGIN;
  return { left, above: height > below && above > below };
}

/** What the box can be seen inside: the nearest scrolling ancestor, which
 *  clips (the sidebar is `overflow: auto`), cut down to the window. */
function visibleBounds(from: HTMLElement): Box {
  let box: Box = { left: 0, top: 0, right: window.innerWidth, bottom: window.innerHeight };
  for (let node: HTMLElement | null = from; node; node = node.parentElement) {
    const overflow = getComputedStyle(node).overflow;
    if (overflow && overflow !== "visible") {
      const r = node.getBoundingClientRect();
      box = {
        left: Math.max(box.left, r.left),
        top: Math.max(box.top, r.top),
        right: Math.min(box.right, r.right),
        bottom: Math.min(box.bottom, r.bottom),
      };
      break;
    }
  }
  return box;
}

/** What holds the box open. `dismissed` is Escape, a second tap or a tap
 *  outside: it outvotes the rest until the pointer or the focus arrives again. */
type Why = { hovered: boolean; focused: boolean; pinned: boolean; dismissed: boolean };
const SHUT: Why = { hovered: false, focused: false, pinned: false, dismissed: false };

/**
 * A label with a small "?" that explains it. The explanation opens on hover,
 * on keyboard focus and on tap (a phone has no hover), and the button points
 * at it with `aria-describedby` so a screen reader reads it too — which a
 * bare `title=` attribute does not do reliably and never does on touch.
 *
 * Whether it shows is `open` and nothing else. It used to be CSS `:hover` and
 * `:focus-within` as well, and those outvoted the state: Escape and a second
 * tap on the "?" set `open` to false and the box stayed up, because the button
 * still had focus (or, on iOS, the sticky hover). WCAG 1.4.13 asks that it be
 * dismissible without moving the pointer or the focus.
 *
 * - hover or focus opens it, and it stays while either holds — focus keeps
 *   it up when the page shifts out from under a parked pointer
 * - a tap (click) pins it open; a second tap closes it
 * - Escape closes it wherever the pointer and focus are; so does a tap outside.
 *   It stays closed until the pointer or the focus comes back afresh.
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
  const [why, setWhy] = useState(SHUT);
  const open = !why.dismissed && (why.pinned || why.hovered || why.focused);
  const root = useRef<HTMLSpanElement>(null);
  const body = useRef<HTMLSpanElement>(null);
  const close = useCallback(() => setWhy((w) => ({ ...w, pinned: false, dismissed: true })), []);

  /** Put the box where it can actually be read, once it is shown and so has
   *  a size. Written straight to the element: CSS cannot ask how much room is
   *  left, and a state round trip would paint it in the wrong place first. */
  useLayoutEffect(() => {
    const el = body.current;
    const anchor = root.current;
    if (!open || !el || !anchor) return;
    const bounds = visibleBounds(anchor);
    el.style.maxWidth = `${widthCap(bounds)}px`;
    const { left, above } = fitBox(
      anchor.getBoundingClientRect(),
      bounds,
      el.offsetWidth,
      el.offsetHeight,
    );
    el.style.left = `${left}px`;
    if (above) anchor.dataset.side = "above";
    else delete anchor.dataset.side;
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") close();
    };
    const onDown = (e: PointerEvent) => {
      if (!root.current?.contains(e.target as Node)) close();
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onDown);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onDown);
    };
  }, [open, close]);

  return (
    <span
      ref={root}
      className="help-tip"
      data-open={open || undefined}
      onMouseEnter={() => setWhy((w) => ({ ...w, hovered: true, dismissed: false }))}
      onMouseLeave={() => setWhy((w) => ({ ...w, hovered: false }))}
      onFocus={() => setWhy((w) => ({ ...w, focused: true, dismissed: w.focused && w.dismissed }))}
      onBlur={(e) => {
        if (e.currentTarget.contains(e.relatedTarget as Node | null)) return;
        setWhy((w) => ({ ...w, focused: false, pinned: false }));
      }}
    >
      <span className="help-tip-label">{children}</span>
      <button
        type="button"
        className="help-tip-button"
        aria-label={label}
        aria-describedby={id}
        aria-expanded={open}
        onClick={() =>
          setWhy((w) =>
            w.pinned
              ? { ...w, pinned: false, dismissed: true }
              : { ...w, pinned: true, dismissed: false },
          )
        }
      >
        ?
      </button>
      <span ref={body} role="tooltip" id={id} className="help-tip-body">
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
