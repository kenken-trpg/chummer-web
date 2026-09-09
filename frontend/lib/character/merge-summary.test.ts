import { describe, expect, it } from "vitest";
import { groupChanges } from "@/lib/character/merge-summary";
import type { MergeChange } from "@/lib/api";

const edit = (file: string, entry: string, fields: string[]): MergeChange => ({
  file,
  entry,
  action: "edited",
  fields,
});

describe("groupChanges", () => {
  it("groups on the file, the action and the fields written", () => {
    // an edit to `source, page` and an edit to `techniques` are different
    // kinds of change to the same file, and must not land in one row
    const groups = groupChanges([
      edit("qualities.xml", "Adept", ["source", "page"]),
      edit("martialarts.xml", "Aikido", ["techniques"]),
      edit("qualities.xml", "Aptitude", ["source", "page"]),
    ]);
    expect(groups.map((g) => [g.file, g.fields.join(","), g.count])).toEqual([
      ["qualities.xml", "source,page", 2],
      ["martialarts.xml", "techniques", 1],
    ]);
  });

  it("keeps every entry name, in merge order", () => {
    const groups = groupChanges([edit("q.xml", "B", ["source"]), edit("q.xml", "A", ["source"])]);
    expect(groups[0].entries).toEqual(["B", "A"]);
  });

  it("puts the largest group first — it is what the pack mostly is", () => {
    const groups = groupChanges([
      { file: "m.xml", entry: "x", action: "added", fields: [] },
      edit("q.xml", "a", ["source"]),
      edit("q.xml", "b", ["source"]),
    ]);
    expect(groups[0].file).toBe("q.xml");
  });

  it("separates an addition from an edit to the same file", () => {
    const groups = groupChanges([
      { file: "m.xml", entry: "居合道", action: "added", fields: [] },
      edit("m.xml", "Aikido", ["source"]),
    ]);
    expect(groups.map((g) => g.action)).toEqual(["added", "edited"]);
  });

  it("returns nothing for a merge that changed nothing", () => {
    expect(groupChanges([])).toEqual([]);
  });
});
