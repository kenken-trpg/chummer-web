import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { WareHeldGear } from "@/components/character/WareHeldGear";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";
import type { InstalledWare } from "@/lib/types";

const housing = {
  id: "head",
  ware_id: "commlink-ware",
  name: "Commlink",
  category: "Headware",
  rating: 1,
  grade: "Standard",
  wireless: true,
  essence: 0.2,
  nuyen: 2000,
  allow_gear: ["Commlinks"],
} as InstalledWare;

const catalog = makeCatalog({
  commlinks: [{ id: "ikon", name: "Hermes Ikon", category: "Commlinks", cost: "3000" }],
} as never);

function renderHeld(implanted: boolean, patch = vi.fn()) {
  const ch = makeCharacter({
    commlinks: implanted ? [{ id: "link", gear_id: "ikon", parent_id: "head" }] : [],
    derived: {
      commlinks: implanted
        ? [{ id: "link", gear_id: "ikon", name: "Hermes Ikon", parent_id: "head" }]
        : [],
    },
  } as never);
  render(
    <WareHeldGear
      item={housing}
      catalog={catalog}
      character={ch}
      tr={identityTr}
      ui={testUi}
      patch={patch}
    />,
  );
  return patch;
}

describe("<WareHeldGear> with a headware Commlink", () => {
  it("puts a commlink in from the commlink list", () => {
    const patch = renderHeld(false);
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "ikon" } });
    fireEvent.click(screen.getByRole("button", { name: "Commlink: 入れる" }));
    expect(patch).toHaveBeenCalledWith({
      commlinks: [{ gear_id: "ikon", parent_id: "head", rating: 1, qty: 1 }],
    });
  });

  it("lists the implanted commlink and takes it out, offering no second one", () => {
    const patch = renderHeld(true);
    expect(screen.getByText("Hermes Ikon")).toBeTruthy();
    expect(screen.queryByRole("combobox")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "取り出す" }));
    expect(patch).toHaveBeenCalledWith({
      commlinks: [{ id: "link", gear_id: "ikon", parent_id: null }],
    });
  });
});
