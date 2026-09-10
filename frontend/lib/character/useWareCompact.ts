import { useState } from "react";

const KEY = "wareCompact";

/**
 * Whether the installed cyberware / bioware rows show only their names,
 * persisted to localStorage the same way {@link useSheetLayout} is. One value
 * for both tabs: someone who wants the long list folded wants it everywhere.
 */
export function useWareCompact(): [boolean, (v: boolean) => void] {
  const [compact, setCompact] = useState<boolean>(() => {
    try {
      return localStorage.getItem(KEY) === "1";
    } catch {
      return false;
    }
  });

  const set = (v: boolean) => {
    setCompact(v);
    try {
      localStorage.setItem(KEY, v ? "1" : "0");
    } catch {
      /* private mode / storage disabled — the in-memory value still applies */
    }
  };

  return [compact, set];
}
