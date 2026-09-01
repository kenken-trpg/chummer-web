import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { PriorityTab } from "@/components/character/tabs/PriorityTab";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";

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
      t={(k) => k}
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
    expect(screen.getByRole("button", { name: "Priority" }).className).toContain("selected");
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
