import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { SpellsTab } from "@/components/character/tabs/SpellsTab";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

const fireball = {
  id: "fb",
  name: "Fireball",
  category: "Combat",
  dv: "F-3",
  kind: "spell",
  source: "SR5",
};
const rite = {
  id: "rite",
  name: "Circle of Healing",
  category: "Health",
  dv: "F-2",
  kind: "ritual",
  source: "SR5",
};
const traditions = [{ id: "hermetic", name: "Hermetic", drain_attrs: ["WIL", "LOG"] }];

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(
    <SpellsTab
      catalog={
        over.catalog ??
        makeCatalog({ spells: [fireball, rite] as any, traditions: traditions as any })
      }
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

describe("<SpellsTab>", () => {
  it("renders the free-slot line, tradition select and kind tabs", () => {
    renderTab();
    expect(screen.getByText(/無料 0\/0/)).toBeDefined();
    expect(screen.getByRole("combobox")).toBeDefined();
    for (const label of ["すべて", "呪文", "儀式", "エンチャント"]) {
      expect(screen.getByRole("button", { name: label })).toBeDefined();
    }
  });

  it("sets the tradition through patch", () => {
    const patch = vi.fn();
    renderTab({ patch });
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "hermetic" } });
    expect(patch).toHaveBeenCalledWith({ tradition_id: "hermetic" });
  });

  it("adds a spell from the catalog via patch", () => {
    const patch = vi.fn();
    renderTab({ patch });
    const row = [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
      el.textContent?.includes("Fireball"),
    )!;
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith({ spells: [{ spell_id: "fb" }] });
  });

  it("filters the catalog by the kind tabs", () => {
    renderTab();
    fireEvent.click(screen.getByRole("button", { name: "儀式" }));
    const names = [...document.querySelectorAll(".quality-list .quality-item b")].map(
      (b) => b.textContent,
    );
    expect(names).toEqual(["Circle of Healing"]);
  });
});
