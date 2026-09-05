import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Character } from "@/lib/types";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";
import { MiscDrugsGear } from "./MiscDrugsGear";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * One component, two tabs. `mode` decides whether a row belongs here at all,
 * and the test for it is a category check written out three times over —
 * `Drugs`, `Toxins`, `Chemicals` — in the owned list, in the category tabs
 * and in each picker. Get one of the three wrong and a drug is invisible in
 * both tabs, or shows up in both.
 *
 * The rest is the gear tree: `d.gear` is flat, parentage lives in
 * `parent_id`, and every control maps or filters that one list. Two other
 * things here read from `ch.gear` rather than `d.gear` on purpose — the drug
 * "in use" checkbox, because the derived row does not carry the flag back —
 * and that distinction is invisible on screen.
 *
 * `gear-owned.test.tsx` covers the plain nesting case in misc mode. This
 * covers the mode split, the pickers, and the "extra" plumbing that appears
 * in four separate places with four separate pieces of state.
 */

const gear = (id: string, name: string, over: Record<string, unknown> = {}) => ({
  id,
  name,
  gear_id: `c-${id}`,
  category: "Electronics",
  qty: 1,
  rating: 1,
  rating_max: 0,
  nuyen: 100,
  source: "SR5",
  included: false,
  ...over,
});

const drug = (id: string, name: string, over: Record<string, unknown> = {}) =>
  gear(id, name, { category: "Drugs", is_drug: true, ...over });

function renderPanel(
  ch: Character,
  patch: (b: Record<string, unknown>) => void,
  mode: "misc" | "drugs" = "misc",
  catalog = makeCatalog(),
) {
  return render(
    <MiscDrugsGear
      catalog={catalog}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      trGroup={identityTr}
      t={((k: string) => k) as any}
      ui={testUi}
      patch={patch as any}
      setCharacter={() => {}}
      mode={mode}
    />,
  );
}

/** A character owning these gear rows, mirrored into `derived`. */
function owning(rows: Record<string, unknown>[], over: Record<string, unknown> = {}): Character {
  return makeCharacter({ gear: rows, ...over, derived: { gear: rows } } as any);
}

const ownedNames = (container: HTMLElement) =>
  [...container.querySelectorAll(".cyber-item > div > b")].map((el) => el.textContent);

describe("<MiscDrugsGear> which rows belong to which tab", () => {
  const rows = [
    gear("g1", "Medkit", { category: "Electronics" }),
    drug("g2", "Novacoke"),
    gear("g3", "Neuro-Stun VIII", { category: "Toxins" }),
    gear("g4", "Cleaner", { category: "Chemicals" }),
  ];

  it("keeps drugs, toxins and chemicals out of the misc tab", () => {
    const { container } = renderPanel(owning(rows), vi.fn(), "misc");
    expect(ownedNames(container)).toEqual(["Medkit"]);
  });

  it("shows exactly those three categories in the drugs tab", () => {
    const { container } = renderPanel(owning(rows), vi.fn(), "drugs");
    expect(ownedNames(container)).toEqual(["Novacoke", "Neuro-Stun VIII", "Cleaner"]);
  });

  it("lists a child under its parent rather than as a row of its own", () => {
    const nested = [gear("g1", "Medkit"), gear("g1a", "Medkit Supplies", { parent_id: "g1" })];
    const { container } = renderPanel(owning(nested), vi.fn(), "misc");

    expect(ownedNames(container)).toEqual(["Medkit"]);
    expect(container.textContent).toContain("Medkit Supplies");
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
          extra_options: ["Pistols", "Blades"],
        }),
      ]),
      patch,
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
          extra_options: Array.from({ length: 100 }, (_, i) => `Name ${i}`),
        }),
      ]),
      patch,
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
      drug_effect: "+1 CHA, +1 REA",
      drug_vectors: ["Ingestion", "Inhalation"],
      drug_speed: "Immediate",
      ...over,
    });

  it("prints the effect, the vectors and the onset", () => {
    const { container } = renderPanel(owning([novacoke()]), vi.fn(), "drugs");

    expect(container.textContent).toContain("効果: +1 CHA, +1 REA");
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
    } as any);
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
    } as any);

  const medkit = (over: Record<string, unknown> = {}) =>
    gear("g1", "Medkit", { addoncategories: ["Medkit Add-ons", "Custom"], ...over });

  it("offers only core add-ons this parent takes, minus what it already has", () => {
    renderPanel(
      owning([
        medkit(),
        gear("g1a", "Medkit Supplies", { gear_id: "a-supplies", parent_id: "g1" }),
      ]),
      vi.fn(),
      "misc",
      catalog(),
    );

    const select = screen.getByRole("combobox", { name: "Medkit: 追加ギア" });
    const options = [...select.querySelectorAll("option")].map((o) => o.textContent);
    expect(options).toEqual(["追加ギア", "Stabilisation Unit (250¥)"]);
  });

  it("a search opens the list up to supplements", () => {
    renderPanel(owning([medkit()]), vi.fn(), "misc", catalog());

    fireEvent.change(screen.getByPlaceholderText("ギアを検索"), { target: { value: "trauma" } });

    const select = screen.getByRole("combobox", { name: "Medkit: 追加ギア" });
    const options = [...select.querySelectorAll("option")].map((o) => o.textContent);
    expect(options).toContain("Trauma Patch (500¥)");
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
    } as any);
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
    } as any);
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
    } as any);

  const offered = () =>
    [...document.querySelectorAll(".quality-list .quality-item b")].map((el) => el.textContent);

  it("leaves out drugs, parts that need a parent, and supplements", () => {
    renderPanel(owning([]), vi.fn(), "misc", catalog());
    expect(offered()).toEqual(["Medkit", "Rope"]);
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
    } as any);
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
          effect: "+1 CHA",
          vectors: ["Ingestion"],
        },
      ],
      // the fallback list, which must not be the one used
      gear: [{ id: "g-jazz", name: "Jazz", category: "Drugs", cost: "75", source: "SR5" }],
    } as any);
    const { container } = renderPanel(owning([]), vi.fn(), "drugs", drugs);

    const tabs = [...container.querySelectorAll(".option-row .tab")].map((el) => el.textContent);
    expect(tabs).toEqual(["すべて", "Chemicals", "Drugs", "Toxins"]);
    expect(offered()).toEqual(["Novacoke"]);
    expect(container.textContent).toContain("効果: +1 CHA");
  });

  it("buying a drug sends rating 1 and nothing else", () => {
    const drugs = makeCatalog({
      drugs: [{ id: "d-nova", name: "Novacoke", category: "Drugs", cost: "10", source: "SR5" }],
    } as any);
    const patch = vi.fn();
    renderPanel(owning([]), patch, "drugs", drugs);

    fireEvent.click(screen.getByRole("button", { name: "購入" }));

    expect(patch.mock.calls[0][0].gear).toEqual([{ gear_id: "d-nova", rating: 1 }]);
  });
});
