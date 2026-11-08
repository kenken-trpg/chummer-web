import { act, renderHook } from "@testing-library/react";
import { useSheetSearchNavigation } from "./useSheetSearchNavigation";
import type { SheetSearchRequest } from "./sheet-search";

const request: SheetSearchRequest = {
  characterId: "c",
  serial: 1,
  target: { key: "gear/a", tab: "gear", gearKind: "misc" },
};
afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
  document.getElementById("character-panels")?.remove();
});
function root() {
  const el = document.createElement("div");
  el.id = "character-panels";
  document.body.append(el);
  return el;
}

it("waits for lazy content, opens folded details and focuses the matching row", async () => {
  const container = root();
  const missing = vi.fn();
  renderHook(() => useSheetSearchNavigation(request, "gear", "c", missing));
  const outer = document.createElement("details");
  const row = document.createElement("div");
  row.dataset.sheetSearch = "gear/a";
  const scroll = vi.fn();
  row.scrollIntoView = scroll;
  const notes = document.createElement("details");
  notes.className = "row-notes";
  notes.dataset.sheetSearch = "gear/a";
  row.append(notes);
  outer.append(row);
  await act(async () => {
    container.append(outer);
  });
  expect(outer.open).toBe(true);
  expect(notes.open).toBe(true);
  expect(row.dataset.searchHighlight).toBe("true");
  expect(document.activeElement).toBe(row);
  expect(scroll).toHaveBeenCalledOnce();
  expect(missing).not.toHaveBeenCalled();
});

it("reports a missing destination and cancels stale navigation on a character switch", () => {
  vi.useFakeTimers();
  root();
  const missing = vi.fn();
  const { rerender } = renderHook(
    ({ id }) => useSheetSearchNavigation(request, "gear", id, missing),
    { initialProps: { id: "c" } },
  );
  rerender({ id: "other" });
  act(() => vi.advanceTimersByTime(10_000));
  expect(missing).not.toHaveBeenCalled();
  rerender({ id: "c" });
  act(() => vi.advanceTimersByTime(10_000));
  expect(missing).toHaveBeenCalledOnce();
});
