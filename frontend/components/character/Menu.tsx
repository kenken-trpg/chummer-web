import { useEffect, useRef, useState, type ReactNode } from "react";

/**
 * A button that drops a column of other buttons under it.
 *
 * Open state is React's rather than `<details>`'s: the toolbar's own tests and
 * the e2e suite click the items inside, and a native `<summary>` toggle is not
 * something every DOM implementation we test against performs.
 */
export function Menu({
  label,
  title,
  children,
}: {
  label: string;
  title?: string;
  children: ReactNode;
}) {
  const [open, setOpen] = useState(false);
  const box = useRef<HTMLDivElement>(null);
  const body = useRef<HTMLDivElement>(null);

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
      if (body.current?.contains(el) && el.closest("button")) setOpen(false);
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
      <button className="btn" title={title} aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        {label} ▾
      </button>
      {open ? (
        <div className="menu-body" ref={body}>
          {children}
        </div>
      ) : null}
    </div>
  );
}
