import { describe, expect, it } from "vitest";
import { advancesOneLeaf } from "@/lib/character/patch-queue";

/** `AttrsTab` builds this: the whole map, spread from the character it saw. */
const attrs = (over: Record<string, number>) => ({
  attributes: { BOD: 3, AGI: 2, REA: 2, STR: 1, ...over },
});

/** `AdeptTab` / `ComplexFormsTab` build this: the whole list, one row changed. */
const powers = (rows: { id: string; rating: number }[]) => ({ adept_powers: rows });

describe("advancesOneLeaf", () => {
  it("holds a number input being worked — one value, one step on", () => {
    expect(advancesOneLeaf(attrs({ BOD: 3 }), attrs({ BOD: 4 }))).toBe(true);
  });

  it("holds a repeat of the same value", () => {
    expect(advancesOneLeaf(attrs({ BOD: 3 }), attrs({ BOD: 3 }))).toBe(true);
  });

  it("holds a row's rating being worked, in a list", () => {
    expect(
      advancesOneLeaf(
        powers([
          { id: "a", rating: 1 },
          { id: "b", rating: 2 },
        ]),
        powers([
          { id: "a", rating: 1 },
          { id: "b", rating: 3 },
        ]),
      ),
    ).toBe(true);
  });

  // The cases below are the ones a queue must refuse. Both bodies were built
  // from the same character, so sending the later one after the earlier has
  // landed would put the earlier one's field back.
  it("refuses two different fields — the second would undo the first", () => {
    expect(advancesOneLeaf(attrs({ BOD: 4 }), attrs({ AGI: 5 }))).toBe(false);
  });

  it("refuses two different rows of one list", () => {
    expect(
      advancesOneLeaf(
        powers([
          { id: "a", rating: 2 },
          { id: "b", rating: 1 },
        ]),
        powers([
          { id: "a", rating: 1 },
          { id: "b", rating: 2 },
        ]),
      ),
    ).toBe(false);
  });

  it("refuses a row added — a different edit, not the same one further on", () => {
    expect(
      advancesOneLeaf(
        powers([{ id: "a", rating: 1 }]),
        powers([
          { id: "a", rating: 1 },
          { id: "b", rating: 1 },
        ]),
      ),
    ).toBe(false);
  });

  it("refuses a row removed", () => {
    expect(
      advancesOneLeaf(
        powers([
          { id: "a", rating: 1 },
          { id: "b", rating: 1 },
        ]),
        powers([{ id: "a", rating: 1 }]),
      ),
    ).toBe(false);
  });

  it("refuses two different top-level fields", () => {
    expect(advancesOneLeaf({ name: "A" }, { notes: "B" })).toBe(false);
  });

  it("refuses a key one side does not have", () => {
    expect(
      advancesOneLeaf({ settings: { name: "x" } }, { settings: { name: "x", books: [] } }),
    ).toBe(false);
  });

  it("refuses a value that changed kind", () => {
    expect(advancesOneLeaf({ quality_extras: { a: "x" } }, { quality_extras: { a: ["x"] } })).toBe(
      false,
    );
  });

  it("counts a nested change as its one leaf", () => {
    expect(
      advancesOneLeaf(
        { quality_extras: { "q1:power": "A", "q2:power": "B" } },
        { quality_extras: { "q1:power": "A", "q2:power": "C" } },
      ),
    ).toBe(true);
  });

  it("refuses two nested changes at once", () => {
    expect(
      advancesOneLeaf(
        { quality_extras: { "q1:power": "A", "q2:power": "B" } },
        { quality_extras: { "q1:power": "X", "q2:power": "C" } },
      ),
    ).toBe(false);
  });
});
