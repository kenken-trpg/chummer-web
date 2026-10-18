import { describe, expect, it } from "vitest";
import {
  attrLabel,
  attrName,
  attrShort,
  contactTerm,
  makeT,
  makeTextTr,
  makeTr,
  makeTrSkillGroup,
  scopeTr,
  specTr,
} from "@/lib/ui-strings";

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

describe("contactTerm", () => {
  const catalog = {
    translations: { Spider: "クモ", Armorer: "武器整備" },
    translations_by_kind: {
      contact: { Spider: "スパイダー", Fixer: "フィクサー", Female: "女性" },
    },
  };

  it("reads a contact's word as a contact, not as the flat table's namesake", () => {
    const tr = makeTr(catalog as never, "ja");
    expect(contactTerm(tr, "Spider")).toBe("スパイダー");
    expect(contactTerm(tr, "Fixer")).toBe("フィクサー");
    expect(contactTerm(tr, "Female")).toBe("女性");
  });

  it("leaves the player's own words as written, even where the flat table has them", () => {
    const tr = makeTr(catalog as never, "ja");
    expect(contactTerm(tr, "Armorer")).toBe("Armorer");
    expect(contactTerm(tr, "my old squadmate")).toBe("my old squadmate");
  });

  it("is English in English", () => {
    expect(contactTerm(makeTr(catalog as never, "en"), "Spider")).toBe("Spider");
  });
});

describe("specTr", () => {
  const catalog = {
    translations: { Spirits: "精霊", Combat: "戦闘", "Rotary Wing": "Rotary Wing" },
    translations_by_kind: { skill: {} },
    skills: {
      spec_names: {
        "Astral Combat": { Spirits: "対精霊" },
        "Pilot Aircraft": { "Rotary Wing": "回転翼機" },
      },
    },
  };

  it("reads a specialization as its skill's, where the flat table has another thing", () => {
    const tr = makeTr(catalog as never, "ja");
    expect(specTr(tr, "Astral Combat", "Spirits")).toBe("対精霊");
    expect(specTr(tr, "Pilot Aircraft", "Rotary Wing")).toBe("回転翼機");
  });

  it("falls back to the flat table for another skill or a custom one", () => {
    const tr = makeTr(catalog as never, "ja");
    expect(specTr(tr, "Arcana", "Spirits")).toBe("精霊");
    expect(specTr(tr, "Astral Combat", "Bound spirits only")).toBe("Bound spirits only");
  });

  it("survives a scoped translator, and is English in English", () => {
    expect(
      specTr(scopeTr(makeTr(catalog as never, "ja"), "skill"), "Astral Combat", "Spirits"),
    ).toBe("対精霊");
    expect(specTr(makeTr(catalog as never, "en"), "Astral Combat", "Spirits")).toBe("Spirits");
  });
});

describe("makeTextTr", () => {
  const texts = { text_translations: { "mentor/ab-12/advantage": "全員：追跡テストにダイス+2" } };

  it("reads a row's sentence by its id, whatever the id's case", () => {
    const textTr = makeTextTr(texts, "ja");
    expect(textTr("mentor", "AB-12", "advantage", "All: +2 dice for Tracking tests.")).toBe(
      "全員：追跡テストにダイス+2",
    );
  });

  it("keeps the English for another field, an untranslated row, or the English UI", () => {
    expect(makeTextTr(texts, "ja")("mentor", "ab-12", "disadvantage", "Loyal.")).toBe("Loyal.");
    expect(makeTextTr(texts, "ja")("mentor", "cd-34", "advantage", "Other.")).toBe("Other.");
    expect(makeTextTr(texts, "en")("mentor", "ab-12", "advantage", "All: +2")).toBe("All: +2");
  });
});
