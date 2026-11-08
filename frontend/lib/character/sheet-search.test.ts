import { buildSheetSearch, searchSheet } from "./sheet-search";
import { makeCharacter, makeCatalog, identityTr } from "@/tests/fixtures";
import type { Catalog } from "@/lib/types";

function example() {
  const catalog = makeCatalog({
    gear: [
      { id: "bag", name: "Backpack", category: "Containers" },
      { id: "kit", name: "Medkit", category: "Biotech" },
      { id: "unowned", name: "Not owned" },
    ] as Catalog["gear"],
  });
  const character = makeCharacter({
    gear: [
      { id: "bag-1", gear_id: "bag", nickname: "救急袋", location: "loc" },
      { id: "kit-1", gear_id: "kit", parent_id: "bag-1", notes: "卓で共有" },
      { id: "kit-2", gear_id: "kit", nickname: "予備" },
    ],
    gear_locations: [{ id: "loc", name: "隠れ家" }],
  });
  const tr = (name: string) => ({ Medkit: "医療キット", Backpack: "バックパック" })[name] ?? name;
  return buildSheetSearch(character, catalog, tr);
}

it("finds owned names in both languages, nicknames and notes, including hidden children", () => {
  const entries = example();
  expect(searchSheet(entries, "ｍｅｄｋｉｔ", "ja")).toHaveLength(2);
  expect(searchSheet(entries, "医療キット 共有", "ja").map((e) => e.key)).toEqual(["gear/kit-1"]);
  expect(searchSheet(entries, "予備", "ja")[0].key).toBe("gear/kit-2");
  expect(searchSheet(entries, "not owned", "en")).toEqual([]);
  expect(searchSheet(entries, "  ", "ja")).toEqual([]);
});

it("includes the container and its inherited storage location and preserves exact row targets", () => {
  const entry = searchSheet(example(), "隠れ家 共有", "ja")[0];
  expect(entry.path).toEqual(["隠れ家", "救急袋"]);
  expect(entry.target).toEqual({ key: "gear/kit-1", tab: "gear", gearKind: "misc" });
});

it("routes a program inside a drone to that drone's category", () => {
  const character = makeCharacter({
    drones: [{ id: "drone", gear_id: "drone-spec" }],
    programs: [{ id: "prog", gear_id: "prog-spec", parent_id: "drone" }],
  });
  const catalog = makeCatalog({
    drones: [{ id: "drone-spec", name: "Fly-Spy" }],
    programs: [{ id: "prog-spec", name: "Clearsight" }],
  } as unknown as Partial<Catalog>);
  const result = searchSheet(
    buildSheetSearch(character, catalog, identityTr),
    "Clearsight",
    "en",
  )[0];
  expect(result.target).toEqual({ key: "programs/prog", tab: "gear", gearKind: "drone" });
  expect(result.path).toEqual(["Fly-Spy"]);
});

it("searches quality notes and protects traversal from cyclic parent links", () => {
  const ch = makeCharacter({
    gear: [
      { id: "a", gear_id: "gear", parent_id: "b" },
      { id: "b", gear_id: "gear", parent_id: "a" },
    ],
    quality_notes: { q: "左手" },
    derived: {
      qualities: [{ id: "q", name: "Ambidextrous", category: "Positive", source: "SR5", karma: 4 }],
    },
  });
  const catalog = makeCatalog({ gear: [{ id: "gear", name: "Bag" }] as Catalog["gear"] });
  const entries = buildSheetSearch(ch, catalog, identityTr);
  expect(searchSheet(entries, "左手", "ja")[0].target).toEqual({
    key: "qualities/q",
    tab: "qualities",
  });
  expect(entries.filter((e) => e.originalName === "Bag")).toHaveLength(2);
});

it("includes computed free ware and keeps programs in an implanted deck's own editor", () => {
  const ch = makeCharacter({
    cyberware: [{ id: "implant", ware_id: "implant-spec" }],
    cyberdecks: [{ id: "deck", gear_id: "deck-spec", parent_id: "implant" }],
    programs: [{ id: "prog", gear_id: "prog-spec", parent_id: "deck" }],
    derived: { cyberware: [{ id: "free", name: "Free implant", ware_id: "free-spec" }] as never },
  });
  const catalog = makeCatalog({
    cyberdecks: [{ id: "deck-spec", name: "Deck" }],
    programs: [{ id: "prog-spec", name: "Browse" }],
    cyberware: { grades: [], items: [{ id: "implant-spec", name: "Housing" }] },
  } as unknown as Partial<Catalog>);
  const entries = buildSheetSearch(ch, catalog, identityTr);
  expect(searchSheet(entries, "Free implant", "en")[0].target.tab).toBe("cyber");
  expect(searchSheet(entries, "Browse", "en")[0].target.gearKind).toBe("cyberdeck");
});

it("finds learned skills and character background without matching untrained shopping choices", () => {
  const catalog = makeCatalog({
    skills: { skills: [{ id: "pistols", name: "Pistols" }], groups: [], knowledge: [] },
  } as unknown as Partial<Catalog>);
  const ch = makeCharacter({
    skills: { Pistols: 2 },
    skill_specializations: { Pistols: "Hold-outs" },
    background: "Old Seattle",
  });
  const entries = buildSheetSearch(ch, catalog, identityTr);
  expect(searchSheet(entries, "Hold-outs", "en")[0].target).toEqual({
    key: "skills/Pistols",
    tab: "skills",
  });
  expect(searchSheet(entries, "Seattle", "en")[0].target.tab).toBe("sheet");
});
