import { useEffect, useRef } from "react";

/** Ctrl/⌘+Z → undo, Ctrl/⌘+Y or +Shift+Z → redo. No-op while an
 * `<input>` / `<textarea>` is focused (the browser's own undo wins there). */
export function useKeyboardShortcuts(undo: () => void, redo: () => void) {
  const undoRef = useRef(undo);
  const redoRef = useRef(redo);
  // Keep the "latest" refs current without touching them during render.
  useEffect(() => {
    undoRef.current = undo;
    redoRef.current = redo;
  });

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (!(e.metaKey || e.ctrlKey) || e.altKey) return;
      const key = e.key.toLowerCase();
      if (key !== "z" && key !== "y") return;
      const el = document.activeElement;
      if (el && (el.tagName === "INPUT" || el.tagName === "TEXTAREA")) return;
      e.preventDefault();
      if (key === "y" || e.shiftKey) redoRef.current();
      else undoRef.current();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);
}
