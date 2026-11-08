import { useEffect, useEffectEvent } from "react";
import type { SheetSearchRequest } from "./sheet-search";
import type { Tab } from "./constants";

/** A lazy tab may mount after the navigation render; wait for its actual row. */
export function useSheetSearchNavigation(
  request: SheetSearchRequest | null,
  tab: Tab,
  characterId: string | undefined,
  onMissing: () => void,
) {
  const missing = useEffectEvent(onMissing);
  useEffect(() => {
    if (!request || request.characterId !== characterId || request.target.tab !== tab) return;
    const root = document.getElementById("character-panels");
    if (!root) return;
    let highlighted: HTMLElement | null = null;
    let finished = false;
    const observer = new MutationObserver(() => find());
    const timeout = setTimeout(() => {
      observer.disconnect();
      if (!finished) missing();
    }, 10_000);
    let clearHighlight: ReturnType<typeof setTimeout> | undefined;
    function find() {
      const marker = Array.from(root!.querySelectorAll<HTMLElement>("[data-sheet-search]")).find(
        (el) => el.dataset.sheetSearch === request!.target.key,
      );
      if (!marker) return;
      finished = true;
      observer.disconnect();
      clearTimeout(timeout);
      for (let el: HTMLElement | null = marker; el && root!.contains(el); el = el.parentElement) {
        if (el instanceof HTMLDetailsElement) el.open = true;
      }
      for (const details of marker.querySelectorAll<HTMLDetailsElement>("details.row-notes")) {
        if (details.dataset.sheetSearch === request!.target.key) details.open = true;
      }
      highlighted = marker.classList.contains("row-notes")
        ? (marker.parentElement ?? marker)
        : marker;
      highlighted.dataset.searchHighlight = "true";
      highlighted.tabIndex = -1;
      highlighted.scrollIntoView({ block: "center", behavior: "smooth" });
      highlighted.focus({ preventScroll: true });
      clearHighlight = setTimeout(() => {
        highlighted?.removeAttribute("data-search-highlight");
      }, 5000);
    }
    observer.observe(root, { childList: true, subtree: true });
    find();
    return () => {
      observer.disconnect();
      clearTimeout(timeout);
      clearTimeout(clearHighlight);
      highlighted?.removeAttribute("data-search-highlight");
    };
  }, [request, tab, characterId]);
}
