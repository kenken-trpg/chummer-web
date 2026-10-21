import { describe, expect, it } from "vitest";
import { advancesOneLeaf, disjointKeys } from "@/lib/character/patch-queue";

/** `AttrsTab` builds this: the whole map, spread from the character it saw. */
const attrs = (over: Record<string, number>) => ({
  attributes: { BOD: 3, AGI: 2, REA: 2, STR: 1, ...over },
});

/** `AdeptTab` / `ComplexFormsTab` build this: the whole list, one row changed. */
const powers = (rows: { id: string; rating: number }[]) => ({ adept_powers: rows });

/** A saved character carrying no list the bodies below touch. */
const saved = attrs({});

/** Two powers, as saved: what the row edits below were composed against. */
const twoPowers = powers([
  { id: "a", rating: 1 },
  { id: "b", rating: 2 },
]);

describe("advancesOneLeaf", () => {
  it("holds a number input being worked — one value, one step on", () => {
    expect(advancesOneLeaf(attrs({ BOD: 3 }), attrs({ BOD: 4 }), saved)).toBe(true);
  });

  it("holds a repeat of the same value", () => {
    expect(advancesOneLeaf(attrs({ BOD: 3 }), attrs({ BOD: 3 }), saved)).toBe(true);
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
        twoPowers,
      ),
    ).toBe(true);
  });

  it("holds a dropdown in a list picked twice — the list stays as long as saved", () => {
    expect(
      advancesOneLeaf(
        { talent_skills: ["Hacking", "Computer"] },
        { talent_skills: ["Cybercombat", "Computer"] },
        { talent_skills: ["Electronic Warfare", "Computer"] },
      ),
    ).toBe(true);
  });

  // The cases below are the ones a queue must refuse. Both bodies were built
  // from the same character, so sending the later one after the earlier has
  // landed would put the earlier one's field back.
  it("refuses two different fields — the second would undo the first", () => {
    expect(advancesOneLeaf(attrs({ BOD: 4 }), attrs({ AGI: 5 }), saved)).toBe(false);
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
        powers([
          { id: "a", rating: 1 },
          { id: "b", rating: 1 },
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
        powers([{ id: "a", rating: 1 }]),
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
        twoPowers,
      ),
    ).toBe(false);
  });

  it("refuses two adds to the same saved list — the second would drop the first", () => {
    // Ticking two rulebooks quickly: each body is the saved list plus one,
    // so they differ in one element, but the second has no RF in it.
    expect(
      advancesOneLeaf(
        { settings: { name: "", books: ["SR5", "RF"] } },
        { settings: { name: "", books: ["SR5", "DTR"] } },
        { settings: { name: "", books: ["SR5"] } },
      ),
    ).toBe(false);
  });

  it("refuses two different rows added, even when they differ in one field", () => {
    expect(
      advancesOneLeaf(
        { qualities: [{ quality_id: "x" }, { quality_id: "a" }] },
        { qualities: [{ quality_id: "x" }, { quality_id: "b" }] },
        { qualities: [{ quality_id: "x" }] },
      ),
    ).toBe(false);
  });

  it("refuses the first add to a list the character has not saved yet", () => {
    expect(advancesOneLeaf({ techniques: ["a"] }, { techniques: ["b"] }, {})).toBe(false);
  });

  it("refuses two different top-level fields", () => {
    expect(advancesOneLeaf({ name: "A" }, { notes: "B" }, saved)).toBe(false);
  });

  it("refuses a key one side does not have", () => {
    expect(
      advancesOneLeaf({ settings: { name: "x" } }, { settings: { name: "x", books: [] } }, saved),
    ).toBe(false);
  });

  it("refuses a value that changed kind", () => {
    expect(
      advancesOneLeaf({ quality_extras: { a: "x" } }, { quality_extras: { a: ["x"] } }, saved),
    ).toBe(false);
  });

  it("counts a nested change as its one leaf", () => {
    expect(
      advancesOneLeaf(
        { quality_extras: { "q1:power": "A", "q2:power": "B" } },
        { quality_extras: { "q1:power": "A", "q2:power": "C" } },
        saved,
      ),
    ).toBe(true);
  });

  it("refuses two nested changes at once", () => {
    expect(
      advancesOneLeaf(
        { quality_extras: { "q1:power": "A", "q2:power": "B" } },
        { quality_extras: { "q1:power": "X", "q2:power": "C" } },
        saved,
      ),
    ).toBe(false);
  });
});

describe("disjointKeys", () => {
  it("lets a career switch wait behind a rename", () => {
    expect(disjointKeys({ name: "Careerist" }, { career: true })).toBe(true);
  });

  it("refuses two bodies that both carry the same block", () => {
    // each was built from the whole block, so the later one puts the rest back
    expect(disjointKeys({ attributes: { BOD: 4 } }, { attributes: { AGI: 5 } })).toBe(false);
  });

  it("refuses a body that only repeats a field", () => {
    expect(disjointKeys({ name: "A" }, { name: "B" })).toBe(false);
  });

  it("counts a key the other side set to undefined as named", () => {
    expect(disjointKeys({ career: undefined }, { career: true })).toBe(false);
  });

  it("refuses an empty body, which has nothing to wait for", () => {
    expect(disjointKeys({ name: "A" }, {})).toBe(false);
  });
});
