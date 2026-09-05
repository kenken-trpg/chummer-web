import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { PriorityTab } from "@/components/character/tabs/PriorityTab";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

const CAT_KEYS = ["Heritage", "Attributes", "Talent", "Skills", "Resources"];
const LETTERS = ["A", "B", "C", "D", "E"];

const fullTable: any = {};
for (const k of CAT_KEYS) {
  fullTable[k] = {};
  for (const l of LETTERS) {
    fullTable[k][l] = {
      name: `${l} - ${k}`,
      metatypes: k === "Heritage" ? [{ name: "Human", special: 0, variants: [] }] : [],
      talents:
        k === "Talent"
          ? l === "E"
            ? [{ name: "Mundane", label: "Mundane", value: 0 }]
            : [
                { name: "Mundane", label: "Mundane", value: 0 },
                { name: "Magician", label: "Magician", value: 5 },
              ]
          : [],
    };
  }
}

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(
    <PriorityTab
      catalog={makeCatalog({ priority_table: fullTable })}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      trGroup={identityTr}
      t={(k) => k}
      ui={testUi}
      patch={over.patch ?? (() => {})}
      setCharacter={() => {}}
    />,
  );
}

const rows = () => [...document.querySelectorAll("tbody tr")];
const cell = (row: number, letter: number) =>
  rows()[row].querySelectorAll("td button")[letter] as HTMLButtonElement;

describe("<PriorityTab>", () => {
  it("renders in Priority mode with the 5×5 grid and its help line", () => {
    renderTab();
    expect(screen.getByRole("button", { name: "優先度" }).className).toContain("selected");
    expect(rows()).toHaveLength(5);
    expect(rows()[0].querySelectorAll("td button")).toHaveLength(5);
    expect(screen.getByText(/A〜E は各1回/)).toBeDefined();
  });

  it("switches build method via the header buttons", () => {
    const patch = vi.fn();
    renderTab({ patch });
    fireEvent.click(screen.getByRole("button", { name: "Sum to Ten" }));
    expect(patch).toHaveBeenCalledWith({ build_method: "SumToTen" });
    fireEvent.click(screen.getByRole("button", { name: "Karma" }));
    expect(patch).toHaveBeenCalledWith({ build_method: "Karma", talent: "Mundane" });
  });

  it("marks the character's current letters and swaps on a collision", () => {
    const patch = vi.fn();
    // defaults: Heritage E, Attributes C, Talent E, Skills B, Resources D
    renderTab({ patch });
    expect(cell(0, 4).className).toContain("selected"); // Heritage = E
    fireEvent.click(cell(0, 2)); // give Heritage the C that Attributes holds
    const next = (patch.mock.calls[0][0] as any).priorities;
    expect(next.Heritage).toBe("C");
    expect(next.Attributes).toBe("E"); // took Heritage's old letter
  });

  it("a Talent-row click also resolves the talent for that letter", () => {
    const patch = vi.fn();
    renderTab({ patch });
    fireEvent.click(cell(2, 0)); // Talent = A
    const call = patch.mock.calls[0][0] as any;
    expect(call.priorities.Talent).toBe("A");
    expect(call.talent).toBe("Magician"); // Mundane not offered at A -> first option
  });

  it("shows the Sum-to-Ten readout when that method is active", () => {
    renderTab({
      character: { build_method: "SumToTen", derived: { sum_to_ten: { used: 8, max: 10 } as any } },
    });
    expect(screen.getByText(/合計 8\/10/)).toBeDefined();
  });
});

describe("<PriorityTab> the table reads in Japanese", () => {
  /** The real cell names, as they come out of the vendored Chummer data. */
  const realTable: any = {
    Heritage: {
      A: { name: "A - Any metatype", metatypes: [], talents: [] },
      B: { name: "B - Any metatype", metatypes: [], talents: [] },
      C: { name: "C - Human, Dwarf, Elf, Ork, or A.I.", metatypes: [], talents: [] },
      D: { name: "D - Human or Elf", metatypes: [], talents: [] },
      E: { name: "E - Human", metatypes: [], talents: [] },
    },
    Attributes: {
      A: { name: "A - 24 (12) Attributes", metatypes: [], talents: [] },
      B: { name: "B - 20 (10) Attributes", metatypes: [], talents: [] },
      C: { name: "C - 16 (8) Attributes", metatypes: [], talents: [] },
      D: { name: "D - 14 (7) Attributes", metatypes: [], talents: [] },
      E: { name: "E - 12 (6) Attributes", metatypes: [], talents: [] },
    },
    Talent: {
      A: { name: "A - Magician or Technomancer", metatypes: [], talents: [] },
      B: { name: "B - Adept, Magician, or Technomancer", metatypes: [], talents: [] },
      C: { name: "C - Adept, Magician, or Technomancer", metatypes: [], talents: [] },
      D: { name: "D - Adept or Aspected Magician", metatypes: [], talents: [] },
      E: { name: "E - Mundane", metatypes: [], talents: [] },
    },
    Skills: {
      A: { name: "A - 46 Skills/10 Skill Groups", metatypes: [], talents: [] },
      B: { name: "B - 36 Skills/5 Skill Groups", metatypes: [], talents: [] },
      C: { name: "C - 28 Skills/2 Skill Groups", metatypes: [], talents: [] },
      D: { name: "D - 22 Skills/0 Skill Groups", metatypes: [], talents: [] },
      E: { name: "E - 18 Skills/0 Skill Groups", metatypes: [], talents: [] },
    },
    Resources: {
      A: { name: "A - 450,000\u00a5", metatypes: [], talents: [] },
      B: { name: "B - 275,000\u00a5", metatypes: [], talents: [] },
      C: { name: "C - 140,000\u00a5", metatypes: [], talents: [] },
      D: { name: "D - 50,000\u00a5", metatypes: [], talents: [] },
      E: { name: "E - 6,000\u00a5", metatypes: [], talents: [] },
    },
  };

  function renderReal() {
    const ch = makeCharacter();
    return render(
      <PriorityTab
        catalog={makeCatalog({ priority_table: realTable })}
        character={ch}
        d={ch.derived}
        tr={identityTr}
        trGroup={identityTr}
        t={(k) => k}
        ui={testUi}
        patch={() => {}}
        setCharacter={() => {}}
      />,
    );
  }

  it("localises every cell the vendored table ships", () => {
    const { container } = renderReal();
    const cells = [...container.querySelectorAll("tbody td button")].map((b) => b.textContent);
    expect(cells).toEqual([
      "ヒューマン, エルフ, ドワーフ, オーク, トロール",
      "ヒューマン, エルフ, ドワーフ, オーク, トロール",
      "ヒューマン, ドワーフ, エルフ, オーク, or A.I.",
      "ヒューマン or エルフ",
      "ヒューマン",
      "24 (12) 能力値",
      "20 (10) 能力値",
      "16 (8) 能力値",
      "14 (7) 能力値",
      "12 (6) 能力値",
      "魔法使いまたはミスティックアデプト or テクノマンサー",
      "アデプト, 魔法使いまたはミスティックアデプト or テクノマンサー",
      "アデプト, 魔法使いまたはミスティックアデプト or テクノマンサー",
      "アデプト or 偏位魔法使い",
      // not in the requested list; still English upstream
      "Mundane",
      "46 技能/10 技能グループ",
      "36 技能/5 技能グループ",
      "28 技能/2 技能グループ",
      "22 技能/0 技能グループ",
      "18 技能/0 技能グループ",
      "450,000\u00a5",
      "275,000\u00a5",
      "140,000\u00a5",
      "50,000\u00a5",
      "6,000\u00a5",
    ]);
  });

  it("heads the metatype row with メタタイプ", () => {
    const { container } = renderReal();
    expect([...container.querySelectorAll("td.rowhead")].map((el) => el.textContent)).toEqual([
      "メタタイプ",
      "能力値",
      "魔力/共振力",
      "技能",
      "資金",
    ]);
  });
});
