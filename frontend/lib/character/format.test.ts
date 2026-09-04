import {
  cfDuration,
  cfTarget,
  lifeIncrement,
  specialArmorBits,
  formatAccessoryCost,
  formatAmmoCost,
  formatPoints,
  leadInt,
  matrixCM,
  mergeRatings,
  vehicleCM,
} from "@/lib/character/format";

describe("matrixCM / vehicleCM", () => {
  it("matrix CM = 8 + ceil(DR/2)", () => {
    expect(matrixCM(0)).toBe(8);
    expect(matrixCM(3)).toBe(10);
    expect(matrixCM(6)).toBe(11);
    expect(matrixCM(undefined)).toBe(8);
  });
  it("vehicle CM = 12 + ceil(Body/2), Body read as a leading int", () => {
    expect(vehicleCM(0)).toBe(12);
    expect(vehicleCM(9)).toBe(17);
    expect(vehicleCM("H12/3")).toBe(18);
  });
});

describe("leadInt", () => {
  it("pulls the first (signed) integer", () => {
    expect(leadInt("12")).toBe(12);
    expect(leadInt("H4/3")).toBe(4);
    expect(leadInt("-2")).toBe(-2);
    expect(leadInt(null)).toBe(0);
  });
});

describe("formatPoints", () => {
  it("rounds to 2dp and stringifies", () => {
    expect(formatPoints(0.25)).toBe("0.25");
    expect(formatPoints(1)).toBe("1");
    expect(formatPoints(0.333333)).toBe("0.33");
  });
});

describe("cfDuration / cfTarget", () => {
  it("maps complex-form duration codes", () => {
    expect(cfDuration("P")).toBe("永続");
    expect(cfDuration("S")).toBe("維持");
    expect(cfDuration("I")).toBe("瞬間");
    expect(cfDuration("weird")).toBe("weird");
  });
  it("maps known targets, passes unknown through", () => {
    expect(cfTarget("Persona")).toBe("ペルソナ");
    expect(cfTarget("Whatever")).toBe("Whatever");
    expect(cfTarget(undefined)).toBe("");
  });
});

describe("formatAccessoryCost / formatAmmoCost", () => {
  it("resolves 'Weapon Cost' against the parent", () => {
    expect(formatAccessoryCost("Weapon Cost", "2000")).toBe("2,000¥");
    expect(formatAccessoryCost("150")).toBe("150¥");
  });
  it("appends the per-N-rounds divisor", () => {
    expect(formatAmmoCost("40", 10)).toBe("40¥ / 10発");
    expect(formatAmmoCost("40")).toBe("40¥");
  });
});

describe("mergeRatings", () => {
  it("takes the max per skill across the two maps", () => {
    expect(mergeRatings({ Pistols: 4, Blades: 2 }, { Pistols: 3, Clubs: 5 })).toEqual({
      Pistols: 4,
      Blades: 2,
      Clubs: 5,
    });
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

  it("collapses an equal toxin/pathogen pair on every vector, not just contact", () => {
    // sheet-format.ts carried a second copy that only collapsed contact, so an
    // armor with matched inhalation protection read differently on the sheet
    // than in the gear tab. One implementation now, and this pins the richer
    // behaviour on all four.
    for (const [vector, label] of [
      ["contact", "化学防護(接触)"],
      ["inhalation", "化学防護(吸入)"],
      ["ingestion", "化学防護(摂取)"],
      ["injection", "化学防護(注射)"],
    ] as const) {
      expect(specialArmorBits({ [`toxin_${vector}`]: 3, [`pathogen_${vector}`]: 3 })).toEqual([
        { label, value: "+3" },
      ]);
    }
  });

  it("keeps the two apart when they differ", () => {
    expect(specialArmorBits({ toxin_inhalation: 3, pathogen_inhalation: 1 })).toEqual([
      { label: "毒素吸入", value: "+3" },
      { label: "病原吸入", value: "+1" },
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
