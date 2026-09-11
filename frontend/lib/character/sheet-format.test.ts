import { rangeNameFor, rangeRow } from "@/lib/character/sheet-format";

const pistolBands = { min: "0", short: "5", medium: "15", long: "30", extreme: "50" };

describe("rangeRow", () => {
  it("builds low–high band strings from a fixed-value table", () => {
    expect(rangeRow(pistolBands, 3)).toEqual(["0–5", "6–15", "16–30", "31–50"]);
  });

  it("evaluates {STR}-scaled formulas", () => {
    const bow = {
      min: "0",
      short: "{STR}*10",
      medium: "{STR}*20",
      long: "{STR}*30",
      extreme: "{STR}*40",
    };
    expect(rangeRow(bow, 5)).toEqual(["0–50", "51–100", "101–150", "151–200"]);
  });

  it("renders a missing (-1) band as a dash", () => {
    expect(rangeRow({ ...pistolBands, extreme: "-1" }, 3)).toEqual(["0–5", "6–15", "16–30", "–"]);
  });
});

describe("rangeNameFor", () => {
  it("prefers an explicit range", () => {
    expect(rangeNameFor({ range: "Pistols", category: "Heavy Pistols" })).toBe("Pistols");
  });
  it("aliases machine-gun categories", () => {
    expect(rangeNameFor({ category: "Heavy Machine Guns" })).toBe("Medium/Heavy Machinegun");
  });
  it("falls back to the raw category", () => {
    expect(rangeNameFor({ category: "Bows" })).toBe("Bows");
  });
});
