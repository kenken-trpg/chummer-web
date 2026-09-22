import { render, screen } from "@testing-library/react";
import { buildSheetData } from "@/lib/character/sheet-data";
import { makeTr } from "@/lib/ui-strings";
import { RICH_CATALOG, RICH_CHARACTER } from "@/tests/fixtures";
import { KnowledgeSection } from "@/components/character/sheet/sections/Knowledge";
import { SkillsSection } from "@/components/character/sheet/sections/Skills";
import { knowItem, renderTab, skillsCatalog } from "./tabs/SkillsTab.helpers";

/**
 * `translations_by_kind` reaches the screen: each section asks for its own
 * kind. Every name here carries three readings — flat, active, knowledge — so
 * a section that forgot its `scopeTr`, or took the other half's, shows the
 * wrong one. (The real case: Medicine is 医術 as an active skill and 医学 as a
 * knowledge skill, and the flat table can hold only one.)
 */
function threeWay(...names: string[]) {
  const table = (tag: string) => Object.fromEntries(names.map((n) => [n, `${n}〈${tag}〉`]));
  return makeTr({
    translations: table("flat"),
    translations_by_kind: { skill: table("active"), knowledge_skill: table("know") },
  } as never);
}

describe("readings by kind, on screen", () => {
  it("the skills tab reads active skills as skills, and the knowledge list as knowledge", () => {
    const tr = threeWay("Blades", "Magic Theory");
    renderTab({ catalog: skillsCatalog({ knowledge: [knowItem] }), tr });
    expect(screen.getAllByText(/Blades〈active〉/).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/Magic Theory〈know〉/).length).toBeGreaterThan(0);
    expect(screen.queryByText(/〈flat〉/)).toBeNull();
    expect(screen.queryByText(/Blades〈know〉|Magic Theory〈active〉/)).toBeNull();
  });

  it("the sheet's skill and knowledge sections each take their own kind", () => {
    const tr = threeWay("Pistols", "Seattle Gangs");
    const s = buildSheetData({
      character: RICH_CHARACTER,
      catalog: RICH_CATALOG,
      tr,
      layout: "standard",
    });
    const skills = render(<SkillsSection {...s} />).container.textContent || "";
    expect(skills).toContain("Pistols〈active〉");
    expect(skills).not.toContain("Pistols〈flat〉");
    const know = render(<KnowledgeSection {...s} />).container.textContent || "";
    expect(know).toContain("Seattle Gangs〈know〉");
    expect(know).not.toContain("Seattle Gangs〈flat〉");
  });
});
