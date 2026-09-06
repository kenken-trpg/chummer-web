import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { FociTab } from "@/components/character/tabs/FociTab";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

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
      catalog={makeCatalog({ foci: [powerFocus] as any })}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      trGroup={identityTr}
      t={(k) => k}
      ui={testUi}
      patch={patch}
      setCharacter={() => {}}
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
});
