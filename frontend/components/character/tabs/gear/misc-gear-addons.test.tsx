import { fireEvent, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { makeCatalog } from "@/tests/fixtures";
import { gear, drug, renderPanel, owning } from "./misc-drugs-gear.helpers";

describe("<MiscDrugsGear> the per-row addon picker", () => {
  const catalog = () =>
    makeCatalog({
      gear: [
        {
          id: "a-supplies",
          name: "Medkit Supplies",
          category: "Medkit Add-ons",
          cost: "50",
          minrating: 2,
          source: "SR5",
          requireparent: true,
        },
        {
          id: "a-stab",
          name: "Stabilisation Unit",
          category: "Medkit Add-ons",
          cost: "250",
          source: "SR5",
          requireparent: true,
        },
        // a supplement add-on: hidden until the search box has something in it
        {
          id: "a-sg",
          name: "Trauma Patch",
          category: "Medkit Add-ons",
          cost: "500",
          source: "SG",
          requireparent: true,
        },
        // fits a different parent's categories
        {
          id: "a-other",
          name: "Rope Hook",
          category: "Rope Add-ons",
          cost: "20",
          source: "SR5",
          requireparent: true,
        },
      ],
    } as never);

  const medkit = (over: Record<string, unknown> = {}) =>
    gear("g1", "Medkit", { addoncategories: ["Medkit Add-ons", "Custom"], ...over });

  const addonOptions = () =>
    [...screen.getByRole("combobox", { name: "Medkit: 追加ギア" }).querySelectorAll("option")].map(
      (o) => o.textContent,
    );

  it("offers the add-ons this parent takes, minus what it already has", () => {
    renderPanel(
      owning([
        medkit(),
        gear("g1a", "Medkit Supplies", { gear_id: "a-supplies", parent_id: "g1" }),
      ]),
      vi.fn(),
      "misc",
      catalog(),
    );
    expect(addonOptions()).toEqual([
      "追加ギア",
      "Stabilisation Unit (250¥)",
      "Trauma Patch (500¥)",
    ]);
  });

  // "minus what it already has" is right for a Vision Magnification and wrong
  // for a Fake License: a Fake SIN carries one per licensed thing, and each is
  // a different item. Hiding the second one made them unbuyable past the first.
  it("keeps offering an add-on that names what it is for", () => {
    const licenses = makeCatalog({
      gear: [
        {
          id: "a-license",
          name: "Fake License",
          category: "Medkit Add-ons",
          cost: "200",
          source: "SR5",
          requireparent: true,
          needs_extra: true,
          extra_kind: "text",
        },
      ],
    } as never);
    renderPanel(
      owning([
        medkit(),
        gear("g1a", "Fake License", { gear_id: "a-license", parent_id: "g1", extra: "運転" }),
      ]),
      vi.fn(),
      "misc",
      licenses,
    );

    expect(addonOptions()).toContain("Fake License (200¥)");
  });

  // This select used to change with the *catalog search box* further down the
  // panel — two unrelated controls wired together, because the search box was
  // the only way past the hard-coded `source === "SR5"`.
  it("does not change with the catalog search box", () => {
    renderPanel(owning([medkit()]), vi.fn(), "misc", catalog());
    const before = addonOptions();

    fireEvent.change(screen.getByPlaceholderText("ギアを検索"), { target: { value: "trauma" } });

    expect(addonOptions()).toEqual(before);
  });

  it("drops the add-ons whose book the settings turned off", () => {
    renderPanel(owning([medkit()]), vi.fn(), "misc", catalog(), ["SR5"]);
    expect(addonOptions()).not.toContain("Trauma Patch (500¥)");
  });

  it("installs the add-on at its own minimum rating, parented to the row", () => {
    const patch = vi.fn();
    renderPanel(owning([medkit(), gear("g2", "Rope")]), patch, "misc", catalog());

    const select = screen.getByRole("combobox", { name: "Medkit: 追加ギア" });
    fireEvent.change(select, { target: { value: "a-supplies" } });
    fireEvent.click(
      within(select.parentElement as HTMLElement).getByRole("button", { name: "装着" }),
    );

    const rows = patch.mock.calls[0][0].gear as Record<string, unknown>[];
    expect(rows.at(-1)).toEqual({
      gear_id: "a-supplies",
      rating: 2,
      parent_id: "g1",
      extra: undefined,
    });
  });

  it("carries the add-on's own target into the installed row", () => {
    // the target select only appears once an add-on that needs one is chosen
    const withExtra = makeCatalog({
      gear: [
        {
          id: "a-soft",
          name: "Activesoft",
          category: "Medkit Add-ons",
          cost: "100",
          source: "SR5",
          requireparent: true,
          extra_kind: "skill",
          extra_options: ["Pistols", "Blades"],
        },
      ],
    } as never);
    const patch = vi.fn();
    renderPanel(owning([medkit()]), patch, "misc", withExtra);

    const select = screen.getByRole("combobox", { name: "Medkit: 追加ギア" });
    expect(screen.queryByRole("combobox", { name: "Medkit: 対象" })).toBeNull();

    fireEvent.change(select, { target: { value: "a-soft" } });
    fireEvent.change(screen.getByRole("combobox", { name: "Medkit: 対象" }), {
      target: { value: "Blades" },
    });
    fireEvent.click(
      within(select.parentElement as HTMLElement).getByRole("button", { name: "装着" }),
    );

    expect((patch.mock.calls[0][0].gear as { extra?: string }[]).at(-1)?.extra).toBe("Blades");
  });

  it("calls the picker グレード／追加 in the drugs tab", () => {
    const grades = makeCatalog({
      gear: [
        {
          id: "a-grade",
          name: "Designer",
          category: "Drug Grades",
          cost: "0",
          source: "SG",
          requireparent: true,
        },
      ],
    } as never);
    renderPanel(
      owning([drug("d1", "Novacoke", { addoncategories: ["Drug Grades"] })]),
      vi.fn(),
      "drugs",
      grades,
    );

    // a Drug Grade is offered without searching even though it is not SR5
    const select = screen.getByRole("combobox", { name: "Novacoke: グレード／追加" });
    expect([...select.querySelectorAll("option")].map((o) => o.textContent)).toEqual([
      "グレード／追加",
      "Designer (0¥)",
    ]);
  });

  it("removing a child keeps its siblings, and an included one cannot be removed", () => {
    const patch = vi.fn();
    renderPanel(
      owning([
        medkit(),
        gear("g1a", "Supplies", { parent_id: "g1" }),
        gear("g1b", "Bundled Case", { parent_id: "g1", included: true }),
      ]),
      patch,
      "misc",
      catalog(),
    );

    const removes = screen.getAllByRole("button", { name: "外す" });
    expect(removes).toHaveLength(1); // the included one has none

    fireEvent.click(removes[0]);
    expect((patch.mock.calls[0][0].gear as { id: string }[]).map((r) => r.id)).toEqual([
      "g1",
      "g1b",
    ]);
  });

  it("removing a child takes whatever is plugged into it", () => {
    // the panel only renders direct children, so a grandchild is invisible
    // here -- and would be left in `gear` pointing at a row that is gone
    const patch = vi.fn();
    renderPanel(
      owning([
        medkit(),
        gear("g1a", "Supplies", { parent_id: "g1" }),
        gear("g1a1", "Refill", { parent_id: "g1a" }),
      ]),
      patch,
      "misc",
      catalog(),
    );

    fireEvent.click(screen.getByRole("button", { name: "外す" }));

    expect((patch.mock.calls[0][0].gear as { id: string }[]).map((r) => r.id)).toEqual(["g1"]);
  });

  it("a child's rating changes that child only", () => {
    const patch = vi.fn();
    renderPanel(
      owning([
        medkit(),
        gear("g1a", "Supplies", { parent_id: "g1", rating_max: 6 }),
        gear("g1b", "Stabiliser", { parent_id: "g1", rating_max: 6 }),
      ]),
      patch,
      "misc",
      catalog(),
    );

    // spinbutton 0 is the parent's quantity
    fireEvent.change(screen.getAllByRole("spinbutton")[2], { target: { value: "4" } });

    const rows = patch.mock.calls[0][0].gear as { id: string; rating: number }[];
    expect(rows.find((r) => r.id === "g1a")?.rating).toBe(1);
    expect(rows.find((r) => r.id === "g1b")?.rating).toBe(4);
  });
});
