import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { WeaponGear } from "@/components/character/tabs/gear/WeaponGear";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";

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
      {...panelProps(ch, {
        catalog: over.catalog ?? makeCatalog({ weapons: [ak, knife] as never }),
        patch: over.patch ?? (() => {}),
      })}
    />,
  );
}

describe("<WeaponGear>", () => {
  it("labels an imported free weapon while keeping its delete action", () => {
    const patch = vi.fn();
    const ch = makeCharacter({
      weapons: [{ id: "free-ak", weapon_id: "ak", qty: 1, free: true }],
      derived: {
        weapons: [
          {
            id: "free-ak",
            weapon_id: "ak",
            name: "AK-97",
            category: "Assault Rifles",
            type: "Ranged",
            accuracy: "5",
            reach: "0",
            damage: "10P",
            ap: "-2",
            mode: "SA/BF/FA",
            ammo: "38(c)",
            qty: 1,
            nuyen: 0,
            free: true,
          },
        ],
      },
    });
    render(<WeaponGear {...panelProps(ch, { patch })} />);
    expect(screen.getByText(/無料購入/)).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "削除" }));
    expect(patch).toHaveBeenCalledWith({ weapons: [], weapon_accessories: [], gear: [] });
  });

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
