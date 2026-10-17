import { describe, expect, it } from "vitest";
import { qualityRestriction, talentAllowed, talentsFor } from "@/lib/character/metatype-limits";
import { makeCatalog } from "@/tests/fixtures";
import type { Catalog } from "@/lib/types/catalog";

const meta = (name: string, category: string, extra: Record<string, unknown> = {}) => ({
  name,
  id: name,
  category,
  attributes: {},
  metavariants: [],
  source: "SR5",
  ...extra,
});

const catalog = makeCatalog({
  metatypes: [
    meta("Human", "Metahuman"),
    meta("Centaur", "Metasapient"),
    meta("A.I.", "Metasapient", {
      quality_restriction: { Positive: ["Guts"], Negative: [] },
      metavariants: [
        {
          name: "E-Ghost",
          attributes: {},
          quality_restriction: { Positive: ["Lucky"], Negative: [] },
        },
        { name: "Xenosapient", attributes: {} },
      ],
    }),
  ] as Catalog["metatypes"],
});

const ai = { name: "A.I.", required: [{ kind: "metatype", name: "A.I." }] } as const;
const adept = { name: "Adept", forbidden: [{ kind: "metatype", name: "A.I." }] } as const;
const techno = {
  name: "Technomancer",
  required: [{ kind: "metatypecategory", name: "Metahuman" }],
} as const;

describe("talentAllowed", () => {
  it("keeps the A.I. to its own talent", () => {
    expect(talentAllowed(ai, "A.I.", catalog)).toBe(true);
    expect(talentAllowed(ai, "Human", catalog)).toBe(false);
    expect(talentAllowed(adept, "A.I.", catalog)).toBe(false);
    expect(talentAllowed(adept, "Human", catalog)).toBe(true);
  });

  it("reads a category off the metatype", () => {
    expect(talentAllowed(techno, "Human", catalog)).toBe(true);
    expect(talentAllowed(techno, "Centaur", catalog)).toBe(false);
  });

  it("lets anyone take a talent without the lists, as an older catalog sends", () => {
    expect(talentAllowed({}, "A.I.", catalog)).toBe(true);
  });
});

describe("talentsFor", () => {
  it("lists what the metatype may take, and the current pick even when it may not", () => {
    const names = (current: string) =>
      talentsFor([ai, adept, techno], "A.I.", current, catalog).map((t) => t.name);
    expect(names("A.I.")).toEqual(["A.I."]);
    expect(names("Adept")).toEqual(["A.I.", "Adept"]);
  });
});

describe("qualityRestriction", () => {
  it("takes the metavariant's list over the metatype's", () => {
    expect(qualityRestriction(catalog, "A.I.", "E-Ghost")?.Positive).toEqual(["Lucky"]);
    expect(qualityRestriction(catalog, "A.I.", "Xenosapient")?.Positive).toEqual(["Guts"]);
    expect(qualityRestriction(catalog, "A.I.", null)?.Positive).toEqual(["Guts"]);
  });

  it("is null for a metatype that takes any quality", () => {
    expect(qualityRestriction(catalog, "Human", null)).toBeNull();
  });
});
