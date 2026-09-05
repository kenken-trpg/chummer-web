import { testUi } from "@/tests/fixtures";
import { translate, type UiFn } from "@/lib/i18n";
import {
  availBit,
  cfDuration,
  cfTarget,
  kindLabel,
  limitModifierLine,
  specialArmorLine,
  lifeIncrement,
  specialArmorBits,
  formatAccessoryCost,
  formatAmmoCost,
  formatPoints,
  leadInt,
  matrixCM,
  mergeRatings,
  mergeSpecialArmor,
  optionalNumber,
  deviceRatingBit,
  poolRating,
  skillDice,
  testLine,
  vehicleCM,
  wareAttrLine,
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
    expect(cfDuration("P", testUi)).toBe("永続");
    expect(cfDuration("S", testUi)).toBe("維持");
    expect(cfDuration("I", testUi)).toBe("瞬間");
    expect(cfDuration("weird", testUi)).toBe("weird");
  });
  it("maps known targets, passes unknown through", () => {
    expect(cfTarget("Persona", testUi)).toBe("ペルソナ");
    expect(cfTarget("Whatever", testUi)).toBe("Whatever");
    expect(cfTarget(undefined, testUi)).toBe("");
  });
});

describe("formatAccessoryCost / formatAmmoCost", () => {
  it("resolves 'Weapon Cost' against the parent", () => {
    expect(formatAccessoryCost("Weapon Cost", "2000")).toBe("2,000¥");
    expect(formatAccessoryCost("150")).toBe("150¥");
  });
  it("appends the per-N-rounds divisor", () => {
    expect(formatAmmoCost("40", 10, testUi)).toBe("40¥ / 10発");
    expect(formatAmmoCost("40", undefined, testUi)).toBe("40¥");
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
    expect(lifeIncrement("day", testUi)).toBe("日");
    expect(lifeIncrement("month", testUi)).toBe("ヶ月");
    expect(lifeIncrement(undefined, testUi)).toBe("ヶ月");
  });
});

describe("specialArmorBits", () => {
  it("returns [] for no special armor", () => {
    expect(specialArmorBits(null, testUi)).toEqual([]);
    expect(specialArmorBits(undefined, testUi)).toEqual([]);
  });

  it("emits a row per elemental protection", () => {
    expect(specialArmorBits({ fire: 2, cold: 1 }, testUi)).toEqual([
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
      expect(
        specialArmorBits({ [`toxin_${vector}`]: 3, [`pathogen_${vector}`]: 3 }, testUi),
      ).toEqual([{ label, value: "+3" }]);
    }
  });

  it("keeps the two apart when they differ", () => {
    expect(specialArmorBits({ toxin_inhalation: 3, pathogen_inhalation: 1 }, testUi)).toEqual([
      { label: "毒素吸入", value: "+3" },
      { label: "病原吸入", value: "+1" },
    ]);
  });

  it("collapses full contact + inhalation immunity", () => {
    expect(
      specialArmorBits(
        {
          immunities: {
            toxin_contact: true,
            pathogen_contact: true,
            toxin_inhalation: true,
            pathogen_inhalation: true,
          },
        },
        testUi,
      ),
    ).toEqual([{ label: "化学密閉", value: "免疫", immune: true }]);
  });
});

describe("the formatters follow the locale", () => {
  const enUi: UiFn = (key, vars) => translate("en", key, vars);

  it("renders SR5 vocabulary in English", () => {
    expect(cfTarget("Persona", enUi)).toBe("Persona");
    expect(cfDuration("S", enUi)).toBe("Sustained");
    expect(kindLabel("ritual", enUi)).toBe("Ritual");
    expect(lifeIncrement("day", enUi)).toBe("day");
  });

  it("renders composed lines in English", () => {
    expect(specialArmorLine({ fire: 2 }, enUi)).toBe("Fire +2");
    expect(limitModifierLine([{ limit: "physical", value: 1 }], enUi)).toBe("Physical limit +1");
    expect(availBit({ avail: "8R", avail_value: 8 }, enUi)).toBe(" / avail 8R");
  });

  it("leaves a code the rulebook does not define alone in either locale", () => {
    expect(cfTarget("Whatever", enUi)).toBe("Whatever");
    expect(cfTarget("Whatever", testUi)).toBe("Whatever");
  });
});

/**
 * The rest of `format.ts`. These feed both sheets and several tabs, and every
 * one of them turns structured data into a sentence a player reads and acts
 * on — the same silently-wrong class as the exporters. A missing bit reads as
 * "this armour has no chemical protection" rather than as a bug.
 */

describe("optionalNumber", () => {
  it("distinguishes an empty field from a zero the user typed", () => {
    // null means "unset"; 0 is a real value, and conflating them clears a stat
    expect(optionalNumber("")).toBeNull();
    expect(optionalNumber("0")).toBe(0);
  });

  it("rejects anything that is not a finite number", () => {
    for (const bad of ["abc", "1/2", "Infinity", "NaN"]) expect(optionalNumber(bad)).toBeNull();
    expect(optionalNumber("-3")).toBe(-3);
    expect(optionalNumber(" 4 ")).toBe(4);
  });
});

describe("testLine", () => {
  // only the fields testLine reads; the rest of MagicTestInfo is irrelevant here
  const base = { skill: "Spellcasting", pool: 10, limit: 5, drain: 3, drain_code: "S" } as Record<
    string,
    unknown
  >;

  it("reads skill pool [limit] → drain", () => {
    expect(testLine(base as never, testUi)).toBe("Spellcasting 10 [5] → ドレイン 3S");
  });

  it("says the drain is opposed rather than printing a number for it", () => {
    // drain: null is not drain 0 — the opposing roll decides it
    const opposed = testLine({ ...base, drain: null } as never, testUi);
    expect(opposed).toContain("相手ヒット");
    expect(opposed).not.toContain("null");
  });

  it("flags a missing skill, which is the part that changes how you roll", () => {
    expect(testLine({ ...base, missing: true } as never, testUi)).not.toBe(
      testLine(base as never, testUi),
    );
  });

  it("is empty for no test at all", () => {
    expect(testLine(null, testUi)).toBe("");
    expect(testLine(undefined, testUi)).toBe("");
  });
});

describe("specialArmorBits — chemical protection", () => {
  const ui: UiFn = testUi;

  it("collapses equal toxin and pathogen values into one chemical row", () => {
    const rows = specialArmorBits({ toxin_contact: 6, pathogen_contact: 6 } as never, ui);

    expect(rows).toHaveLength(1);
    expect(rows[0].value).toBe("+6");
  });

  it("keeps them apart when they differ, because they are rolled separately", () => {
    const rows = specialArmorBits({ toxin_contact: 6, pathogen_contact: 4 } as never, ui);

    expect(rows.map((r) => r.value)).toEqual(["+6", "+4"]);
  });

  it("calls full contact + inhalation immunity 'sealed', not two immunities", () => {
    const rows = specialArmorBits(
      {
        immunities: {
          toxin_contact: true,
          pathogen_contact: true,
          toxin_inhalation: true,
          pathogen_inhalation: true,
        },
      } as never,
      ui,
    );

    expect(rows).toHaveLength(1);
    expect(rows[0].immune).toBe(true);
  });

  it("needs both toxin and pathogen immunity before claiming a vector is immune", () => {
    const partial = specialArmorBits(
      { immunities: { toxin_contact: true, pathogen_contact: false } } as never,
      ui,
    );

    expect(partial).toEqual([]);
  });
});

describe("specialArmorLine", () => {
  it("drops the value for an immunity — '+0' would read as no protection", () => {
    const line = specialArmorLine(
      {
        fire: 2,
        immunities: {
          toxin_contact: true,
          pathogen_contact: true,
          toxin_inhalation: true,
          pathogen_inhalation: true,
        },
      } as never,
      testUi,
    );

    expect(line).toContain("+2");
    expect(line).not.toContain("+0");
    expect(line.split(" / ")).toHaveLength(2);
  });

  it("is empty rather than a stray separator when there is nothing to say", () => {
    expect(specialArmorLine(null, testUi)).toBe("");
    expect(specialArmorLine({} as never, testUi)).toBe("");
  });
});

describe("mergeSpecialArmor", () => {
  it("adds ratings across mods and ORs the immunities", () => {
    const merged = mergeSpecialArmor([
      { special_armor: { fire: 2, toxin_contact: 1 } as never },
      { special_armor: { fire: 3, immunities: { toxin_contact: true } } as never },
    ]);

    expect(merged?.fire).toBe(5);
    expect(merged?.toxin_contact).toBe(1);
    expect(merged?.immunities?.toxin_contact).toBe(true);
    expect(merged?.immunities?.pathogen_contact).toBe(false);
  });

  it("is undefined when no mod contributes any, so callers can skip the row", () => {
    expect(mergeSpecialArmor([])).toBeUndefined();
    expect(mergeSpecialArmor([{}, { special_armor: undefined }])).toBeUndefined();
  });
});

describe("limitModifierLine", () => {
  it("signs the modifier and names the limit", () => {
    const line = limitModifierLine([{ limit: "physical", value: 1 } as never], testUi);

    expect(line).toContain("+1");
    expect(line).toContain("物理");
  });

  it("keeps a negative sign rather than printing +-1", () => {
    expect(limitModifierLine([{ limit: "mental", value: -2 } as never], testUi)).toContain("-2");
  });

  it("falls back to the raw limit name for one it does not know", () => {
    expect(limitModifierLine([{ limit: "astral", value: 1 } as never], testUi)).toContain("astral");
  });

  it("appends the condition, since a conditional bonus is not always on", () => {
    const line = limitModifierLine(
      [{ limit: "social", value: 2, condition_label: "対メタヒューマン" } as never],
      testUi,
    );

    expect(line).toContain("（対メタヒューマン）");
  });

  it("is empty for none", () => {
    expect(limitModifierLine([], testUi)).toBe("");
    expect(limitModifierLine(null, testUi)).toBe("");
  });
});

describe("small bits", () => {
  it("deviceRatingBit is empty at rating 0, not ' / DR 0'", () => {
    expect(deviceRatingBit({ device_rating: 3 })).toBe(" / DR 3");
    expect(deviceRatingBit({ device_rating: 0 })).toBe("");
    expect(deviceRatingBit(null)).toBe("");
  });

  it("wareAttrLine lists only the attributes actually bonused, in ATTRS order", () => {
    expect(wareAttrLine({ AGI: 2, BOD: 1, REA: 0 })).toBe("BOD +1 / AGI +2");
    expect(wareAttrLine(null)).toBe("");
  });

  it("skillDice signs a bonus and omits it when zero", () => {
    expect(skillDice(4)).toBe("4");
    expect(skillDice(4, 0)).toBe("4");
    expect(skillDice(4, 2)).toBe("4 +2");
    expect(skillDice(4, -1)).toBe("4 -1");
  });

  it("poolRating takes the best of a skill and its specialisations", () => {
    const pool = { Pistols: 8, "Pistols (Semi-Automatics)": 10, Blades: 12 };

    expect(poolRating(pool, "Pistols")).toBe(10);
    expect(poolRating(pool, "Longarms")).toBe(0);
  });

  it("poolRating does not match a different skill that merely starts the same", () => {
    // "Pistol" must not pick up "Pistols (…)": the prefix includes the paren
    expect(poolRating({ "Pistols (Holdouts)": 9 }, "Pistol")).toBe(0);
  });

  it("availBit says nothing for freely available gear", () => {
    expect(availBit({ avail: "8R", avail_value: 8 }, testUi)).toContain("8R");
    expect(availBit({ avail: "0", avail_value: 0 }, testUi)).toBe("");
    expect(availBit({ avail_value: 4 }, testUi)).toBe("");
    expect(availBit(null, testUi)).toBe("");
  });
});
