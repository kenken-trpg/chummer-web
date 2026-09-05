import { describe, expect, it } from "vitest";
import { attrLabel, attrName, attrShort, makeT, makeTr, makeTrSkillGroup } from "@/lib/ui-strings";

/** The shape the backend ships: `ui_strings` keyed by locale, `translations`
 *  English -> Japanese (there is no English table; see `makeTr`). */
const catalog = {
  ui_strings: {
    ja: { String_AttributeBODShort: "強靱", String_AttributeBODLong: "強靱力" },
    en: { String_AttributeBODShort: "BOD", String_AttributeBODLong: "Body" },
  },
  translations: { "Armor Jacket": "アーマージャケット" },
};

describe("makeT", () => {
  it("reads the requested locale's table", () => {
    expect(makeT(catalog, "ja")("String_AttributeBODLong")).toBe("強靱力");
    expect(makeT(catalog, "en")("String_AttributeBODLong")).toBe("Body");
  });

  it("defaults to ja, the reference locale", () => {
    expect(makeT(catalog)("String_AttributeBODLong")).toBe("強靱力");
  });

  it("falls back to the caller's default, then the key", () => {
    const t = makeT(catalog, "en");
    expect(t("String_Nope", "fallback")).toBe("fallback");
    expect(t("String_Nope")).toBe("String_Nope");
  });

  it("survives a catalog that has not loaded, and a locale with no table", () => {
    expect(makeT(null, "en")("String_AttributeBODLong", "Body")).toBe("Body");
    // @ts-expect-error — a locale the backend did not ship
    expect(makeT(catalog, "fr")("String_AttributeBODLong", "Body")).toBe("Body");
  });
});

describe("makeTr", () => {
  it("translates catalog names in ja", () => {
    expect(makeTr(catalog, "ja")("Armor Jacket")).toBe("アーマージャケット");
  });

  it("is the identity in en — the catalog names are already English", () => {
    expect(makeTr(catalog, "en")("Armor Jacket")).toBe("Armor Jacket");
  });

  it("passes an untranslated name through rather than blanking it", () => {
    expect(makeTr(catalog, "ja")("Something New")).toBe("Something New");
    expect(makeTr(null, "ja")("Armor Jacket")).toBe("Armor Jacket");
  });
});

describe("attribute helpers", () => {
  it("build String_Attribute<KEY>Short|Long — the only keys the app reads", () => {
    const ja = makeT(catalog, "ja");
    const en = makeT(catalog, "en");
    expect(attrShort("BOD", ja)).toBe("強靱");
    expect(attrName("BOD", en)).toBe("Body");
    expect(attrLabel("BOD", en)).toBe("BOD Body");
  });

  it("falls back to the code for an attribute the lang file lacks", () => {
    const t = makeT(catalog, "en");
    expect(attrShort("EDG", t)).toBe("EDG");
    expect(attrLabel("EDG", t)).toBe("EDG EDG");
  });
});

describe("makeTrSkillGroup", () => {
  /** "Influence" is a spell in the flat table and a skill group in
   *  `group_names`; the group must not inherit the spell's reading. */
  const catalog = {
    translations: { Influence: "感化" },
    skills: { groups: ["Influence"], group_names: { Influence: "対人" } },
  } as unknown as Parameters<typeof makeTrSkillGroup>[0];

  it("prefers the group map over the colliding flat translation", () => {
    expect(makeTrSkillGroup(catalog, "ja")("Influence")).toBe("対人");
  });

  it("falls back to the flat table, then to the English name", () => {
    const bare = { translations: { Sorcery: "魔術" }, skills: { groups: [] } };
    const tr = makeTrSkillGroup(bare as never, "ja");
    expect(tr("Sorcery")).toBe("魔術");
    expect(tr("Tasking")).toBe("Tasking");
  });

  it("is the identity for en, like makeTr", () => {
    expect(makeTrSkillGroup(catalog, "en")("Influence")).toBe("Influence");
  });
});
