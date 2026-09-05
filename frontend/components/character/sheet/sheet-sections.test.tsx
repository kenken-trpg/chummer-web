import { render } from "@testing-library/react";
import { buildSheetData } from "@/lib/character/sheet-data";
import {
  identityTr,
  makeCatalog,
  makeCharacter,
  RICH_CATALOG,
  RICH_CHARACTER,
} from "@/tests/fixtures";
import { ActionDpSection } from "@/components/character/sheet/sections/ActionDp";
import { CareerSection } from "@/components/character/sheet/sections/Career";
import { CombatSection } from "@/components/character/sheet/sections/Combat";
import { ContactsSection } from "@/components/character/sheet/sections/Contacts";
import { CoreSection } from "@/components/character/sheet/sections/Core";
import { DescriptionSection } from "@/components/character/sheet/sections/Description";
import { DrugsSection } from "@/components/character/sheet/sections/Drugs";
import { KnowledgeSection } from "@/components/character/sheet/sections/Knowledge";
import { MagicSection } from "@/components/character/sheet/sections/Magic";
import { MartialSection } from "@/components/character/sheet/sections/Martial";
import { MatrixSection } from "@/components/character/sheet/sections/Matrix";
import { MiscGearSection } from "@/components/character/sheet/sections/MiscGear";
import { QualitiesSection } from "@/components/character/sheet/sections/Qualities";
import { ResonanceSection } from "@/components/character/sheet/sections/Resonance";
import { SinSection } from "@/components/character/sheet/sections/Sin";
import { SkillsSection } from "@/components/character/sheet/sections/Skills";
import { VehiclesSection } from "@/components/character/sheet/sections/Vehicles";
import { WareSection } from "@/components/character/sheet/sections/Ware";

/* eslint-disable @typescript-eslint/no-explicit-any */

// A `derived` payload that touches every sheet section with realistic nested
// rows. Rows are hand-shaped only far enough to render, then cast — like the
// rest of the suite's fixtures.

const s = buildSheetData({
  character: RICH_CHARACTER,
  catalog: RICH_CATALOG,
  tr: identityTr,
  layout: "standard",
});

const SECTIONS: [string, (p: typeof s) => React.ReactNode, string][] = [
  ["コア", CoreSection, "イニシアチブ"],
  ["技能", SkillsSection, "Pistols"],
  ["知識技能", KnowledgeSection, "Seattle Gangs"],
  ["キャリア", CareerSection, "報酬"],
  ["資質", QualitiesSection, "Ambidextrous"],
  ["アクションDP", ActionDpSection, "Hack"],
  ["戦闘", CombatSection, "Ares Predator V"],
  ["ウェア", WareSection, "Wired Reflexes"],
  ["マトリクス", MatrixSection, "Meta Link"],
  ["魔法", MagicSection, "Manabolt"],
  ["共鳴", ResonanceSection, "Cleaner"],
  ["武道", MartialSection, "Krav Maga"],
  ["コンタクト", ContactsSection, "Fixer"],
  ["車両・ドローン", VehiclesSection, "Ford Americar"],
  ["ドラッグ／毒物", DrugsSection, "Kamikaze"],
  ["SIN／ライセンス", SinSection, "Fake SIN"],
  ["その他ギア", MiscGearSection, "Medkit"],
  ["記述", DescriptionSection, "背景メモ"],
];

describe("sheet sections — smoke render", () => {
  it.each(SECTIONS)("%s renders with populated derived data", (_title, Section, marker) => {
    const { container } = render(<Section {...(s as any)} />);
    // the section did not collapse to null and shows a representative value
    expect(container.querySelector("section.sheet-section")).not.toBeNull();
    expect(container.textContent).toContain(marker);
  });

  it("every section collapses to null for an empty character", () => {
    const empty = buildSheetData({
      character: makeCharacter(),
      catalog: makeCatalog(),
      tr: identityTr,
      layout: "standard",
    });
    for (const [title, Section] of SECTIONS) {
      if (title === "コア") continue; // always-on
      const { container } = render(<Section {...(empty as any)} />);
      expect(container.querySelector("section.sheet-section")).toBeNull();
    }
  });
});
