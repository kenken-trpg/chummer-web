import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { makeCatalog, makeCharacter } from "@/tests/fixtures";
import { gear, renderPanel, owning } from "./misc-drugs-gear.helpers";

describe("<MiscDrugsGear> the catalog picker", () => {
  const catalog = () =>
    makeCatalog({
      gear: [
        { id: "c-medkit", name: "Medkit", category: "Biotech", cost: "250", source: "SR5" },
        { id: "c-rope", name: "Rope", category: "Survival Gear", cost: "50", source: "SR5" },
        { id: "c-sg", name: "Micro Drone", category: "Survival Gear", cost: "900", source: "SG" },
        { id: "c-nova", name: "Novacoke", category: "Drugs", cost: "10", source: "SR5" },
        {
          id: "c-part",
          name: "Medkit Supplies",
          category: "Biotech",
          cost: "50",
          source: "SR5",
          requireparent: true,
        },
      ],
    } as never);

  const offered = () =>
    [...document.querySelectorAll(".quality-list .quality-item b")].map((el) => el.textContent);

  it("leaves out drugs and parts that need a parent", () => {
    renderPanel(owning([]), vi.fn(), "misc", catalog());
    // supplements are on the list now: narrowing an idle list to SR5 under
    // the settings' own book list meant enabling a book changed nothing
    expect(offered()).toEqual(["Medkit", "Rope", "Micro Drone"]);
  });

  it("a search reaches supplements and matches the category too", () => {
    renderPanel(owning([]), vi.fn(), "misc", catalog());

    fireEvent.change(screen.getByPlaceholderText("ギアを検索"), { target: { value: "survival" } });
    expect(offered()).toEqual(["Rope", "Micro Drone"]);
  });

  it("builds its category tabs from the gear on offer", () => {
    const { container } = renderPanel(owning([]), vi.fn(), "misc", catalog());

    const tabs = [...container.querySelectorAll(".option-row .tab")].map((el) => el.textContent);
    // sorted, no drug categories, nothing that only exists as a child part
    expect(tabs).toEqual(["すべて", "Biotech", "Survival Gear"]);

    fireEvent.click(screen.getByRole("button", { name: "Biotech" }));
    expect(offered()).toEqual(["Medkit"]);
  });

  it("buys at the catalog minimum rating, with the chosen target", () => {
    const withExtra = makeCatalog({
      gear: [
        {
          id: "c-soft",
          name: "Activesoft",
          category: "Software",
          cost: "1000",
          source: "SR5",
          minrating: 3,
          needs_extra: true,
          extra_kind: "skill",
          extra_options: ["Pistols"],
        },
      ],
    } as never);
    const patch = vi.fn();
    renderPanel(owning([]), patch, "misc", withExtra);

    fireEvent.change(screen.getByRole("combobox", { name: "Activesoft: 技能" }), {
      target: { value: "Pistols" },
    });
    fireEvent.click(screen.getByRole("button", { name: "購入" }));

    expect(patch.mock.calls[0][0].gear).toEqual([
      { gear_id: "c-soft", rating: 3, extra: "Pistols" },
    ]);
  });

  it("the drugs tab has fixed category tabs and prefers catalog.drugs", () => {
    const drugs = makeCatalog({
      drugs: [
        {
          id: "d-nova",
          name: "Novacoke",
          category: "Drugs",
          cost: "10",
          source: "SR5",
          effect: [{ key: "engine.drugEffect.attribute", params: { name: "CHA", value: "+1" } }],
          vectors: ["Ingestion"],
        },
      ],
      // the fallback list, which must not be the one used
      gear: [{ id: "g-jazz", name: "Jazz", category: "Drugs", cost: "75", source: "SR5" }],
    } as never);
    const { container } = renderPanel(owning([]), vi.fn(), "drugs", drugs);

    const tabs = [...container.querySelectorAll(".option-row .tab")].map((el) => el.textContent);
    expect(tabs).toEqual(["すべて", "BTLs", "Chemicals", "Drugs", "Toxins"]);
    expect(offered()).toEqual(["Novacoke"]);
    expect(container.textContent).toContain("効果: CHA +1");
  });

  it("buying a drug sends rating 1 and nothing else", () => {
    const drugs = makeCatalog({
      drugs: [{ id: "d-nova", name: "Novacoke", category: "Drugs", cost: "10", source: "SR5" }],
    } as never);
    const patch = vi.fn();
    renderPanel(owning([]), patch, "drugs", drugs);

    fireEvent.click(screen.getByRole("button", { name: "購入" }));

    expect(patch.mock.calls[0][0].gear).toEqual([{ gear_id: "d-nova", rating: 1 }]);
  });
});

describe("<MiscDrugsGear> an item the player prices", () => {
  it("offers a price within its range, and a Custom Item a name of its own", () => {
    const patch = vi.fn();
    const ch = makeCharacter({
      gear: [{ id: "g1", gear_id: "c-g1", cost: 100 }] as never,
      derived: {
        gear: [
          gear("g1", "Custom Item", {
            category: "Custom",
            label: "Custom Item",
            cost_range: [0, 1000000],
            custom_name: "",
          }),
        ],
      } as never,
    });
    renderPanel(ch, patch);
    const price = screen.getByRole("spinbutton", { name: /Custom Item: 値段/ }) as HTMLInputElement;
    expect(price.max).toBe("1000000");
    expect(price.value).toBe("100");
    fireEvent.change(price, { target: { value: "2500" } });
    expect(patch).toHaveBeenCalledWith({ gear: [{ id: "g1", gear_id: "c-g1", cost: 2500 }] });
    fireEvent.change(screen.getByPlaceholderText("Custom Item"), { target: { value: "Rosary" } });
    expect(patch).toHaveBeenLastCalledWith({
      gear: [{ id: "g1", gear_id: "c-g1", cost: 100, name: "Rosary" }],
    });
  });

  it("shows no price for an item with a fixed one", () => {
    renderPanel(makeCharacter({ derived: { gear: [gear("g1", "Medkit")] } as never }), vi.fn());
    expect(screen.queryByRole("spinbutton", { name: /値段/ })).toBeNull();
  });
});
