import { buildChatPalette, buildCocofolia } from "@/lib/cocofolia";
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
