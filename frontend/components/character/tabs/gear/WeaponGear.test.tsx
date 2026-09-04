import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { WeaponGear } from "@/components/character/tabs/gear/WeaponGear";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

const ak = {
  id: "ak",
  name: "AK-97",
  category: "Assault Rifles",
  cost: 950,
  avail: "4R",
  source: "SR5",
};
const knife = { ...ak, id: "knife", name: "Combat Knife", category: "Blades", cost: 300 };

function renderTab(
  over: {
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter();
  return render(
    <WeaponGear
      catalog={over.catalog ?? makeCatalog({ weapons: [ak, knife] as any })}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      t={(k) => k}
      ui={testUi}
      patch={over.patch ?? (() => {})}
      setCharacter={() => {}}
    />,
  );
}

describe("<WeaponGear>", () => {
  it("renders the search box and category tabs from the catalog", () => {
    renderTab();
    expect(screen.getByPlaceholderText("武器を検索")).toBeDefined();
    expect(screen.getByRole("button", { name: "すべて" })).toBeDefined();
    expect(screen.getByRole("button", { name: "Assault Rifles" })).toBeDefined();
  });

  it("buys a weapon via patch", () => {
    const patch = vi.fn();
    renderTab({ patch });
    const row = [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
      el.textContent?.includes("AK-97"),
    )!;
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith({ weapons: [{ weapon_id: "ak", qty: 1 }] });
  });

  it("filters the catalog by search", () => {
    renderTab();
    fireEvent.change(screen.getByPlaceholderText("武器を検索"), { target: { value: "knife" } });
    const names = [...document.querySelectorAll(".quality-list .quality-item b")].map(
      (b) => b.textContent,
    );
    expect(names).toEqual(["Combat Knife"]);
  });
});
