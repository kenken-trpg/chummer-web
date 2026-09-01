import { renderHook } from "@testing-library/react";
import { useKeyboardShortcuts } from "@/lib/character/useKeyboardShortcuts";

function key(init: KeyboardEventInit) {
  window.dispatchEvent(new KeyboardEvent("keydown", { ...init, bubbles: true }));
}

describe("useKeyboardShortcuts", () => {
  afterEach(() => {
    document.body.innerHTML = "";
  });

  it("⌘Z runs undo, not redo", () => {
    const undo = vi.fn();
    const redo = vi.fn();
    renderHook(() => useKeyboardShortcuts(undo, redo));
    key({ key: "z", metaKey: true });
    expect(undo).toHaveBeenCalledTimes(1);
    expect(redo).not.toHaveBeenCalled();
  });

  it("⌘⇧Z and ⌘Y run redo", () => {
    const undo = vi.fn();
    const redo = vi.fn();
    renderHook(() => useKeyboardShortcuts(undo, redo));
    key({ key: "z", metaKey: true, shiftKey: true });
    key({ key: "y", ctrlKey: true });
    expect(redo).toHaveBeenCalledTimes(2);
    expect(undo).not.toHaveBeenCalled();
  });

  it("does nothing without a modifier or with Alt held", () => {
    const undo = vi.fn();
    renderHook(() => useKeyboardShortcuts(undo, vi.fn()));
    key({ key: "z" });
    key({ key: "z", metaKey: true, altKey: true });
    expect(undo).not.toHaveBeenCalled();
  });

  it("ignores the shortcut while an input is focused", () => {
    const undo = vi.fn();
    renderHook(() => useKeyboardShortcuts(undo, vi.fn()));
    const input = document.createElement("input");
    document.body.appendChild(input);
    input.focus();
    key({ key: "z", metaKey: true });
    expect(undo).not.toHaveBeenCalled();
  });

  it("uses the latest callbacks after a re-render", () => {
    const first = vi.fn();
    const second = vi.fn();
    const { rerender } = renderHook(({ u }) => useKeyboardShortcuts(u, vi.fn()), {
      initialProps: { u: first },
    });
    rerender({ u: second });
    key({ key: "z", metaKey: true });
    expect(first).not.toHaveBeenCalled();
    expect(second).toHaveBeenCalledTimes(1);
  });
});
