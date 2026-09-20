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
        errors: [{ key: "engine.skills.pointsOver", params: { used: 5, max: 4 } }],
      },
    });
    const items = buildChecklist(ch);
    expect(items).toHaveLength(1);
    expect(items[0]).toMatchObject({ severity: "error", tab: "skills" });
  });

  // The pick lists stop offering an item once its book is off, so a character
  // who already holds one has no other clue. It routes to the priority tab,
  // where the settings and the book checkboxes live.
  it("routes the out-of-book warning to the settings tab, as a warning", () => {
    const ch = makeCharacter({
      derived: {
        karma: { pool: 25, spent: 25, remaining: 0 },
        warnings: [
          {
            key: "engine.settings.outOfBooks",
            params: { count: 1, names: [{ tr: "Armanté Suit" }], more: 0, books: "RG" },
          },
        ],
      },
    });
    const items = buildChecklist(ch);
    expect(items).toHaveLength(1);
    expect(items[0]).toMatchObject({ severity: "warn", tab: "priority" });
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
        contacts: { used: 0, max: 0 },
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

  it("flags a missing paragon as an error of its own", () => {
    const items = buildChecklist(
      makeCharacter({
        derived: { karma: { pool: 25, spent: 25, remaining: 0 }, needs_paragon: true },
      }),
    );
    expect(items.find((i) => i.id === "needs-paragon")).toMatchObject({
      severity: "error",
      tab: "qualities",
      ref: "KC p.102",
    });
    expect(items.find((i) => i.id === "needs-mentor")).toBeUndefined();
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
      { id: "a", severity: "warn", notice: { key: "engine.contacts.unnamed" } },
      { id: "b", severity: "info", notice: { key: "check.karmaLeft" } },
    ]);
    expect(s).toEqual({ errors: 0, warns: 1, infos: 1, ok: true });
  });

  it("is not ok with an error present", () => {
    expect(
      checklistSummary([{ id: "a", severity: "error", notice: { key: "engine.karma.negative" } }])
        .ok,
    ).toBe(false);
  });
});

describe("guessTab", () => {
  it("routes an engine notice by the area in its key", () => {
    expect(guessTab("engine.nuyen.negative")).toBe("gear");
    expect(guessTab("engine.attrs.essenceDepleted")).toBe("attrs");
    expect(guessTab("engine.settings.outOfBooks")).toBe("priority");
    expect(guessTab("engine.somethingNew.whatever")).toBeUndefined();
    expect(guessTab("check.karmaLeft")).toBeUndefined();
  });
});
