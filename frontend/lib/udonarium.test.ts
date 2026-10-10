// @vitest-environment jsdom
// The escaping test parses the result back with DOMParser, which is the same
// parser Udonarium reads the file with.
import {
  buildUdonariumConjured,
  buildUdonariumPalette,
  buildUdonariumXml,
  portraitEntry,
  slotTag,
  xmlEscape,
} from "@/lib/udonarium";
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

  // Two cyberarms mean two rows of Spurs in the save, and Ghile Mear's has
  // four. They roll the same test.
  it("collapses identical weapons into one entry, and drops a melee row's 0 mode", () => {
    const spur = {
      name: "Spurs",
      category: "Blades",
      type: "Melee",
      accuracy: "7",
      damage: "9P",
      ap: "-2",
      mode: "0",
      reach: "1",
    };
    const ch = makeCharacter({ derived: { weapons: [spur, { ...spur }] as never } });
    const out = buildUdonariumPalette(ch, makeCatalog(), identityTr);
    expect(out).toContain("//近接武器A=Spurs [DV9P/AP-2/リーチ+1]");
    expect(out).not.toContain("近接武器B");
  });

  it("keeps two weapons that differ in anything the palette shows", () => {
    const ch = makeCharacter({
      derived: {
        weapons: [
          {
            name: "Spurs",
            category: "Blades",
            type: "Melee",
            accuracy: "7",
            damage: "9P",
            reach: "1",
          },
          {
            name: "Spurs",
            category: "Blades",
            type: "Melee",
            accuracy: "8",
            damage: "9P",
            reach: "1",
          },
        ] as never,
      },
    });
    expect(buildUdonariumPalette(ch, makeCatalog(), identityTr)).toContain("近接武器B");
  });

  it("lists a technomancer's complex forms at the pool and Level the engine resolved", () => {
    const ch = makeCharacter({
      derived: {
        enabled_tabs: ["complexforms"],
        complex_forms: [
          { name: "Puppeteer", level: 3, fv: "L+1", test: { pool: 14, limit: 3 } },
        ] as never,
      },
    });
    expect(buildUdonariumPalette(ch, makeCatalog(), identityTr)).toContain(
      "14B6@3 Puppeteer [FVL+1]",
    );
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

  it("gives any persona a Matrix condition monitor and leaves it off everyone else", () => {
    const plain = buildUdonariumXml(makeCharacter(), makeCatalog(), identityTr);
    expect(plain).not.toContain("マトリックスCM");
    const decker = makeCharacter({
      derived: { cyberdeck: { device_rating: 5, attack: 4 } as never },
    });
    expect(buildUdonariumXml(decker, makeCatalog(), identityTr)).toContain(
      '<data name="マトリックスCM" type="numberResource" currentValue="0">11</data>',
    );
    // a technomancer runs on a living persona, and has one just the same
    const techno = makeCharacter({
      derived: { living_persona: { device_rating: 6, attack: 3 } as never },
    });
    expect(buildUdonariumXml(techno, makeCatalog(), identityTr)).toContain(
      '<data name="マトリックスCM" type="numberResource" currentValue="0">11</data>',
    );
  });

  // Udonarium drops every piece where the file says, so a party loaded one
  // file at a time would land in one stack.
  it("puts two characters in different places, and one character always in the same place", () => {
    const at = (name: string) =>
      /location\.x="(\d+)" location\.y="(\d+)"/
        .exec(buildUdonariumXml(makeCharacter({ name }), makeCatalog(), identityTr))
        ?.slice(1, 3);
    expect(at("Ghile Mear")).not.toEqual(at("Spirit Warden"));
    expect(at("Ghile Mear")).toEqual(at("Ghile Mear"));
  });
});

describe("buildUdonariumConjured", () => {
  const spirit = {
    name: "Spirit of Earth",
    force: 4,
    services: 3,
    bound: true,
    attributes: { BOD: 8, AGI: 2, REA: 3, STR: 8, CHA: 4, INT: 4, LOG: 3, WIL: 4, INI: 7 },
    skills: [{ name: "Assensing", attribute: "INT", rating: 4 }],
    powers: [{ name: "Guard" }],
    weaknesses: ["Allergy"],
  };
  const sprite = {
    name: "Machine Sprite",
    level: 4,
    services: 1,
    registered: true,
    matrix: { attack: 3, sleaze: 2, dataprocessing: 5, firewall: 4, initiative: 8 },
    skills: [{ name: "Computer", rating: 4 }],
    powers: [{ name: "Diagnostics" }],
  };

  it("is empty for a character with nothing bound or registered", () => {
    expect(buildUdonariumConjured(makeCharacter(), makeCatalog(), identityTr)).toEqual([]);
  });

  it("leaves out the spirits and sprites that are not bound or registered", () => {
    const ch = makeCharacter({
      derived: {
        spirits: [{ ...spirit, bound: false }] as never,
        sprites: [{ ...sprite, registered: false }] as never,
      },
    });
    expect(buildUdonariumConjured(ch, makeCatalog(), identityTr)).toEqual([]);
  });

  it("writes one xml per piece, under names a zip can hold side by side", () => {
    const ch = makeCharacter({
      derived: { spirits: [spirit] as never, sprites: [sprite] as never },
    });
    const files = buildUdonariumConjured(ch, makeCatalog(), identityTr);
    expect(files.map((f) => f.name)).toEqual(["data.xml", "data_1.xml"]);
    expect(files[0].content).toContain('<data name="name">Spirit of Earth F4</data>');
    expect(files[1].content).toContain('<data name="name">Machine Sprite L4</data>');
  });

  it("rolls a spirit off Force, and defines every variable it reads", () => {
    const ch = makeCharacter({ derived: { spirits: [spirit] as never } });
    const [file] = buildUdonariumConjured(ch, makeCatalog(), identityTr);
    const palette = /<chat-palette[^>]*>([\s\S]*)<\/chat-palette>/.exec(file.content)![1];
    const text = palette
      .replace(/&lt;/g, "<")
      .replace(/&gt;/g, ">")
      .replace(/&quot;/g, '"')
      .replace(/&apos;/g, "'")
      .replace(/&amp;/g, "&");
    expect(text).toContain("({INT}+{Assensing}+0)B6@{フォース} Assensing");
    // Immunity to Normal Weapons is Body plus twice the Force
    expect(text).toContain("({BOD}+{フォース}+{フォース})B6");
    expect(text).toContain("//フォース=4");
    expect(text).toContain("//Assensing=4");
    expect(undefinedRefs(text)).toEqual([]);
    // the counters the table clicks: Force and the services left
    expect(file.content).toContain(
      '<data name="フォース" type="numberResource" currentValue="4">4</data>',
    );
    expect(file.content).toContain(
      '<data name="残りサービス" type="numberResource" currentValue="3">3</data>',
    );
  });

  it("rolls a sprite off Level, capped at it, and defines every variable", () => {
    const ch = makeCharacter({ derived: { sprites: [sprite] as never } });
    const [file] = buildUdonariumConjured(ch, makeCatalog(), identityTr);
    const palette = /<chat-palette[^>]*>([\s\S]*)<\/chat-palette>/.exec(file.content)![1];
    expect(palette).toContain("({レベル}+{Computer}+0)B6@{レベル} Computer");
    expect(palette).toContain("({ファイアウォール}+{レベル}+0)B6");
    expect(palette).toContain("//レベル=4");
    expect(palette).toContain("//ファイアウォール=4");
    expect(undefinedRefs(palette)).toEqual([]);
    // a sprite has only a Matrix condition monitor
    expect(file.content).toContain('<data name="マトリックスCM"');
    expect(file.content).not.toContain('<data name="身体CM"');
  });
});

describe("portraitEntry", () => {
  // a 1x1 red PNG, and the SHA-256 of exactly those bytes
  const PNG =
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==";

  it("names the file after the hash of its bytes, which is what the piece points at", async () => {
    const entry = await portraitEntry(`data:image/png;base64,${PNG}`);
    expect(entry).not.toBeNull();
    // the identifier is a SHA-256, and the file is named after it
    expect(entry!.identifier).toMatch(/^[0-9a-f]{64}$/);
    expect(entry!.file.name).toBe(`${entry!.identifier}.png`);
    // and it really is the hash of the decoded bytes, not of the data URL
    const bytes = entry!.file.content as Uint8Array<ArrayBuffer>;
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    expect(
      Array.from(new Uint8Array(digest))
        .map((b) => b.toString(16).padStart(2, "0"))
        .join(""),
    ).toBe(entry!.identifier);
  });

  it("gives the same picture the same identifier, so two pieces share one copy", async () => {
    const a = await portraitEntry(`data:image/png;base64,${PNG}`);
    const b = await portraitEntry(`data:image/png;base64,${PNG}`);
    expect(a!.identifier).toBe(b!.identifier);
  });

  it("uses the extension the type calls for", async () => {
    const jpeg = await portraitEntry(`data:image/jpeg;base64,${PNG}`);
    expect(jpeg!.file.name.endsWith(".jpg")).toBe(true);
  });

  it("refuses anything that is not a portrait image, rather than carrying it", async () => {
    for (const bad of [
      "",
      "not a data url",
      "data:image/svg+xml;base64,PHN2Zy8+", // not a portrait type (and scriptable)
      "data:image/png;base64,", // empty
      "data:image/png;base64,!!!not base64!!!",
    ]) {
      expect(await portraitEntry(bad)).toBeNull();
    }
  });
});

describe("buildUdonariumXml with a portrait", () => {
  it("points the piece at the picture, and at the silhouette without one", async () => {
    const entry = await portraitEntry(
      "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
    );
    const ch = makeCharacter();
    expect(buildUdonariumXml(ch, makeCatalog(), identityTr, "ja", { image: entry })).toContain(
      `<data type="image" name="imageIdentifier">${entry!.identifier}</data>`,
    );
    expect(buildUdonariumXml(ch, makeCatalog(), identityTr)).toContain(
      '<data type="image" name="imageIdentifier">none_icon</data>',
    );
  });
});
