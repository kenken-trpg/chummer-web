import { useState } from "react";

/**
 * Whether the installed cyberware / bioware rows show only their names,
 * persisted to localStorage the same way {@link useSheetLayout} is. One value
 * for both tabs: someone who wants the long list folded wants it everywhere.
 * Vehicles and drones keep their own key — a garage and a body fold apart.
 */
export function useWareCompact(key = "wareCompact"): [boolean, (v: boolean) => void] {
  const [compact, setCompact] = useState<boolean>(() => {
    try {
      return localStorage.getItem(key) === "1";
    } catch {
      return false;
    }
  });

  const set = (v: boolean) => {
    setCompact(v);
    try {
      localStorage.setItem(key, v ? "1" : "0");
    } catch {
      /* private mode / storage disabled — the in-memory value still applies */
    }
  };

  return [compact, set];
}
