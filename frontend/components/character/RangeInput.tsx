"use client";

import { useId } from "react";

/**
 * A range slider that says where its stops are.
 *
 * A bare `<input type="range">` shows a thumb on a blank track: the only way
 * to find out that dragging one pixel further buys you rating 4 is to drag and
 * watch the number beside it change. Every rating on this page is an integer
 * from a short range, so the positions can simply be drawn — a tick per step,
 * numbered, with the current one highlighted.
 *
 * The tick row is `aria-hidden`: it is a redraw of the slider's own value, and
 * a screen reader already gets that from the input.
 */
export function RangeInput({
  min,
  max,
  value,
  onDraft,
  onCommit,
  label,
  title,
  disabled,
  /** Marked on the scale as a floor the value can never go under — the
   *  metatype's racial minimum on the attribute sliders. */
  floor,
}: {
  min: number;
  max: number;
  value: number;
  /** Every drag frame. Update local state here, do not hit the API. */
  onDraft: (value: number) => void;
  /** Pointer released / focus left. Commit here. */
  onCommit: (value: number) => void;
  label?: string;
  title?: string;
  disabled?: boolean;
  floor?: number;
}) {
  const id = useId();
  const lo = Math.min(min, max);
  const hi = Math.max(min, max);
  const span = hi - lo;
  // Clamp for display: a stored rating can sit outside the range after a
  // metatype swap, and a slider whose value is off its own track lies about
  // where the thumb is.
  const shown = Math.min(hi, Math.max(lo, value));

  // At most ~13 numbers, else they collide. Beyond that, label every Nth stop
  // (the untitled ticks in between still mark the steps).
  const stride = Math.max(1, Math.ceil((span + 1) / 13));
  const stops: number[] = [];
  for (let v = lo; v <= hi; v += 1) stops.push(v);

  return (
    <div className="range">
      <input
        id={id}
        type="range"
        min={lo}
        max={hi}
        value={shown}
        disabled={disabled}
        aria-label={label}
        title={title}
        onChange={(e) => onDraft(Number(e.target.value))}
        onMouseUp={(e) => onCommit(Number((e.target as HTMLInputElement).value))}
        onTouchEnd={(e) => onCommit(Number((e.target as HTMLInputElement).value))}
        onKeyUp={(e) => onCommit(Number((e.target as HTMLInputElement).value))}
        onBlur={(e) => onCommit(Number(e.target.value))}
      />
      <div className="range-scale" aria-hidden="true">
        {stops.map((v) => {
          const pct = span === 0 ? 50 : ((v - lo) / span) * 100;
          const classes = ["range-tick"];
          if (v === shown) classes.push("here");
          if (floor !== undefined && v === floor) classes.push("floor");
          const labelled = v === lo || v === hi || v === shown || (v - lo) % stride === 0;
          return (
            <span
              key={v}
              className={classes.join(" ")}
              // The thumb's centre is inset by half its width at each end, so a
              // flat percentage would drift off the tick it names.
              style={{ left: `calc(${pct}% + (0.5 - ${pct / 100}) * var(--thumb))` }}
            >
              <i />
              {labelled ? <em>{v}</em> : null}
            </span>
          );
        })}
      </div>
    </div>
  );
}
