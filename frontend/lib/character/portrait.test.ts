import { describe, expect, it } from "vitest";

import { portraitsOf, portraitsPatch } from "./portrait";

describe("portraits", () => {
  it("lists the main one first and skips an empty main one", () => {
    expect(portraitsOf({ portrait: "a", extra_portraits: ["b", "c"] })).toEqual(["a", "b", "c"]);
    expect(portraitsOf({ portrait: "", extra_portraits: ["b"] })).toEqual(["b"]);
  });

  it("moves the next one up when the main one is taken away, and keeps three", () => {
    expect(portraitsPatch(["b", "c"])).toEqual({ portrait: "b", extra_portraits: ["c"] });
    expect(portraitsPatch([])).toEqual({ portrait: "", extra_portraits: [] });
    expect(portraitsPatch(["a", "b", "c", "d"]).extra_portraits).toEqual(["b", "c"]);
  });
});
