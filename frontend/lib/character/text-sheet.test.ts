import { buildSheetData } from "@/lib/character/sheet-data";
import { textSheet } from "@/lib/character/text-sheet";
import {
  identityTr,
  makeCatalog,
  makeCharacter,
  RICH_CATALOG,
  RICH_CHARACTER,
} from "@/tests/fixtures";

/**
 * The text sheet is what gets pasted into a VTT or a chat window, so a wrong
 * number in it is a number somebody plays with. It is also the output nobody
 * looks at twice — a dropped section or a stat off by one reads as plausible
 * text, which is why this asserts on values rather than smoke-rendering.
 *
 * Built from the same `RICH_CHARACTER` as the visual sheet's section tests:
 * both consume `buildSheetData()`, and testing them against different data is
 * how the two quietly stop agreeing.
 */

const sheet = (character = RICH_CHARACTER, catalog = RICH_CATALOG) =>
  textSheet(buildSheetData({ character, catalog, tr: identityTr, layout: "standard" }));

/** The block under a `=== heading ===`, up to the blank line that ends it. */
function section(text: string, heading: string): string[] {
  const lines = text.split("\n");
  const at = lines.indexOf(`=== ${heading} ===`);
  if (at < 0) return [];
  const rest = lines.slice(at + 1);
  const end = rest.indexOf("");
  return (end < 0 ? rest : rest.slice(0, end)).filter(Boolean);
}

describe("textSheet header", () => {
  it("leads with the name, metatype and talent", () => {
    const [name, ident] = sheet().split("\n");

    expect(name).toBe("Test Runner");
    expect(ident).toContain("Human");
    expect(ident).toContain("Mundane");
  });

  it("names an unnamed character rather than emitting a blank first line", () => {
    const [first] = sheet(makeCharacter({ name: "" }), makeCatalog()).split("\n");

    expect(first).not.toBe("");
  });
});

describe("textSheet core stats", () => {
  it("prints initiative as value+Nd6, and the three limits", () => {
    const text = sheet();

    expect(text).toContain("6+1d6");
    expect(text).toContain("リミット 物3/精4/社4");
    expect(text).toContain("CM P10/S10");
  });

  it("omits MAG and RES unless the character has them", () => {
    // a mundane sheet listing 魔法 0 invites the reader to roll it
    const mundane = sheet(makeCharacter(), makeCatalog());

    const attrLine = mundane.split("\n")[3];
    expect(attrLine).not.toContain("MAG");
    expect(attrLine).not.toContain("RES");
  });
});

describe("textSheet sections", () => {
  it("renders a skill with its specialisation, rating and pool", () => {
    expect(section(sheet(), "技能")).toEqual(["  Pistols 4 [AGI プール 7]"]);
  });

  it("renders a weapon's damage, AP and accuracy", () => {
    const [weapon] = section(sheet(), "武器");

    expect(weapon).toContain("Ares Predator V");
    expect(weapon).toContain("DV 8P");
    expect(weapon).toContain("AP -1");
    expect(weapon).toContain("ACC 5");
  });

  it("lists worn armour with its rating", () => {
    const [armor] = section(sheet(), "防具");

    expect(armor).toContain("Armor Jacket");
    expect(armor).toContain("12");
  });

  it("tags cyberware and bioware separately and carries the essence cost", () => {
    const ware = section(sheet(), "ウェア");

    expect(ware[0]).toContain("Wired Reflexes");
    expect(ware[0]).toContain("R2");
    expect(ware[1]).toContain("Muscle Toner");
    expect(ware[0].slice(0, 6)).not.toBe(ware[1].slice(0, 6)); // different tag
  });

  it("renders a spell's category, type, range, duration and drain", () => {
    const [spell] = section(sheet(), "術式");

    expect(spell).toContain("Manabolt");
    expect(spell).toContain("DV F-3");
  });

  it("renders a vehicle's stat line", () => {
    const [vehicle] = section(sheet(), "車両・ドローン");

    expect(vehicle).toContain("Ford Americar");
    expect(vehicle).toContain("11"); // body
  });

  it("renders contacts with connection and loyalty", () => {
    expect(section(sheet(), "コンタクト")[0]).toContain("C3/L2");
  });

  it("keeps notes verbatim, one line per line", () => {
    const notes = section(sheet(makeCharacter({ notes: "one\ntwo" }), makeCatalog()), "メモ");

    expect(notes).toEqual(["  one", "  two"]);
  });
});

describe("textSheet omits what the character does not have", () => {
  const empty = sheet(makeCharacter(), makeCatalog());

  it.each([
    ["技能"],
    ["知識技能"],
    ["資質"],
    ["武器"],
    ["ウェア"],
    ["術式"],
    ["車両・ドローン"],
    ["コンタクト"],
    ["メモ"],
  ])("has no %s heading", (heading) => {
    expect(empty).not.toContain(`=== ${heading} ===`);
  });

  it("still prints the header and the always-on core block", () => {
    expect(empty.split("\n")[0]).toBeTruthy();
    expect(empty).toContain("=== 能力値 ===");
  });

  it("never leaves a trailing run of blank lines", () => {
    expect(empty).toBe(empty.trimEnd());
    expect(sheet()).toBe(sheet().trimEnd());
  });
});
