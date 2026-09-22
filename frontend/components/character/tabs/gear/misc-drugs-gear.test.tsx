import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { makeCharacter } from "@/tests/fixtures";
import {
  gear,
  drug,
  renderPanel,
  withOptions,
  owning,
  ownedNames,
} from "./misc-drugs-gear.helpers";

describe("<MiscDrugsGear> which rows belong to which tab", () => {
  const rows = [
    gear("g1", "Medkit", { category: "Electronics" }),
    drug("g2", "Novacoke"),
    gear("g3", "Neuro-Stun VIII", { category: "Toxins" }),
    gear("g4", "Cleaner", { category: "Chemicals" }),
    gear("g5", "Berserker BTL", { category: "BTLs" }),
  ];

  it("keeps drugs, toxins, chemicals and BTLs out of the misc tab", () => {
    const { container } = renderPanel(owning(rows), vi.fn(), "misc");
    expect(ownedNames(container)).toEqual(["Medkit"]);
  });

  it("shows exactly those four categories in the drugs tab", () => {
    const { container } = renderPanel(owning(rows), vi.fn(), "drugs");
    expect(ownedNames(container)).toEqual([
      "Novacoke",
      "Neuro-Stun VIII",
      "Cleaner",
      "Berserker BTL",
    ]);
  });

  it("lists a child under its parent rather than as a row of its own", () => {
    const nested = [gear("g1", "Medkit"), gear("g1a", "Medkit Supplies", { parent_id: "g1" })];
    const { container } = renderPanel(owning(nested), vi.fn(), "misc");

    expect(ownedNames(container)).toEqual(["Medkit"]);
    expect(container.textContent).toContain("Medkit Supplies");
  });
});

describe("<MiscDrugsGear> the addiction test", () => {
  it("shows both pools, and only in the drugs tab", () => {
    const misc = renderPanel(owning([]), vi.fn(), "misc");
    expect(misc.container.textContent).not.toContain("中毒抵抗");

    // The fixture is 3s across the board: BOD + WIL and LOG + WIL are both 6.
    const { container } = renderPanel(owning([]), vi.fn(), "drugs");
    expect(container.textContent).toContain("中毒抵抗: 生理 6 ／ 心理 6");
  });

  it("splits the first dose from the test an addict makes", () => {
    const ch = makeCharacter({
      gear: [],
      derived: { gear: [], test_mods: { addiction_physiological_first: 2 } },
    } as never);
    const { container } = renderPanel(ch, vi.fn(), "drugs");

    expect(container.textContent).toContain("生理 8 (中毒後 6) ／ 心理 6");
  });
});

describe("<MiscDrugsGear> a row a quality granted", () => {
  /** Dead SIN's fake SIN: it lives in `derived` only, so there is nothing in
   *  `ch.gear` for a control to edit or a delete button to remove. */
  const granted = [
    gear("granted:0", "Fake SIN", { included: true, granted_by: "Dead SIN", nuyen: 0 }),
  ];

  it("names the quality and offers neither controls nor a delete button", () => {
    const ch = makeCharacter({ gear: [], derived: { gear: granted } } as never);
    const { container } = renderPanel(ch, vi.fn());

    expect(container.textContent).toContain("Dead SIN");
    expect(container.querySelector(".cyber-controls")).toHaveProperty("hidden", true);
    expect(screen.queryByRole("button", { name: "common.delete" })).toBeNull();
  });
});

describe("<MiscDrugsGear> the controls on an owned row", () => {
  const two = () => [
    gear("g1", "Medkit", { rating_max: 6 }),
    gear("g2", "Rope", { rating_max: 6 }),
  ];

  it("quantity changes the row that moved, not both", () => {
    const patch = vi.fn();
    renderPanel(owning(two()), patch);

    fireEvent.change(screen.getAllByRole("spinbutton")[2], { target: { value: "3" } });

    const rows = patch.mock.calls[0][0].gear as { id: string; qty: number }[];
    expect(rows.find((r) => r.id === "g1")?.qty).toBe(1);
    expect(rows.find((r) => r.id === "g2")?.qty).toBe(3);
  });

  it("rating changes the row that moved, not both", () => {
    const patch = vi.fn();
    renderPanel(owning(two()), patch);

    // each row shows quantity then rating
    fireEvent.change(screen.getAllByRole("spinbutton")[3], { target: { value: "5" } });

    const rows = patch.mock.calls[0][0].gear as { id: string; rating: number }[];
    expect(rows.find((r) => r.id === "g1")?.rating).toBe(1);
    expect(rows.find((r) => r.id === "g2")?.rating).toBe(5);
  });

  it("shows no rating box for gear that has no rating", () => {
    renderPanel(owning([gear("g1", "Medkit")]), vi.fn());
    expect(screen.getAllByRole("spinbutton")).toHaveLength(1); // quantity only
  });

  it("picks the skill an autosoft is for, and clearing it stores undefined", () => {
    // "" would be written into the character as a value; the engine reads the
    // absence of the field, not an empty string
    const patch = vi.fn();
    renderPanel(
      owning([
        gear("g1", "Skillsoft", {
          needs_extra: true,
          extra_kind: "skill",
        }),
      ]),
      patch,
      "misc",
      // the choices come from the catalog entry, not the derived row
      withOptions("c-g1", ["Pistols", "Blades"]),
    );

    const select = screen.getByRole("combobox", { name: "Skillsoft: 技能" });
    fireEvent.change(select, { target: { value: "Blades" } });
    expect((patch.mock.calls[0][0].gear as { extra?: string }[])[0].extra).toBe("Blades");

    fireEvent.change(select, { target: { value: "" } });
    expect((patch.mock.calls[1][0].gear as { extra?: string }[])[0].extra).toBeUndefined();
  });

  it("takes a free-text target with the catalog's suggestions behind it", () => {
    const patch = vi.fn();
    const { container } = renderPanel(
      owning([
        gear("g1", "Fake SIN", {
          needs_extra: true,
          extra_kind: "text",
        }),
      ]),
      patch,
      "misc",
      withOptions(
        "c-g1",
        Array.from({ length: 100 }, (_, i) => `Name ${i}`),
      ),
    );

    fireEvent.change(screen.getByPlaceholderText("対象"), { target: { value: "Hans Brackhaus" } });
    expect((patch.mock.calls[0][0].gear as { extra?: string }[])[0].extra).toBe("Hans Brackhaus");

    // the list is capped: a datalist of every name in the book is unusable
    expect(container.querySelectorAll("datalist option")).toHaveLength(80);
  });

  it("deleting a row takes its children with it", () => {
    const patch = vi.fn();
    renderPanel(
      owning([
        gear("g1", "Medkit"),
        gear("g1a", "Supplies", { parent_id: "g1" }),
        gear("g2", "Rope"),
      ]),
      patch,
    );

    fireEvent.click(screen.getAllByRole("button", { name: "削除" })[0]);

    expect((patch.mock.calls[0][0].gear as { id: string }[]).map((r) => r.id)).toEqual(["g2"]);
  });
});

describe("<MiscDrugsGear> drugs", () => {
  const novacoke = (over: Record<string, unknown> = {}) =>
    drug("d1", "Novacoke", {
      drug_effect: [
        { key: "engine.drugEffect.attribute", params: { name: "CHA", value: "+1" } },
        { key: "engine.drugEffect.attribute", params: { name: "REA", value: "+1" } },
      ],
      drug_vectors: ["Ingestion", "Inhalation"],
      drug_speed: "Immediate",
      ...over,
    });

  it("prints the effect, the vectors and the onset", () => {
    const { container } = renderPanel(owning([novacoke()]), vi.fn(), "drugs");

    expect(container.textContent).toContain("効果: CHA +1 / REA +1");
    expect(container.textContent).toContain("経路 Ingestion・Inhalation");
    expect(container.textContent).toContain("発現 Immediate");
  });

  it("offers no in-use toggle for a drug with no effect to apply", () => {
    renderPanel(owning([drug("d1", "Novacoke")]), vi.fn(), "drugs");
    expect(screen.queryByRole("checkbox")).toBeNull();
  });

  it("reads the in-use flag off the character, not the derived row", () => {
    // `derived` does not carry `active` back, so a checkbox bound to it would
    // silently snap off again after every patch
    const rows = [novacoke()];
    const ch = makeCharacter({
      gear: [{ ...rows[0], active: true }],
      derived: { gear: rows },
    } as never);
    renderPanel(ch, vi.fn(), "drugs");

    expect((screen.getByRole("checkbox") as HTMLInputElement).checked).toBe(true);
  });

  it("toggling one drug leaves the others alone", () => {
    const patch = vi.fn();
    renderPanel(owning([novacoke(), novacoke({ id: "d2", name: "Jazz" })]), patch, "drugs");

    fireEvent.click(screen.getAllByRole("checkbox")[1]);

    const rows = patch.mock.calls[0][0].gear as { id: string; active?: boolean }[];
    expect(rows.find((r) => r.id === "d1")?.active).toBeUndefined();
    expect(rows.find((r) => r.id === "d2")?.active).toBe(true);
  });
});
