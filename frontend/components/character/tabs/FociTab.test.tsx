import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { FociTab } from "@/components/character/tabs/FociTab";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";

const powerFocus = {
  id: "pf",
  name: "Power Focus",
  cost: "F*18000",
  source: "SR5",
  effect: "",
  needs_weapon: false,
};

function renderTab(patch: (b: Record<string, unknown>) => void = () => {}) {
  const ch = makeCharacter();
  return render(
    <FociTab
      {...panelProps(ch, { catalog: makeCatalog({ foci: [powerFocus] as never }), patch })}
    />,
  );
}

describe("<FociTab>", () => {
  it("renders the focus-limit line and the search box", () => {
    renderTab();
    expect(screen.getByText(/同時 0\//)).toBeDefined();
    expect(screen.getByPlaceholderText("収束具を検索")).toBeDefined();
  });

  it("buys and crafts a focus via patch", () => {
    const patch = vi.fn();
    renderTab(patch);
    fireEvent.click(screen.getByRole("button", { name: "購入" }));
    expect(patch).toHaveBeenCalledWith({
      foci: [{ gear_id: "pf", force: 1, crafted: false }],
    });
    fireEvent.click(screen.getByRole("button", { name: "クラフト" }));
    expect(patch).toHaveBeenCalledWith({
      foci: [{ gear_id: "pf", force: 1, crafted: true, formula_bought: true }],
    });
  });

  /**
   * `foci.note` prints "同時 0/6 ・ Force合計 0/12" without saying where either
   * ceiling comes from, or that going over the Force one stops every focus
   * working — a silent loss the numbers alone never explain.
   */
  it("explains where the two ceilings come from", () => {
    renderTab();
    const button = screen.getByRole("button", { name: "収束具の上限 の説明" });
    const tip = screen.getByRole("tooltip", { hidden: true });
    expect(button.getAttribute("aria-describedby")).toBe(tip.id);
    expect(tip.textContent).toContain("同時に結合できる数は魔力まで");
    expect(tip.textContent).toContain("結合カルマは Force と同数");
  });
});
