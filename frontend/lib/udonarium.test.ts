// @vitest-environment jsdom
// The escaping test parses the result back with DOMParser, which is the same
// parser Udonarium reads the file with.
import { buildUdonariumPalette, buildUdonariumXml, slotTag, xmlEscape } from "@/lib/udonarium";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";

const pistolsCatalog = makeCatalog({
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
    ],
  } as never,
});

/** Every `{name}` the palette reads has to be given a value by some
 *  `//name=…`, or Udonarium hands BCDice the literal text and the roll fails. */
function undefinedRefs(palette: string): string[] {
  const defined = new Set([...palette.matchAll(/^\/\/([^=\n]+)=/gm)].map((m) => m[1]));
  const used = new Set([...palette.matchAll(/\{([^}]+)\}/g)].map((m) => m[1]));
  return [...used].filter((name) => !defined.has(name));
}

describe("slotTag", () => {
  it("counts A..Z then AA, so a 27th weapon still gets its own variables", () => {
    expect([0, 1, 25, 26, 27].map(slotTag)).toEqual(["A", "B", "Z", "AA", "AB"]);
  });
});

describe("xmlEscape", () => {
  it("escapes all five predefined entities", () => {
    expect(xmlEscape(`Ares & "S-III" <x> 'y'`)).toBe(
      "Ares &amp; &quot;S-III&quot; &lt;x&gt; &apos;y&apos;",
    );
  });
});

describe("buildUdonariumPalette", () => {
  it("defines every variable it reads, on a bare character", () => {
    const out = buildUdonariumPalette(makeCharacter(), makeCatalog(), identityTr);
    expect(undefinedRefs(out)).toEqual([]);
  });

  it("defines every variable it reads, on a character with weapons, magic and a deck", () => {
    const ch = makeCharacter({
      derived: {
        totals: { AGI: 5, LOG: 5, MAG: 6, WIL: 4, INT: 4 } as never,
        skill_totals: { Pistols: 4, Spellcasting: 6, Hacking: 3, Assensing: 2 },
        enabled_tabs: ["spells", "spirits", "complexforms"],
        weapons: [
          {
            name: "Ares Predator V",
            category: "Pistols",
            type: "Ranged",
            accuracy: "5",
            damage: "8P",
            ap: "-1",
            mode: "SA",
            reach: "",
          },
          { name: "Knucks", category: "Unarmed", type: "Melee", accuracy: "Physical", reach: "0" },
        ] as never,
        spells: [{ name: "Fireball", kind: "spell", dv: "F-1" }] as never,
        cyberdeck: { attack: 4, sleaze: 3, dataprocessing: 5, firewall: 6 } as never,
      },
    });
    expect(undefinedRefs(buildUdonariumPalette(ch, pistolsCatalog, identityTr))).toEqual([]);
  });

  it("rolls a ranged weapon off AGI, its skill and its own modifier, capped at Accuracy", () => {
    const ch = makeCharacter({
      derived: {
        totals: { AGI: 5 } as never,
        skill_totals: { Pistols: 4 },
        weapons: [
          {
            name: "Ares Predator V",
            category: "Pistols",
            type: "Ranged",
            accuracy: "7",
            damage: "8P",
            ap: "-1",
            mode: "SA",
            reach: "",
          },
        ] as never,
      },
    });
    const out = buildUdonariumPalette(ch, pistolsCatalog, identityTr);
    expect(out).toContain("({AGI}+{射撃技能A}+{射撃補正A}+0)B6@{射撃精度A} {射撃武器A}");
    expect(out).toContain("//射撃武器A=Ares Predator V [DV8P/AP-1/SA]");
    expect(out).toContain("//射撃精度A=7");
    expect(out).toContain("//射撃技能A=4");
    expect(out).toContain("//射撃補正A=0");
  });

  it("points a melee weapon's Accuracy at the Physical limit variable", () => {
    const ch = makeCharacter({
      derived: {
        weapons: [
          { name: "Knucks", category: "Unarmed", type: "Melee", accuracy: "Physical", reach: "0" },
        ] as never,
      },
    });
    const out = buildUdonariumPalette(ch, makeCatalog(), identityTr);
    expect(out).toContain("//近接精度A={身体リミット}");
    expect(out).toContain("({AGI}+{近接技能A}+{近接補正A}+0)B6@{近接精度A} {近接武器A}");
  });

  it("gives each spell its own name and modifier variable", () => {
    const ch = makeCharacter({
      derived: {
        totals: { MAG: 6 } as never,
        skill_totals: { Spellcasting: 6 },
        enabled_tabs: ["spells"],
        spells: [
          { name: "Fireball", kind: "spell", dv: "F-1" },
          { name: "Invisibility", kind: "spell", dv: "F-1" },
        ] as never,
      },
    });
    const out = buildUdonariumPalette(ch, makeCatalog(), identityTr);
    expect(out).toContain("({MAG}+{Spellcasting}+{呪文補正A}+0)B6 {呪文A}");
    expect(out).toContain("//呪文A=Fireball [DVF-1]");
    expect(out).toContain("({MAG}+{Spellcasting}+{呪文補正B}+0)B6 {呪文B}");
    expect(out).toContain("//呪文B=Invisibility [DVF-1]");
    expect(out).toContain("//Spellcasting=6");
  });

  it("leaves out the magic and Matrix blocks a mundane runner has nothing for", () => {
    const out = buildUdonariumPalette(makeCharacter(), makeCatalog(), identityTr);
    expect(out).not.toContain("マトリックス");
    expect(out).not.toContain("呪文行使");
  });

  it("caps the Matrix actions at the persona's own attributes", () => {
    const ch = makeCharacter({
      derived: {
        totals: { LOG: 5, INT: 4, WIL: 4 } as never,
        skill_totals: { Hacking: 6, Cybercombat: 4, Computer: 3 },
        cyberdeck: { attack: 4, sleaze: 3, dataprocessing: 5, firewall: 6 } as never,
      },
    });
    const out = buildUdonariumPalette(ch, makeCatalog(), identityTr);
    expect(out).toContain("({LOG}+{Hacking}+0)B6@{スリーズ}");
    expect(out).toContain("({LOG}+{Cybercombat}+0)B6@{アタック}");
    expect(out).toContain("({INT}+{Computer}+0)B6@{データ処理}");
    expect(out).toContain("//スリーズ=3");
    expect(out).toContain("//ファイアウォール=6");
  });

  it("writes the skill list as plain numbers, not variables", () => {
    const ch = makeCharacter({
      derived: { totals: { AGI: 5 } as never, skill_totals: { Pistols: 4 } },
    });
    expect(buildUdonariumPalette(ch, pistolsCatalog, identityTr)).toContain(
      "9B6@{身体リミット} Pistols",
    );
  });

  it("lists the defaultable skills only when asked", () => {
    const ch = makeCharacter({ derived: { totals: { AGI: 5 } as never } });
    expect(buildUdonariumPalette(ch, pistolsCatalog, identityTr)).not.toContain("4B6");
    const un = buildUdonariumPalette(ch, pistolsCatalog, identityTr, "ja", { untrained: true });
    expect(un).toContain("4B6@{身体リミット} Pistols");
    expect(undefinedRefs(un)).toEqual([]);
  });
});

describe("buildUdonariumXml", () => {
  it("writes a ShadowRun5 piece with the condition monitors as resources", () => {
    const ch = makeCharacter({
      name: "Ghile Mear",
      derived: {
        condition_monitor: { physical: 11, stun: 10 },
        totals: { EDG: 3 } as never,
        movement: { walk: "10", run: "20", sprint: "2", sprint_bonus: 0 },
      },
    });
    const xml = buildUdonariumXml(ch, makeCatalog(), identityTr);
    expect(xml.startsWith('<?xml version="1.0" encoding="UTF-8"?>')).toBe(true);
    expect(xml).toContain('<chat-palette dicebot="ShadowRun5">');
    expect(xml).toContain('<data name="name">Ghile Mear</data>');
    expect(xml).toContain('<data name="身体CM" type="numberResource" currentValue="0">11</data>');
    expect(xml).toContain('<data name="エッジ" type="numberResource" currentValue="3">3</data>');
    expect(xml).toContain(
      '<data name="残り移動力" type="numberResource" currentValue="20">20</data>',
    );
    expect(xml).toContain("身体[][][][][][][][][][][]");
    expect(xml).toContain('<data type="image" name="imageIdentifier">none_icon</data>');
  });

  it("escapes the palette and the name, so the xml still parses", () => {
    const ch = makeCharacter({
      name: `Ares & "Co"`,
      derived: {
        weapons: [
          {
            name: "Ares S-III Super Squirt <2>",
            category: "Pistols",
            type: "Ranged",
            accuracy: "4",
            reach: "",
          },
        ] as never,
      },
    });
    const xml = buildUdonariumXml(ch, makeCatalog(), identityTr);
    expect(xml).not.toMatch(/<data name="name">[^<]*&(?!amp;|lt;|gt;|quot;|apos;)/);
    const doc = new DOMParser().parseFromString(xml, "application/xml");
    expect(doc.querySelector("parsererror")).toBeNull();
    expect(doc.documentElement.tagName).toBe("character");
    expect(doc.querySelector("chat-palette")?.textContent).toContain("Ares S-III Super Squirt <2>");
  });

  it("gives a deck-runner a Matrix condition monitor and leaves it off everyone else", () => {
    const plain = buildUdonariumXml(makeCharacter(), makeCatalog(), identityTr);
    expect(plain).not.toContain("マトリックスCM");
    const decker = makeCharacter({
      derived: { cyberdeck: { device_rating: 5, attack: 4 } as never },
    });
    expect(buildUdonariumXml(decker, makeCatalog(), identityTr)).toContain(
      '<data name="マトリックスCM" type="numberResource" currentValue="0">11</data>',
    );
  });
});
