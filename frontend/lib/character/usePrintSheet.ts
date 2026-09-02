import { useCallback, useEffect, useRef } from "react";
import type { SheetLayout } from "@/lib/character/sheet-data";

/** One-click "印刷 / PDF": switch the sheet to the `print` layout, let it
 * paint, call `window.print()`, then restore whatever layout was active
 * before (unless the user was already on `print`, in which case there is
 * nothing to restore). */
export function usePrintSheet(sheetLayout: SheetLayout, setSheetLayout: (v: SheetLayout) => void) {
  // layout to go back to once the print dialog closes; null = not printing
  const restoreTo = useRef<SheetLayout | null>(null);

  useEffect(() => {
    if (restoreTo.current === null || sheetLayout !== "print") return;

    let done = false;
    const restore = () => {
      if (done) return;
      done = true;
      window.removeEventListener("afterprint", restore);
      const back = restoreTo.current;
      restoreTo.current = null;
      if (back && back !== "print") setSheetLayout(back);
    };

    window.addEventListener("afterprint", restore);
    // two frames so the print layout is fully laid out before the dialog opens
    const raf = requestAnimationFrame(() =>
      requestAnimationFrame(() => {
        window.print();
        // Safari fires no reliable `afterprint`; fall back to a timer.
        window.setTimeout(restore, 0);
      }),
    );

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("afterprint", restore);
    };
  }, [sheetLayout, setSheetLayout]);

  return useCallback(() => {
    if (sheetLayout === "print") {
      window.print();
      return;
    }
    restoreTo.current = sheetLayout;
    setSheetLayout("print");
  }, [sheetLayout, setSheetLayout]);
}
