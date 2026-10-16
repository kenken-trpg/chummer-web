import { render } from "@testing-library/react";
import { textSheet } from "@/lib/character/text-sheet";
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
import { PrintStatBlock } from "@/components/character/sheet/sections/print/PrintStatBlock";
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
import { SheetHeader } from "@/components/character/sheet/SheetHeader";

// A `derived` payload that touches every sheet section with realistic nested
// rows. Rows are hand-shaped only far enough to render, then cast — like the
// rest of the suite's fixtures.

const s = buildSheetData({
  character: RICH_CHARACTER,
  catalog: RICH_CATALOG,
  tr: identityTr,
  layout: "standard",
});

it("shows Confidence's penalty and inactive specialization in visual and text sheets", () => {
  const name = "Exotic Ranged Weapon (Lasers)";
  const data = buildSheetData({
    character: makeCharacter({
      derived: {
        totals: { AGI: 5 } as never,
        skill_totals: { Pistols: 4, [name]: 4 },
        skill_bonus: { Pistols: -2, [name]: -2 },
        skill_specializations: { Pistols: "Revolvers" },
        skill_specializations_disabled: ["Pistols"],
        exotic_skills: [
          {
            id: "lasers",
            skill_name: "Exotic Ranged Weapon",
            label: name,
            extra: "Lasers",
            rating: 4,
            rating_max: 6,
            attribute: "AGI",
            category: "Combat Active",
            options: [],
          },
        ],
      },
    }),
    catalog: makeCatalog({
      skills: {
        groups: [],
        knowledge: [],
        skills: [
          {
            id: "pistols",
            name: "Pistols",
            attribute: "AGI",
            source: "SR5",
            category: "Combat Active",
            skillgroup: null,
          },
        ],
      },
    }),
    tr: identityTr,
    layout: "standard",
  });
  const { container } = render(<SkillsSection {...data} />);
  const rows = [...container.querySelectorAll("tbody tr")];
  expect(rows[0].querySelector("b")?.textContent).toBe("7");
  expect(rows[0].textContent).toContain("Revolvers 専門化の効果なし");
  expect(rows[1].querySelector("b")?.textContent).toBe("7");
  const text = textSheet(data);
  expect(text).toContain("Pistols（Revolvers） 専門化の効果なし 4 [AGI プール 7]");
  expect(text).toContain(`${name} 4 [AGI プール 7]`);
});

it("prints innate qualities and fixed powers with provenance and the kick selection", () => {
  const data = buildSheetData({
    character: makeCharacter({
      metatype: "Centaur",
      derived: {
        qualities: [
          {
            id: "magic",
            name: "Magic Sense",
            category: "Positive",
            source: "RF",
            karma: 0,
            free: true,
            origin: "Metatype",
            origin_name: "Centaur",
            removable: false,
          },
        ],
        metatype_info: {
          name: "Centaur",
          parent: null,
          source: "RF",
          attributes: {},
          powers: [
            {
              id: "natural",
              name: "Natural Weapon",
              source: "SR5",
              page: "399",
              rating: "",
              select: "Kick: DV ({STR} + 2)P, AP +1, +1 Reach",
              origin: "Metatype",
              origin_id: "centaur",
              origin_name: "Centaur",
            },
          ],
        },
      },
    }),
    catalog: makeCatalog(),
    tr: identityTr,
    layout: "print",
  });
  const { container } = render(<QualitiesSection {...data} />);
  expect(container.textContent).toContain("Centaurの生得能力（追加カルマなし）");
  expect(container.textContent).toContain("クリッター・パワー");
  expect(container.textContent).toContain("Kick: DV ({STR} + 2)P, AP +1, +1 Reach");
  expect(container.textContent).toContain("SR5 p.399");
});

const SECTIONS: [string, (p: typeof s) => React.ReactNode, string][] = [
  ["コア", CoreSection, "イニシアティブ"],
  ["技能", SkillsSection, "Pistols"],
  ["知識技能", KnowledgeSection, "Seattle Gangs"],
  ["キャリア", CareerSection, "報酬"],
  ["資質", QualitiesSection, "Ambidextrous"],
  ["アクションDP", ActionDpSection, "強行アクセス"],
  ["戦闘", CombatSection, "Ares Predator V"],
  ["ウェア", WareSection, "Wired Reflexes"],
  ["マトリックス", MatrixSection, "Meta Link"],
  ["魔法", MagicSection, "Manabolt"],
  ["共鳴", ResonanceSection, "Cleaner"],
  ["格闘技", MartialSection, "Krav Maga"],
  ["コンタクト", ContactsSection, "Fixer"],
  ["ヴィークル・ドローン", VehiclesSection, "Ford Americar"],
  ["ドラッグ／毒物", DrugsSection, "Kamikaze"],
  ["SIN／ライセンス", SinSection, "Fake SIN"],
  ["その他装備", MiscGearSection, "Medkit"],
  ["記述", DescriptionSection, "背景メモ"],
];

describe("sheet sections — smoke render", () => {
  it.each(SECTIONS)("%s renders with populated derived data", (_title, Section, marker) => {
    const { container } = render(<Section {...s} />);
    // the section did not collapse to null and shows a representative value
    expect(container.querySelector("section.sheet-section")).not.toBeNull();
    expect(container.textContent).toContain(marker);
  });

  it("the description section prints the player and the GM's notes", () => {
    const sheet = buildSheetData({
      character: {
        ...RICH_CHARACTER,
        player_name: "まんたに",
        game_notes: "CUP 1",
      } as never,
      catalog: RICH_CATALOG,
      tr: identityTr,
      layout: "standard",
    });
    const { container } = render(<DescriptionSection {...sheet} />);
    expect(container.textContent).toContain("まんたに");
    expect(container.textContent).toContain("CUP 1");
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
      } as never,
      catalog: RICH_CATALOG,
      tr: identityTr,
      layout: "standard",
    });
    const { container } = render(<MatrixSection {...withVr} />);
    expect(container.textContent).toContain("冷7+3d6");
    expect(container.textContent).toContain("熱7+4d6");
  });

  it("the core section prints the astral initiative only when there is one", () => {
    const sheet = (astral: unknown) =>
      buildSheetData({
        character: {
          ...RICH_CHARACTER,
          derived: { ...RICH_CHARACTER.derived, astral_initiative: astral },
        } as never,
        catalog: RICH_CATALOG,
        tr: identityTr,
        layout: "standard",
      });
    const awakened = render(<CoreSection {...sheet({ value: 8, dice: 3 })} />);
    expect(awakened.container.textContent).toContain("アストラル・イニシアティブ8+3d6");
    const mundane = render(<CoreSection {...sheet(null)} />);
    expect(mundane.container.textContent).not.toContain("アストラル・イニシアティブ");
  });

  it("the core section names a conditional limit in the reader's language", () => {
    const withMod = buildSheetData({
      character: {
        ...RICH_CHARACTER,
        derived: {
          ...RICH_CHARACTER.derived,
          limit_modifiers: [{ limit: "social", value: 2, condition: "交渉" }],
        },
      } as never,
      catalog: RICH_CATALOG,
      tr: identityTr,
      layout: "standard",
    });
    const { container } = render(<CoreSection {...withMod} />);
    expect(container.textContent).toContain("社交 +2");
    expect(container.textContent).not.toContain("social");
  });

  it("the core section prints movement in metres with the sprint rate", () => {
    const { container } = render(<CoreSection {...s} />);
    expect(container.textContent).toContain("歩6m / 走12m / 全力疾走 +2m/ヒット");
  });

  it("visual, print and text sheets show swimming and omit unavailable flight", () => {
    const data = buildSheetData({
      character: makeCharacter({
        derived: {
          movement: {
            walk: "3",
            run: "12",
            sprint: "4",
            sprint_bonus: 0,
            modes: {
              Swim: {
                rates: { walk: 1, run: 0, sprint: 1 },
                available: true,
                walk: "3.5",
                run: "0",
                sprint: "1",
                sprint_bonus: 0,
              },
              Fly: {
                rates: { walk: 0, run: 0, sprint: 0 },
                available: false,
                walk: "0",
                run: "0",
                sprint: "0",
                sprint_bonus: 0,
              },
            },
          },
        },
      }),
      catalog: RICH_CATALOG,
      tr: identityTr,
      layout: "standard",
    });
    for (const Component of [CoreSection, PrintStatBlock]) {
      const { container, unmount } = render(<Component {...data} />);
      expect(container.textContent).toContain("水泳");
      expect(container.textContent).toContain("3.5m / +1m/ヒット");
      expect(container.textContent).not.toContain("飛行");
      unmount();
    }
    expect(textSheet(data)).toContain("水泳 3.5m / +1m/ヒット");
    expect(textSheet(data)).not.toContain("飛行");
  });

  it("the magic section prints a bound spirit's powers with their action", () => {
    const { container } = render(<MagicSection {...s} />);
    expect(container.textContent).toContain("Engulf（物理・複雑・接触・維持）");
  });

  it("the resonance section prints a sprite's powers the same way", () => {
    const { container } = render(<ResonanceSection {...s} />);
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
      } as never,
      catalog: RICH_CATALOG,
      tr: identityTr,
      layout: "standard",
    });
    const { container } = render(<MagicSection {...withQuickening} />);
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
      const { container } = render(<Section {...empty} />);
      expect(container.querySelector("section.sheet-section")).toBeNull();
    }
  });

  it("the action DP section names the action in Japanese, with its category", () => {
    // Codeslinger's pick is from a list this app keeps, so `translations` has
    // nothing for it and the line read "Matrix: Brute Force"
    const { container } = render(<ActionDpSection {...s} />);
    expect(container.textContent).toContain("Matrix: 強行アクセス");
    expect(container.textContent).toContain("+2");
  });
});

describe("<WareSection> on the compact sheet", () => {
  it("lists ware by name alone", () => {
    const standard = render(<WareSection {...s} />);
    expect(standard.container.querySelector(".sheet-list li")!.textContent).toContain("ESS −2");
    standard.unmount();

    const compact = buildSheetData({
      character: RICH_CHARACTER,
      catalog: RICH_CATALOG,
      tr: identityTr,
      layout: "compact",
    });
    const { container } = render(<WareSection {...compact} />);
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
              ...RICH_CHARACTER.derived!.weapons![0],
              id: "blade",
              name: "Hand Blade",
              accuracy: "6",
              accuracy_formula: "Physical",
              damage: "4P",
              damage_formula: "({STR}+1)P",
            },
          ],
        },
      } as never,
      catalog: RICH_CATALOG,
      tr: identityTr,
      layout: "standard",
    });
    const { container } = render(<CombatSection {...withBlade} />);
    const cell = container.querySelector('td[title="Physical"]');
    expect(cell?.textContent).toBe("6");
    expect(container.querySelector('td[title="({STR}+1)P"]')?.textContent).toBe("4P");
  });
});

describe("quality levels on sheets", () => {
  it.each(["standard", "compact", "text", "print"] as const)(
    "%s groups the level and total karma; text export agrees",
    (layout) => {
      const magic = {
        id: "magic",
        name: "Magic Resistance",
        karma: 6,
        category: "Positive",
        source: "SR5",
        has_levels: true,
      };
      const gremlins = {
        id: "gremlins",
        name: "Gremlins",
        karma: -4,
        category: "Negative",
        source: "SR5",
        has_levels: true,
      };
      const sheet = buildSheetData({
        character: makeCharacter({
          derived: { qualities: [magic, magic, magic, gremlins] as never },
        }),
        catalog: makeCatalog(),
        tr: identityTr,
        layout,
      });
      const { container } = render(<QualitiesSection {...sheet} />);
      expect(container.querySelectorAll("li")).toHaveLength(2);
      expect(container.textContent).toContain("Magic Resistance Lv3");
      expect(container.textContent).toContain("+18K");
      expect(container.textContent).toContain("Gremlins Lv1");
      expect(container.textContent).toContain("-4K");
      const text = textSheet(sheet);
      expect(text.match(/Magic Resistance/g)).toHaveLength(1);
      expect(text).toContain("Magic Resistance Lv3");
      expect(text).toContain("Gremlins Lv1");
    },
  );
});

describe("no English left on the sheet where a translation exists", () => {
  const jaTr = (name: string) =>
    ({ Used: "中古", Alphaware: "アルファウェア", "Wired Reflexes": "ワイヤード・リフレックス" })[
      name
    ] ?? name;
  const sheet = (derived: Record<string, unknown>, character: Record<string, unknown> = {}) =>
    buildSheetData({
      character: {
        ...RICH_CHARACTER,
        ...character,
        derived: { ...RICH_CHARACTER.derived, ...derived },
      } as never,
      catalog: RICH_CATALOG,
      tr: jaTr,
      layout: "standard",
    });

  it("the header and the text sheet name a core talent in Japanese", () => {
    const data = sheet({}, { talent: "Adept" });
    expect(render(<SheetHeader {...data} />).container.textContent).toContain("アデプト");
    expect(textSheet(data)).toContain("アデプト");
  });

  it("ware shows its grade and side translated, and no grade for None", () => {
    const base = RICH_CHARACTER.derived!.cyberware![0];
    const { container } = render(
      <WareSection
        {...sheet({
          cyberware: [
            { ...base, id: "used", grade: "Used", side: "Left" },
            { ...base, id: "alpha", grade: "Alphaware", side: undefined },
          ],
          bioware: [{ ...base, id: "none", name: "Narco", grade: "None" }],
        })}
      />,
    );
    const items = [...container.querySelectorAll("li")].map((li) => li.textContent);
    expect(items[0]).toContain("/ 中古 / 左");
    expect(items[1]).toContain("/ アルファウェア");
    expect(items[2]).not.toContain("None");
  });

  it("the weapon and matrix tables head their columns in Japanese", () => {
    const combat = render(<CombatSection {...s} />).container.textContent;
    expect(combat).toContain("精度");
    expect(combat).not.toContain("Acc");
    const matrix = render(<MatrixSection {...s} />).container.querySelector("thead")!.textContent;
    expect(matrix).toContain("プログラム");
    expect(matrix).toContain("イニシアティブ");
    expect(matrix).not.toMatch(/Prog|M\.CM|M\.Init/);
  });

  it("a Special drain and Chummer's starting rewards read in Japanese", () => {
    const data = sheet(
      {
        spells: [{ ...RICH_CHARACTER.derived!.spells![0], id: "x", dv: "Special" }],
        reward_log: [
          { id: "k", label: "Starting Karma", karma: 7, nuyen: 0 },
          { id: "n", label: "Starting Nuyen", karma: 0, nuyen: 596 },
          { id: "p", label: "Run: Fortune Cookie", karma: 5, nuyen: 0 },
        ],
      },
      { career: true },
    );
    expect(render(<MagicSection {...data} />).container.textContent).toContain("ドレイン 特殊");
    const career = render(<CareerSection {...data} />).container.textContent;
    expect(career).toContain("初期カルマ");
    expect(career).toContain("初期新円");
    // the player's own label is left as written
    expect(career).toContain("Run: Fortune Cookie");
  });

  it("a lifestyle quality's pick reads in Japanese, as its name does", () => {
    const tr = (name: string) =>
      ({ "Grid Subscription": "グリッド契約", "Public Grid": "公共グリッド" })[name] ?? name;
    const data = buildSheetData({
      character: {
        ...RICH_CHARACTER,
        derived: {
          ...RICH_CHARACTER.derived,
          lifestyle: {
            ...(RICH_CHARACTER.derived!.lifestyle ?? { name: "Middle", months: 1 }),
            qualities: [{ name: "Grid Subscription", extra: "Public Grid" }],
          },
        },
      } as never,
      catalog: RICH_CATALOG,
      tr,
      layout: "standard",
    });
    expect(render(<CoreSection {...data} />).container.textContent).toContain(
      "グリッド契約:公共グリッド",
    );
  });
});
