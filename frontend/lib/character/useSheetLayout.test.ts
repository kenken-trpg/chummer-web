import { act, renderHook } from "@testing-library/react";
import { useSheetLayout } from "@/lib/character/useSheetLayout";

describe("useSheetLayout", () => {
  beforeEach(() => localStorage.clear());

  it("defaults to standard when nothing is stored", () => {
    const { result } = renderHook(() => useSheetLayout());
    expect(result.current[0]).toBe("standard");
  });

  it("reads a valid stored value", () => {
    localStorage.setItem("sheetLayout", "compact");
    const { result } = renderHook(() => useSheetLayout());
    expect(result.current[0]).toBe("compact");
  });

  it("falls back to standard for a bogus stored value", () => {
    localStorage.setItem("sheetLayout", "nonsense");
    const { result } = renderHook(() => useSheetLayout());
    expect(result.current[0]).toBe("standard");
  });

  it("writes through to localStorage when set", () => {
    const { result } = renderHook(() => useSheetLayout());
    act(() => result.current[1]("text"));
    expect(result.current[0]).toBe("text");
    expect(localStorage.getItem("sheetLayout")).toBe("text");
  });
});
