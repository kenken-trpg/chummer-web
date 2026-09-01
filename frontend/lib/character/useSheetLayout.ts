import { useState } from "react";
import type { SheetLayout } from "@/lib/character/sheet-data";

/** `sheetLayout` persisted to localStorage; a missing / bogus value -> "standard". */
export function useSheetLayout(): [SheetLayout, (v: SheetLayout) => void] {
  const [layout, setLayout] = useState<SheetLayout>(() => {
    try {
      const v = localStorage.getItem("sheetLayout");
      return v === "compact" || v === "text" ? v : "standard";
    } catch {
      return "standard";
    }
  });

  const set = (v: SheetLayout) => {
    setLayout(v);
    try {
      localStorage.setItem("sheetLayout", v);
    } catch {
      /* private mode / storage disabled — the in-memory value still applies */
    }
  };

  return [layout, set];
}
