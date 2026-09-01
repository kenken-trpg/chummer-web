import {
  lifeIncrement,
  rangeNameFor,
  rangeRow,
  specialArmorBits,
} from "@/lib/character/sheet-format";

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

describe("lifeIncrement", () => {
  it("maps day / month", () => {
    expect(lifeIncrement("day")).toBe("日");
    expect(lifeIncrement("month")).toBe("ヶ月");
    expect(lifeIncrement(undefined)).toBe("ヶ月");
  });
});

describe("specialArmorBits", () => {
  it("returns [] for no special armor", () => {
    expect(specialArmorBits(null)).toEqual([]);
    expect(specialArmorBits(undefined)).toEqual([]);
  });
  it("emits a row per elemental protection", () => {
    expect(specialArmorBits({ fire: 2, cold: 1 })).toEqual([
      { label: "耐火", value: "+2" },
      { label: "断熱", value: "+1" },
    ]);
  });
  it("combines equal toxin/pathogen contact protection", () => {
    expect(specialArmorBits({ toxin_contact: 3, pathogen_contact: 3 })).toEqual([
      { label: "化学防護(接触)", value: "+3" },
    ]);
  });
  it("collapses full contact + inhalation immunity", () => {
    expect(
      specialArmorBits({
        immunities: {
          toxin_contact: true,
          pathogen_contact: true,
          toxin_inhalation: true,
          pathogen_inhalation: true,
        },
      }),
    ).toEqual([{ label: "化学密閉", value: "免疫" }]);
  });
});
