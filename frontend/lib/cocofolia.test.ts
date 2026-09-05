import {
  buildChatPalette,
  buildCocofolia,
  buildCocofoliaConjured,
  buildSpiritPieces,
  buildSpritePieces,
} from "@/lib/cocofolia";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

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
  } as any,
});

describe("buildChatPalette", () => {
  it("always emits the initiative line + the fixed defense/resist rolls", () => {
    const out = buildChatPalette(makeCharacter(), makeCatalog(), identityTr);
    expect(out.split("\n")[0]).toBe("1D6+6 イニシアチブ");
    for (const label of ["完全回避", "フル防御", "冷静", "記憶", "ダメージ抵抗（＋装甲）"]) {
      expect(out).toContain(label);
    }
    expect(out).toContain("エッジ振り足しは B6→R6");
  });

  it("emits a skill roll (pool = rating + attr, limit = attr's limit) and its spec", () => {
    const ch = makeCharacter({
      skill_specializations: { Pistols: "Revolvers" },
      derived: {
        totals: { AGI: 5 } as any,
        skill_totals: { Pistols: 4 },
        skill_specializations: { Pistols: "Revolvers" },
      },
    });
    const out = buildChatPalette(ch, pistolsCatalog, identityTr);
    expect(out).toContain("9B6@3 Pistols");
    expect(out).toContain("11B6@3 Pistols：Revolvers");
  });

  it("emits a weapon attack line (pool = skill + AGI, limit = Accuracy)", () => {
    const ch = makeCharacter({
      derived: {
        totals: { AGI: 5 } as any,
        skill_totals: { Pistols: 4 },
        weapons: [
          {
            id: "w1",
            name: "Predator V",
            useskill: "Pistols",
            damage: "8P",
            ap: "-1",
            accuracy: "5",
          },
        ] as any,
      },
    });
    const out = buildChatPalette(ch, pistolsCatalog, identityTr);
    expect(out).toContain("// ── 武器 ──");
    expect(out).toContain("9B6@5 Predator V攻撃 ［DV8P AP-1］");
  });

  it("emits a spellcasting line (pool = Spellcasting + MAG)", () => {
    const scCatalog = makeCatalog({
      skills: {
        groups: [],
        skills: [{ name: "Spellcasting", attribute: "MAG", category: "Magical", source: "SR5" }],
      } as any,
    });
    const ch = makeCharacter({
      derived: {
        totals: { MAG: 5 } as any,
        skill_totals: { Spellcasting: 6 },
        spells: [{ id: "s1", name: "Manabolt", dv: "F-3" }] as any,
      },
    });
    const out = buildChatPalette(ch, scCatalog, identityTr);
    expect(out).toContain("// ── 術式（リミット＝Force） ──");
    expect(out).toContain("11B6 Manabolt ［DVF-3］");
  });

  it("adds a matrix block when a persona is present", () => {
    const ch = makeCharacter({
      derived: {
        cyberdeck: { attack: 5, sleaze: 4, dataprocessing: 3, firewall: 2 } as any,
      },
    });
    const out = buildChatPalette(ch, makeCatalog(), identityTr);
    expect(out).toContain("// ── マトリクス ──");
    expect(out).toContain("3B6@4 素早いハッキング"); // limit = Sleaze
    expect(out).toContain("3B6@5 データスパイク"); // limit = Attack
  });
});

describe("buildCocofolia", () => {
  it("produces a parseable ccfolia character piece", () => {
    const parsed = JSON.parse(
      buildCocofolia(makeCharacter({ name: "Wire" }), makeCatalog(), identityTr),
    );
    expect(parsed.kind).toBe("character");
    expect(parsed.data.name).toBe("Wire");
    expect(parsed.data.initiative).toBe(6);
    expect(typeof parsed.data.commands).toBe("string");
    expect(parsed.data.commands).toContain("イニシアチブ");

    const paramLabels = parsed.data.params.map((p: any) => p.label);
    expect(paramLabels).toEqual(expect.arrayContaining(["BOD", "AGI", "装甲", "ESS"]));
    // MAG / RES only appear when > 0
    expect(paramLabels).not.toContain("MAG");

    const statusLabels = parsed.data.status.map((s: any) => s.label);
    expect(statusLabels).toEqual(["物理CM", "精神CM", "エッジ"]);
  });
});

/**
 * The conjured pieces are the part nobody proofreads: a spirit is dropped on
 * the table and its palette is rolled as printed. Every number below is
 * arithmetic the exporter does itself — the engine supplies Force and the
 * attributes, not the pools — so a wrong constant here is a wrong roll at a
 * real table with nothing to catch it.
 */

const spirit = (over: any = {}) => ({
  id: "sp1",
  name: "Spirit of Fire",
  force: 4,
  services: 2,
  bound: true,
  role_label: "戦闘",
  attributes: { BOD: 5, AGI: 6, REA: 6, STR: 3, CHA: 4, INT: 4, LOG: 3, WIL: 4, INI: 12 },
  skills: [{ name: "Unarmed Combat", attribute: "AGI", rating: 0 }],
  powers: ["Engulf"],
  optionalpowers: [],
  weaknesses: ["Allergy (Water)"],
  ...over,
});

const sprite = (over: any = {}) => ({
  id: "spr1",
  name: "Courier Sprite",
  level: 3,
  services: 2,
  registered: true,
  matrix: { attack: 0, sleaze: 3, dataprocessing: 6, firewall: 4, initiative: 9 },
  skills: [{ name: "Hacking", rating: 0 }],
  powers: ["Hash"],
  ...over,
});

const conjure = (derived: any) =>
  JSON.parse(buildCocofoliaConjured(makeCharacter({ derived }) as any, makeCatalog(), identityTr));

describe("buildSpiritPieces", () => {
  it("only puts bound spirits on the table", () => {
    const pieces = buildSpiritPieces(
      makeCharacter({
        derived: { spirits: [spirit(), spirit({ id: "sp2", bound: false })] },
      }) as any,
      makeCatalog(),
      identityTr,
    );

    expect(pieces).toHaveLength(1);
    expect(pieces[0].data.name).toBe("Spirit of Fire F4");
  });

  it("derives the condition monitors from BOD and WIL, not from Force", () => {
    const [piece] = buildSpiritPieces(
      makeCharacter({ derived: { spirits: [spirit()] } }) as any,
      makeCatalog(),
      identityTr,
    );

    // 8 + ceil(BOD 5 / 2) = 11, 8 + ceil(WIL 4 / 2) = 10
    expect(piece.data.status).toEqual([
      { label: "物理CM", value: 11, max: 11 },
      { label: "精神CM", value: 10, max: 10 },
      { label: "エッジ", value: 4, max: 4 },
    ]);
  });

  it("rolls a skill at rating-or-Force + attribute, limited by Force", () => {
    const [piece] = buildSpiritPieces(
      makeCharacter({ derived: { spirits: [spirit()] } }) as any,
      makeCatalog(),
      identityTr,
    );

    // rating 0 falls back to Force 4, + AGI 6
    expect(piece.data.commands).toContain("10B6@4 Unarmed Combat");
  });

  it("spells out the resist rolls a GM would otherwise have to compute", () => {
    const [piece] = buildSpiritPieces(
      makeCharacter({ derived: { spirits: [spirit()] } }) as any,
      makeCatalog(),
      identityTr,
    );

    expect(piece.data.commands).toContain("2D6+12 イニシアチブ");
    expect(piece.data.commands).toContain("10B6 完全回避"); // REA 6 + INT 4
    expect(piece.data.commands).toContain("13B6 ダメージ抵抗（イミュニティ）"); // BOD 5 + 2×Force
    expect(piece.data.commands).toContain("8B6 精霊追放に対抗"); // 2×Force
  });

  it("carries powers and weaknesses as comments, and drops the line when empty", () => {
    const [withThem] = buildSpiritPieces(
      makeCharacter({ derived: { spirits: [spirit()] } }) as any,
      makeCatalog(),
      identityTr,
    );
    const [without] = buildSpiritPieces(
      makeCharacter({
        derived: { spirits: [spirit({ powers: [], optionalpowers: [], weaknesses: [] })] },
      }) as any,
      makeCatalog(),
      identityTr,
    );

    expect(withThem.data.commands).toContain("// パワー: Engulf");
    expect(withThem.data.commands).toContain("// 弱点: Allergy (Water)");
    expect(without.data.commands).not.toContain("// パワー");
    expect(without.data.commands).not.toContain("// 弱点");
  });

  it("falls back to Force × 2 when the engine gave no initiative", () => {
    const [piece] = buildSpiritPieces(
      makeCharacter({ derived: { spirits: [spirit({ attributes: { BOD: 4, WIL: 4 } })] } }) as any,
      makeCatalog(),
      identityTr,
    );

    expect(piece.data.initiative).toBe(8);
  });
});

describe("buildSpritePieces", () => {
  it("only puts registered sprites on the table", () => {
    const pieces = buildSpritePieces(
      makeCharacter({
        derived: { sprites: [sprite(), sprite({ id: "spr2", registered: false })] },
      }) as any,
      makeCatalog(),
      identityTr,
    );

    expect(pieces).toHaveLength(1);
    expect(pieces[0].data.name).toBe("Courier Sprite L3");
  });

  it("exposes the matrix attributes as params, not meat attributes", () => {
    const [piece] = buildSpritePieces(
      makeCharacter({ derived: { sprites: [sprite()] } }) as any,
      makeCatalog(),
      identityTr,
    );

    expect(piece.data.params).toEqual([
      { label: "A", value: "0" },
      { label: "S", value: "3" },
      { label: "DP", value: "6" },
      { label: "FW", value: "4" },
      { label: "INI", value: "9" },
      { label: "Level", value: "3" },
    ]);
  });

  it("rolls skills at rating-or-Level + Level, and defends at Firewall + Level", () => {
    const [piece] = buildSpritePieces(
      makeCharacter({ derived: { sprites: [sprite()] } }) as any,
      makeCatalog(),
      identityTr,
    );

    expect(piece.data.commands).toContain("6B6@3 Hacking"); // rating 0 -> Level 3, + Level
    expect(piece.data.commands).toContain("7B6 マトリクス防御"); // FW 4 + Level 3
    expect(piece.data.commands).toContain("6B6 消去（デレゾ）に対抗"); // 2×Level
  });

  it("has one matrix condition monitor, not a physical/stun pair", () => {
    const [piece] = buildSpritePieces(
      makeCharacter({ derived: { sprites: [sprite()] } }) as any,
      makeCatalog(),
      identityTr,
    );

    // 8 + ceil(Level 3 / 2) = 10
    expect(piece.data.status).toEqual([
      { label: "マトリクスCM", value: 10, max: 10 },
      { label: "エッジ", value: 3, max: 3 },
    ]);
  });
});

describe("buildCocofoliaConjured", () => {
  it("returns an empty string when there is nothing to conjure", () => {
    expect(buildCocofoliaConjured(makeCharacter(), makeCatalog(), identityTr)).toBe("");
    expect(
      buildCocofoliaConjured(
        makeCharacter({
          derived: {
            spirits: [spirit({ bound: false })],
            sprites: [sprite({ registered: false })],
          },
        }) as any,
        makeCatalog(),
        identityTr,
      ),
    ).toBe("");
  });

  it("is a JSON array of spirits then sprites", () => {
    const pieces = conjure({ spirits: [spirit()], sprites: [sprite()] });

    expect(pieces.map((p: any) => p.data.name)).toEqual(["Spirit of Fire F4", "Courier Sprite L3"]);
    expect(pieces.every((p: any) => p.kind === "character")).toBe(true);
  });
});
