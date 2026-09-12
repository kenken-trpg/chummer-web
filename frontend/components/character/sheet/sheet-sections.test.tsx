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

  it("the matrix section prints the VR initiative next to the persona", () => {
    const withVr = buildSheetData({
      character: {
        ...RICH_CHARACTER,
        derived: {
          ...RICH_CHARACTER.derived,
          matrix_initiative: {
            device: "living_persona",
            dataprocessing: 3,
            value: 7,
            cold_dice: 3,
            hot_dice: 4,
          },
        },
      } as any,
      catalog: RICH_CATALOG,
      tr: identityTr,
      layout: "standard",
    });
    const { container } = render(<MatrixSection {...(withVr as any)} />);
    expect(container.textContent).toContain("冷7+3d6");
    expect(container.textContent).toContain("熱7+4d6");
  });

  it("the core section prints the astral initiative only when there is one", () => {
    const sheet = (astral: unknown) =>
      buildSheetData({
        character: {
          ...RICH_CHARACTER,
          derived: { ...RICH_CHARACTER.derived, astral_initiative: astral },
        } as any,
        catalog: RICH_CATALOG,
        tr: identityTr,
        layout: "standard",
      });
    const awakened = render(<CoreSection {...(sheet({ value: 8, dice: 3 }) as any)} />);
    expect(awakened.container.textContent).toContain("アストラル・イニシアチブ8+3d6");
    const mundane = render(<CoreSection {...(sheet(null) as any)} />);
    expect(mundane.container.textContent).not.toContain("アストラル・イニシアチブ");
  });

  it("the core section prints movement in metres with the sprint rate", () => {
    const { container } = render(<CoreSection {...(s as any)} />);
    expect(container.textContent).toContain("歩6m / 走12m / 全力疾走 +2m/ヒット");
  });

  it("the magic section prints a bound spirit's powers with their action", () => {
    const { container } = render(<MagicSection {...(s as any)} />);
    expect(container.textContent).toContain("Engulf（物理・複雑・接触・維持）");
  });

  it("the resonance section prints a sprite's powers the same way", () => {
    const { container } = render(<ResonanceSection {...(s as any)} />);
    expect(container.textContent).toContain("Hash（物理・複雑・接触・即時）");
  });

  it("the magic section says so when Quickening is in hand", () => {
    const withQuickening = buildSheetData({
      character: {
        ...RICH_CHARACTER,
        derived: {
          ...RICH_CHARACTER.derived,
          enabled_tabs: [...(RICH_CHARACTER.derived.enabled_tabs || []), "initiation"],
          initiation: {
            grade: 1,
            karma: 13,
            choices: [],
            metamagics: [],
            arts: [],
            quickening: true,
          },
        },
      } as any,
      catalog: RICH_CATALOG,
      tr: identityTr,
      layout: "standard",
    });
    const { container } = render(<MagicSection {...(withQuickening as any)} />);
    expect(container.textContent).toContain("クイックニング可");
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

describe("<WareSection> on the compact sheet", () => {
  it("lists ware by name alone", () => {
    const standard = render(<WareSection {...(s as any)} />);
    expect(standard.container.querySelector(".sheet-list li")!.textContent).toContain("ESS −2");
    standard.unmount();

    const compact = buildSheetData({
      character: RICH_CHARACTER,
      catalog: RICH_CATALOG,
      tr: identityTr,
      layout: "compact",
    });
    const { container } = render(<WareSection {...(compact as any)} />);
    const lists = [...container.querySelectorAll(".sheet-list")];
    expect(lists.every((ul) => ul.classList.contains("sheet-list-compact"))).toBe(true);
    expect(lists[0].textContent).toBe("Wired Reflexes R2");
    // the loss stays on the heading
    expect(container.querySelector("h4")!.textContent).toContain("ESS −2");
  });
});

describe("<CombatSection> a limit-based Accuracy", () => {
  it("shows the number and keeps the formula on hover", () => {
    const withBlade = buildSheetData({
      character: {
        ...RICH_CHARACTER,
        derived: {
          ...RICH_CHARACTER.derived,
          weapons: [
            {
              ...(RICH_CHARACTER.derived as any).weapons[0],
              id: "blade",
              name: "Hand Blade",
              accuracy: "6",
              accuracy_formula: "Physical",
              damage: "4P",
              damage_formula: "({STR}+1)P",
            },
          ],
        },
      } as any,
      catalog: RICH_CATALOG,
      tr: identityTr,
      layout: "standard",
    });
    const { container } = render(<CombatSection {...(withBlade as any)} />);
    const cell = container.querySelector('td[title="Physical"]');
    expect(cell?.textContent).toBe("6");
    expect(container.querySelector('td[title="({STR}+1)P"]')?.textContent).toBe("4P");
  });
});
