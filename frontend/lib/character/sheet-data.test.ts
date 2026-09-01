import { buildSheetData } from "@/lib/character/sheet-data";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

describe("buildSheetData", () => {
  it("splits the gear list into misc / drugs / sins, skipping children", () => {
    const gear: any[] = [
      { id: "g1", name: "Rope" },
      { id: "d1", name: "Novacoke", category: "Drugs" },
      { id: "s1", name: "Fake SIN", category: "ID/Credsticks" },
      { id: "g1c", name: "Attachment", parent_id: "g1" },
    ];
    const s = buildSheetData({
      character: makeCharacter({ derived: { gear } }),
      catalog: makeCatalog(),
      tr: identityTr,
      layout: "standard",
    });
    expect(s.gearMisc.map((g) => g.id)).toEqual(["g1"]);
    expect(s.drugs.map((g) => g.id)).toEqual(["d1"]);
    expect(s.sins.map((g) => g.id)).toEqual(["s1"]);
    expect(s.gearChildren("g1").map((g) => g.id)).toEqual(["g1c"]);
  });

  it("keeps only top-level cyber/bioware", () => {
    const s = buildSheetData({
      character: makeCharacter({
        derived: {
          cyberware: [{ id: "c1" }, { id: "c1a", parent_id: "c1" }] as any,
          bioware: [{ id: "b1" }] as any,
        },
      }),
      catalog: makeCatalog(),
      tr: identityTr,
      layout: "standard",
    });
    expect(s.cyber.map((c: any) => c.id)).toEqual(["c1"]);
    expect(s.bio.map((c: any) => c.id)).toEqual(["b1"]);
  });

  it("resolves active skills: SR5 non-exotic, rating > 0, pool = rating + attr, sorted", () => {
    const catalog = makeCatalog({
      skills: {
        groups: [],
        skills: [
          {
            id: "1",
            name: "Pistols",
            attribute: "AGI",
            category: "Combat",
            skillgroup: null,
            source: "SR5",
          },
          {
            id: "2",
            name: "Archery",
            attribute: "AGI",
            category: "Combat",
            skillgroup: null,
            source: "SR5",
          },
          {
            id: "3",
            name: "Astral",
            attribute: "INT",
            category: "Magic",
            skillgroup: null,
            source: "SR5",
          },
          {
            id: "4",
            name: "Exotic Ranged",
            attribute: "AGI",
            category: "Combat",
            skillgroup: null,
            source: "SR5",
            exotic: true,
          },
        ],
      } as any,
    });
    const s = buildSheetData({
      character: makeCharacter({
        derived: {
          totals: { AGI: 5, INT: 4 } as any,
          skill_totals: { Pistols: 4, Astral: 0 },
        },
      }),
      catalog,
      tr: identityTr,
      layout: "standard",
    });
    // Astral (rating 0) and the exotic skill are dropped; only Pistols survives.
    expect(s.activeSkills).toEqual([
      { name: "Pistols", attribute: "AGI", rating: 4, pool: 9, soft: 0, spec: undefined },
    ]);
  });
});
