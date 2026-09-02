import { act, renderHook } from "@testing-library/react";
import { useCharacterHistory } from "@/lib/character/history";
import type { Character } from "@/lib/types";

/* eslint-disable @typescript-eslint/no-explicit-any */

// Snapshots are opaque to the stack — a tagged stub is enough.
const snap = (tag: string) => ({ id: tag }) as unknown as Character;

describe("useCharacterHistory", () => {
  it("starts empty", () => {
    const { result } = renderHook(() => useCharacterHistory());
    expect(result.current.counts).toEqual({ undo: 0, redo: 0 });
    expect(result.current.stepBack(snap("now"))).toBeNull();
    expect(result.current.stepForward(snap("now"))).toBeNull();
  });

  it("record → stepBack → stepForward round-trips the snapshot and the counts", () => {
    const { result } = renderHook(() => useCharacterHistory());

    act(() => result.current.record(snap("v1")));
    expect(result.current.counts).toEqual({ undo: 1, redo: 0 });

    let restored: Character | null = null;
    act(() => {
      restored = result.current.stepBack(snap("v2"));
    });
    expect((restored as any).id).toBe("v1");
    expect(result.current.counts).toEqual({ undo: 0, redo: 1 });

    let forward: Character | null = null;
    act(() => {
      forward = result.current.stepForward(snap("v1"));
    });
    expect((forward as any).id).toBe("v2");
    expect(result.current.counts).toEqual({ undo: 1, redo: 0 });
  });

  it("record clears the redo stack (a new edit forks history)", () => {
    const { result } = renderHook(() => useCharacterHistory());
    act(() => result.current.record(snap("v1")));
    act(() => {
      result.current.stepBack(snap("v2"));
    });
    expect(result.current.counts).toEqual({ undo: 0, redo: 1 });

    act(() => result.current.record(snap("v1")));
    expect(result.current.counts).toEqual({ undo: 1, redo: 0 });
    // redo is gone: stepForward yields nothing
    act(() => {
      expect(result.current.stepForward(snap("v1b"))).toBeNull();
    });
  });

  it("caps the undo stack at 50 (drops the oldest)", () => {
    const { result } = renderHook(() => useCharacterHistory());
    act(() => {
      for (let i = 0; i < 55; i++) result.current.record(snap(`v${i}`));
    });
    expect(result.current.counts.undo).toBe(50);
    // walking all the way back lands on v5, not v0
    let last: Character | null = null;
    act(() => {
      for (let i = 0; i < 50; i++) last = result.current.stepBack(snap("cur"));
    });
    expect((last as any).id).toBe("v5");
  });

  it("reset drops both stacks", () => {
    const { result } = renderHook(() => useCharacterHistory());
    act(() => {
      result.current.record(snap("v1"));
      result.current.record(snap("v2"));
    });
    act(() => {
      result.current.stepBack(snap("cur"));
    });
    expect(result.current.counts).toEqual({ undo: 1, redo: 1 });
    act(() => result.current.reset());
    expect(result.current.counts).toEqual({ undo: 0, redo: 0 });
  });
});
