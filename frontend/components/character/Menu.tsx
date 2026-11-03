import { useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";

/**
 * A button that drops a column of other buttons under it.
 *
 * Open state is React's rather than `<details>`'s: the toolbar's own tests and
 * the e2e suite click the items inside, and a native `<summary>` toggle is not
 * something every DOM implementation we test against performs.
 */
export function Menu({
  label,
  note,
  children,
}: {
  label: string;
  /**
   * A word shown on the button in place of its label, outliving the panel. Picking an item closes
   * the menu, so an item that reports on itself (コピー ✓ on its own label)
   * reports to nobody — the panel is gone before anyone reads it.
   */
  note?: ReactNode;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  // Which edge of the button the panel hangs from. 書き出し sits at the right
  // end of the toolbar on a wide tab (the sheet), where a panel hung from its
  // left edge runs off the window and cuts the last item in half.
  const [alignEnd, setAlignEnd] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const body = useRef<HTMLDivElement>(null);

  // Before paint, so the panel never shows on the wrong side for a frame.
  // Reset to the left edge on each open (the button's click), not here: the
  // toolbar may have wrapped since, and the button left the edge.
  useLayoutEffect(() => {
    if (!open) return;
    const panel = body.current;
    if (!panel || alignEnd) return;
    const room = document.documentElement.clientWidth;
    if (panel.getBoundingClientRect().right > room) setAlignEnd(true);
  }, [open, alignEnd]);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (!box.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    // Picking an item is the end of the errand, so the menu gets out of the
    // way. The checkbox inside is not a button and so leaves the menu open,
    // which is what you want — it changes what the next item writes.
    //
    // On `document`, not on the panel: React listens on its own root, which is
    // below this. Closing from a listener under the root unmounts the button
    // before the click reaches React, and the item's own handler never runs.
    const onPick = (e: Event) => {
      const el = e.target as HTMLElement;
      // a "?" (HelpTip) is a button too, but opening it is not picking an item
      if (body.current?.contains(el) && el.closest("button:not(.help-tip-button)")) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    document.addEventListener("click", onPick);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("click", onPick);
    };
  }, [open]);

  return (
    <div className="menu" ref={box}>
      <button
        className="btn"
        // the name stays put while the face below says コピー ✓
        aria-label={`${label} ▾`}
        aria-expanded={open}
        onClick={() => {
          if (!open) setAlignEnd(false);
          setOpen(!open);
        }}
      >
        {/* Both faces share one grid cell and the hidden one keeps its room,
            so the button is as wide as the wider of the two either way: the
            note neither pushes the toolbar along (beside the button) nor
            covers the row under it (hung below). */}
        <span className="menu-face" data-note={note ? "" : undefined}>
          <span className="menu-face-label">{label} ▾</span>
          <span className="menu-face-note" aria-hidden="true">
            {note}
          </span>
        </span>
      </button>
      {/* always mounted: a live region only announces changes to itself */}
      <span className="menu-note" role="status">
        {note}
      </span>
      {open ? (
        <div className={alignEnd ? "menu-body menu-body-end" : "menu-body"} ref={body}>
          {children}
        </div>
      ) : null}
    </div>
  );
}
