import { rangeNameFor, rangeRow, resolveDamageStr } from "@/lib/character/sheet-format";

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

describe("resolveDamageStr", () => {
  it("resolves ({STR}+n)P against a Strength", () => {
    expect(resolveDamageStr("({STR}+1)P", 3)).toBe("4P");
    expect(resolveDamageStr("({STR})P", 3)).toBe("3P");
    expect(resolveDamageStr("({STR}-1)S", 5)).toBe("4S");
  });
  it("passes non-{STR} damage codes through", () => {
    expect(resolveDamageStr("8P", 3)).toBe("8P");
    expect(resolveDamageStr("Grenade", 3)).toBe("Grenade");
    expect(resolveDamageStr(undefined, 3)).toBe("");
  });
  it("folds a throwstr bonus in via the caller's Strength", () => {
    expect(resolveDamageStr("({STR}+1)P", 3 + 1)).toBe("5P"); // Missile Mastery: STR 3, throw_str 1
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
