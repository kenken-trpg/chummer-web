import { describe, expect, it } from "vitest";
import { buildChecklist, checklistSummary, guessTab } from "@/lib/character/checklist";
import { makeCharacter } from "@/tests/fixtures";

describe("buildChecklist", () => {
  it("returns no items for a fully-resolved chargen character", () => {
    const ch = makeCharacter({ derived: { karma: { pool: 25, spent: 25, remaining: 0 } } });
    expect(buildChecklist(ch)).toEqual([]);
  });

  it("surfaces engine errors and routes them to a tab", () => {
    const ch = makeCharacter({
      derived: {
        karma: { pool: 25, spent: 25, remaining: 0 },
        errors: ["技能点が不足しています（使用 5 / 上限 4）"],
      },
    });
    const items = buildChecklist(ch);
    expect(items).toHaveLength(1);
    expect(items[0]).toMatchObject({ severity: "error", tab: "skills" });
  });

  it("reports leftover priority points in chargen but not in career", () => {
    const derived = {
      karma: { pool: 25, spent: 25, remaining: 0 },
      points: {
        attributes: { used: 10, max: 16 },
        special: { used: 0, max: 0 },
        skills: { used: 0, max: 0 },
        skill_groups: { used: 0, max: 0 },
        knowledge: { used: 0, max: 0 },
      },
    };
    const chargen = buildChecklist(makeCharacter({ derived }));
    expect(chargen.find((i) => i.id === "left-attributes")).toMatchObject({
      severity: "info",
      tab: "attrs",
    });

    const career = buildChecklist(makeCharacter({ career: true, derived }));
    expect(career.find((i) => i.id === "left-attributes")).toBeUndefined();
  });

  it("flags leftover karma and nuyen as notes", () => {
    const items = buildChecklist(
      makeCharacter({
        derived: { karma: { pool: 25, spent: 18, remaining: 7 }, nuyen: 1200 },
      }),
    );
    expect(items.map((i) => i.id)).toEqual(expect.arrayContaining(["left-karma", "left-nuyen"]));
  });

  it("flags a missing mentor as an error", () => {
    const items = buildChecklist(
      makeCharacter({
        derived: { karma: { pool: 25, spent: 25, remaining: 0 }, needs_mentor: true },
      }),
    );
    expect(items.find((i) => i.id === "needs-mentor")).toMatchObject({
      severity: "error",
      tab: "qualities",
    });
  });

  it("lists unimplemented bonuses as notes", () => {
    const items = buildChecklist(
      makeCharacter({
        derived: {
          karma: { pool: 25, spent: 25, remaining: 0 },
          unimplemented_bonuses: [{ source: "Foo", tag: "bar" }],
        },
      }),
    );
    expect(items.find((i) => i.id === "unimpl-0")).toMatchObject({ severity: "info" });
  });
});

describe("checklistSummary", () => {
  it("counts by severity and is ok when there is no error", () => {
    const s = checklistSummary([
      { id: "a", severity: "warn", message: "" },
      { id: "b", severity: "info", message: "" },
    ]);
    expect(s).toEqual({ errors: 0, warns: 1, infos: 1, ok: true });
  });

  it("is not ok with an error present", () => {
    expect(checklistSummary([{ id: "a", severity: "error", message: "" }]).ok).toBe(false);
  });
});

describe("guessTab", () => {
  it("maps common engine phrasings", () => {
    expect(guessTab("新円が不足しています（残り -100¥）")).toBe("gear");
    expect(guessTab("エッセンスが0以下です")).toBe("attrs");
    expect(guessTab("何かよくわからない文言")).toBeUndefined();
  });
});
