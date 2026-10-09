import { testUi } from "@/tests/fixtures";
import {
  dropRemovedWarePicks,
  dropSkillPicksForPrefix,
  qualityBlockReason,
  qualityDisplayRows,
  qualityLevelMax,
  setQualityLevel,
  qualityTreeMet,
  reqNodeMet,
  type QualityReqCtx,
} from "@/lib/character/quality";

const baseCtx = (over: Partial<QualityReqCtx> = {}): QualityReqCtx => ({
  qualities: new Set(),
  metatypes: new Set(["Human"]),
  magenabled: false,
  resenabled: false,
  skills: {},
  knowledge: {},
  powers: new Set(),
  spells: new Set(),
  cyberware: new Set(),
  bioware: new Set(),
  tradition: "",
  essence: 6,
  essLost: 0,
  ...over,
});

describe("reqNodeMet", () => {
  it("set-membership tags", () => {
    expect(reqNodeMet({ tag: "quality", name: "Focused Concentration" }, baseCtx())).toBe(false);
    expect(
      reqNodeMet(
        { tag: "quality", name: "Focused Concentration" },
        baseCtx({ qualities: new Set(["Focused Concentration"]) }),
      ),
    ).toBe(true);
    expect(reqNodeMet({ tag: "metatype", name: "Human" }, baseCtx())).toBe(true);
    expect(
      reqNodeMet({ tag: "tradition", name: "Hermeticism" }, baseCtx({ tradition: "Hermeticism" })),
    ).toBe(true);
  });

  it("magenabled / resenabled", () => {
    expect(reqNodeMet({ tag: "magenabled" }, baseCtx({ magenabled: true }))).toBe(true);
    expect(reqNodeMet({ tag: "resenabled" }, baseCtx())).toBe(false);
  });

  it("skill: pool >= val, knowledge pool via type", () => {
    const ctx = baseCtx({ skills: { Sorcery: 5 }, knowledge: { "Magical Theory": 2 } });
    expect(reqNodeMet({ tag: "skill", name: "Sorcery", val: 4 }, ctx)).toBe(true);
    expect(reqNodeMet({ tag: "skill", name: "Sorcery", val: 6 }, ctx)).toBe(false);
    expect(
      reqNodeMet({ tag: "skill", name: "Magical Theory", val: 2, type: "Knowledge" }, ctx),
    ).toBe(true);
    expect(reqNodeMet({ tag: "skill", name: "Sorcery" }, baseCtx({ skills: { Sorcery: 1 } }))).toBe(
      true,
    ); // default val 1
  });

  it("ess: positive checks essence, negative checks essLost", () => {
    expect(reqNodeMet({ tag: "ess", value: 5 }, baseCtx({ essence: 6 }))).toBe(true);
    expect(reqNodeMet({ tag: "ess", value: 5 }, baseCtx({ essence: 4 }))).toBe(false);
    expect(reqNodeMet({ tag: "ess", value: -2 }, baseCtx({ essLost: 3 }))).toBe(true);
    expect(reqNodeMet({ tag: "ess", value: -2 }, baseCtx({ essLost: 1 }))).toBe(false);
  });

  it("oneof / allof / group", () => {
    const ctx = baseCtx({ qualities: new Set(["A"]) });
    expect(
      reqNodeMet(
        {
          tag: "oneof",
          children: [
            { tag: "quality", name: "A" },
            { tag: "quality", name: "B" },
          ],
        },
        ctx,
      ),
    ).toBe(true);
    expect(
      reqNodeMet(
        {
          tag: "allof",
          children: [
            { tag: "quality", name: "A" },
            { tag: "quality", name: "B" },
          ],
        },
        ctx,
      ),
    ).toBe(false);
    expect(reqNodeMet({ tag: "oneof", children: [] }, ctx)).toBe(true);
    expect(reqNodeMet({ tag: "group", children: [] }, ctx)).toBe(true);
  });

  it("unknown tag -> false", () => {
    expect(reqNodeMet({ tag: "sasquatch" }, baseCtx())).toBe(false);
  });
});

describe("qualityTreeMet / qualityBlockReason", () => {
  it("empty tree is met", () => {
    expect(qualityTreeMet(undefined, baseCtx())).toBe(true);
    expect(qualityTreeMet([], baseCtx())).toBe(true);
  });
  it("every top-level node must pass", () => {
    const ctx = baseCtx({ magenabled: true });
    expect(qualityTreeMet([{ tag: "magenabled" }, { tag: "metatype", name: "Human" }], ctx)).toBe(
      true,
    );
    expect(qualityTreeMet([{ tag: "magenabled" }, { tag: "metatype", name: "Elf" }], ctx)).toBe(
      false,
    );
  });
  it("qualityBlockReason: unmet required / matched forbidden / clear", () => {
    const ctx = baseCtx({ magenabled: true });
    expect(
      qualityBlockReason({ required_tree: [{ tag: "magenabled" }] } as never, ctx, testUi),
    ).toBe("");
    expect(
      qualityBlockReason({ required_tree: [{ tag: "resenabled" }] } as never, ctx, testUi),
    ).toBe("前提を満たしていません");
    expect(
      qualityBlockReason({ forbidden_tree: [{ tag: "magenabled" }] } as never, ctx, testUi),
    ).toBe("現在のキャラクターでは取れません");
  });
});

describe("dropSkillPicksForPrefix / dropRemovedWarePicks", () => {
  it("drops picks whose key starts with any prefix", () => {
    expect(
      dropSkillPicksForPrefix(
        { "quality:q1:0": "Pistols", "quality:q2:0": "Blades", "mentor:x": "y" },
        ["quality:q1:"],
      ),
    ).toEqual({ "quality:q2:0": "Blades", "mentor:x": "y" });
  });
  it("drops ware:<id>: picks whose id is no longer installed", () => {
    expect(
      dropRemovedWarePicks(
        { "ware:w1:skill": "Pistols", "ware:w2:skill": "Blades", other: "keep" },
        [{ id: "w1" } as never],
      ),
    ).toEqual({ "ware:w1:skill": "Pistols", other: "keep" });
  });
});

describe("quality levels", () => {
  const spec = {
    id: "ind",
    name: "Indomitable (Physical)",
    max_takes: 3,
    has_levels: true,
    include_in_limit: ["Indomitable (Mental)"],
  };
  const sibling = { id: "mental", name: "Indomitable (Mental)" };
  const row = {
    id: "magic",
    name: "Magic Resistance",
    karma: 6,
    has_levels: true,
    category: "Positive",
    source: "SR5",
  };

  it("combines levels and sums total and career karma without mutating engine rows", () => {
    const rows = [row, { ...row, career_cost: 12 }, { ...row, career_cost: 12 }];
    expect(qualityDisplayRows(rows)).toEqual([{ ...row, level: 3, karma: 18, career_cost: 24 }]);
    expect(rows[0].karma).toBe(6);
    expect(qualityDisplayRows([row])[0].level).toBe(1);
  });

  it("keeps distinct targets and free grants apart; repeatable nonlevels stay separate", () => {
    const rows = [
      row,
      { ...row, extra: "A" },
      { ...row, free: true },
      { ...row, has_levels: false },
      { ...row, has_levels: false },
    ];
    expect(qualityDisplayRows(rows)).toHaveLength(5);
    expect(qualityDisplayRows(rows).map((q) => q.level)).toEqual([1, 1, 1, undefined, undefined]);
  });

  it("resolves level metadata from the catalog for older derived payloads", () => {
    const { has_levels: _levels, ...old } = row;
    expect(
      qualityDisplayRows([old, old], [{ id: "magic", has_levels: true } as never])[0],
    ).toMatchObject({ level: 2, karma: 12 });
  });

  it("limits the selected total by siblings, including a separate shared cap", () => {
    expect(qualityLevelMax(spec as never, ["ind", "mental"], [spec, sibling] as never)).toBe(2);
    expect(
      qualityLevelMax({ ...spec, limit_with_inclusions: 4 } as never, ["mental", "mental"], [
        spec,
        sibling,
      ] as never),
    ).toBe(2);
    expect(
      qualityLevelMax(spec as never, ["mental", "mental", "mental"], [spec, sibling] as never),
    ).toBe(0);
  });

  it("changes the total while preserving other qualities and earlier career levels", () => {
    const ids = ["ind", "other", "ind", "third", "ind"];
    expect(setQualityLevel(ids, "ind", 2)).toEqual(["ind", "other", "ind", "third"]);
    expect(setQualityLevel(ids, "ind", 4)).toEqual([...ids, "ind"]);
    expect(setQualityLevel(ids, "ind", 0)).toEqual(["other", "third"]);
  });
});
