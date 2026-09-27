// @vitest-environment jsdom
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { PendingGear } from "@/lib/api";
import {
  clearPendingGear,
  loadPendingGear,
  savePendingGear,
} from "@/lib/character/pending-gear-store";

const row = (name: string): PendingGear => ({
  name,
  rating: 0,
  qty: 1,
  note: "",
  suggestions: [],
});

describe("pending-gear-store", () => {
  beforeEach(() => localStorage.clear());

  it("has nothing for a character nothing was imported for", () => {
    expect(loadPendingGear("c1")).toEqual([]);
  });

  it("keeps a character's rows and hands them back", () => {
    savePendingGear("c1", [row("FN-HAL")]);
    expect(loadPendingGear("c1")).toEqual([row("FN-HAL")]);
  });

  it("keeps each character's rows apart", () => {
    savePendingGear("c1", [row("FN-HAL")]);
    savePendingGear("c2", [row("現代-シンヒュン")]);
    expect(loadPendingGear("c1").map((r) => r.name)).toEqual(["FN-HAL"]);
    expect(loadPendingGear("c2").map((r) => r.name)).toEqual(["現代-シンヒュン"]);
  });

  it("replaces a character's rows rather than adding to them", () => {
    savePendingGear("c1", [row("FN-HAL"), row("錠前キット")]);
    savePendingGear("c1", [row("錠前キット")]);
    expect(loadPendingGear("c1").map((r) => r.name)).toEqual(["錠前キット"]);
  });

  it("forgets a character once its last row is settled", () => {
    savePendingGear("c1", [row("FN-HAL")]);
    savePendingGear("c1", []);
    expect(loadPendingGear("c1")).toEqual([]);
    expect(localStorage.getItem("pendingGear")).toBe("{}");
  });

  it("forgets a character on request", () => {
    savePendingGear("c1", [row("FN-HAL")]);
    clearPendingGear("c1");
    expect(loadPendingGear("c1")).toEqual([]);
  });

  it("drops the character imported longest ago past the cap", () => {
    for (let i = 0; i < 12; i++) savePendingGear(`c${i}`, [row(`item${i}`)]);
    // the newest is kept, the first ones are not
    expect(loadPendingGear("c11")).toHaveLength(1);
    expect(loadPendingGear("c0")).toEqual([]);
    expect(Object.keys(JSON.parse(localStorage.getItem("pendingGear") ?? "{}"))).toHaveLength(10);
  });

  it("survives a store written by something else", () => {
    localStorage.setItem("pendingGear", "not json at all");
    expect(loadPendingGear("c1")).toEqual([]);
    localStorage.setItem("pendingGear", JSON.stringify(["an array, not a map"]));
    expect(loadPendingGear("c1")).toEqual([]);
  });

  it("keeps the rows that still look like rows", () => {
    // hand-edited, or written by an older version: one good row among junk is
    // worth more than throwing the character's whole list away
    localStorage.setItem(
      "pendingGear",
      JSON.stringify({ c1: [row("FN-HAL"), { name: "no suggestions key" }, null, 7] }),
    );
    expect(loadPendingGear("c1").map((r) => r.name)).toEqual(["FN-HAL"]);
  });

  it("costs the reminder and not the import when the store refuses", () => {
    const setItem = vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new Error("QuotaExceededError");
    });
    expect(() => savePendingGear("c1", [row("FN-HAL")])).not.toThrow();
    setItem.mockRestore();
  });
});
