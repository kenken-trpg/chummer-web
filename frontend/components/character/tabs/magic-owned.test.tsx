import { fireEvent, render, screen, within } from "@testing-library/react";
import type { ComponentType } from "react";
import { describe, expect, it, vi } from "vitest";
import type { Catalog, Character } from "@/lib/types";
import type { TabPanelProps } from "@/components/character/types";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";
import { AdeptTab } from "./AdeptTab";
import { FociTab } from "./FociTab";
import { SpiritsTab } from "./SpiritsTab";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * The magic tabs' catalog halves are covered by the per-tab tests. This covers
 * the half that only exists once something is *bought*: the row of controls
 * under an installed power, a summoned spirit, a bonded focus.
 *
 * Every one of those controls is a `map` over the whole list keyed on
 * `row.id === item.id`, and a single owned row cannot distinguish a correct
 * predicate from `() => true`. So each case owns **two** rows and acts on the
 * second.
 */

function renderTab(
  Panel: ComponentType<TabPanelProps> | ComponentType<any>,
  character: Character,
  patch: (b: Record<string, unknown>) => void,
  catalog: Partial<Catalog> = {},
) {
  return render(
    <Panel
      catalog={makeCatalog(catalog)}
      character={character}
      d={character.derived}
      tr={identityTr}
      trGroup={identityTr}
      t={((k: string) => k) as any}
      ui={testUi}
      patch={patch as any}
      setCharacter={() => {}}
    />,
  );
}

const rows = (container: HTMLElement) => [
  ...container.querySelectorAll<HTMLElement>(".cyber-item"),
];

describe("<AdeptTab> installed powers", () => {
  const power = (id: string, name: string, over: Record<string, unknown> = {}) => ({
    id,
    power_id: `c-${id}`,
    name,
    cost: 1,
    rating: 1,
    rating_min: 1,
    rating_max: 4,
    source: "SR5",
    ...over,
  });
  const owning = (list: Record<string, unknown>[]) =>
    makeCharacter({
      talent: "Adept",
      adept_powers: list,
      derived: { adept_powers: list },
    } as any);

  it("the rating box edits the power it sits under", () => {
    const patch = vi.fn();
    renderTab(
      AdeptTab,
      owning([power("p1", "Improved Reflexes"), power("p2", "Combat Sense")]),
      patch,
    );

    fireEvent.change(screen.getAllByRole("spinbutton")[1], { target: { value: "3" } });

    const out = patch.mock.calls[0][0].adept_powers as { id: string; rating: number }[];
    expect(out.find((r) => r.id === "p1")?.rating).toBe(1);
    expect(out.find((r) => r.id === "p2")?.rating).toBe(3);
  });

  it("offers no rating box for a power with a single rating", () => {
    renderTab(AdeptTab, owning([power("p1", "Combat Sense", { rating_max: 1 })]), vi.fn());
    expect(screen.queryAllByRole("spinbutton")).toHaveLength(0);
  });

  it("toggles the way discount on one power only", () => {
    const patch = vi.fn();
    renderTab(
      AdeptTab,
      owning([
        power("p1", "First", { can_discount: true }),
        power("p2", "Second", { can_discount: true }),
      ]),
      patch,
    );

    fireEvent.click(screen.getAllByRole("checkbox")[1]);

    const out = patch.mock.calls[0][0].adept_powers as { id: string; discounted: boolean }[];
    expect(out.find((r) => r.id === "p1")?.discounted).toBeUndefined();
    expect(out.find((r) => r.id === "p2")?.discounted).toBe(true);
  });

  /** A power granted by a mentor or a quality is not the character's to spend
   *  on, so it has no controls and no delete button — only a "free" note. */
  it("shows a free power as free, with nothing to edit or remove", () => {
    const { container } = renderTab(
      AdeptTab,
      owning([power("p1", "Granted", { free_only: true, cost: 0 })]),
      vi.fn(),
    );

    const row = rows(container)[0];
    expect(within(row).queryByRole("button", { name: "削除" })).toBeNull();
    expect(within(row).queryAllByRole("spinbutton")).toHaveLength(0);
    expect(row.textContent).toContain("無料");
  });

  it("deleting the second power keeps the first", () => {
    const patch = vi.fn();
    const { container } = renderTab(
      AdeptTab,
      owning([power("p1", "First"), power("p2", "Second")]),
      patch,
    );

    fireEvent.click(within(rows(container)[1]).getByRole("button", { name: "削除" }));

    const out = patch.mock.calls[0][0].adept_powers as { id: string }[];
    expect(out.map((r) => r.id)).toEqual(["p1"]);
  });
});

describe("<SpiritsTab> summoned spirits", () => {
  const spirit = (id: string, name: string, over: Record<string, unknown> = {}) => ({
    id,
    spirit_id: `c-${id}`,
    name,
    force: 2,
    force_max: 6,
    services: 2,
    bound: false,
    nuyen: 0,
    hits: 4,
    opposed_hits: 1,
    attributes: {},
    source: "SR5",
    ...over,
  });
  const owning = (list: Record<string, unknown>[]) =>
    makeCharacter({ spirits: list, derived: { spirits: list } } as any);

  const character = () => owning([spirit("s1", "Fire"), spirit("s2", "Air")]);

  it("Force on the second spirit leaves the first alone", () => {
    const patch = vi.fn();
    const { container } = renderTab(SpiritsTab, character(), patch);

    const box = within(rows(container)[1]).getByRole("spinbutton", { name: "Force" });
    fireEvent.change(box, { target: { value: "5" } });

    const out = patch.mock.calls[0][0].spirits as { id: string; force: number }[];
    expect(out.find((r) => r.id === "s1")?.force).toBe(2);
    expect(out.find((r) => r.id === "s2")?.force).toBe(5);
  });

  /** Editing the services count by hand contradicts the roll that produced it,
   *  so the recorded hits are dropped rather than left to disagree. */
  it("setting services by hand clears the recorded roll", () => {
    const patch = vi.fn();
    const { container } = renderTab(SpiritsTab, character(), patch);

    fireEvent.change(within(rows(container)[0]).getByRole("spinbutton", { name: "サービス" }), {
      target: { value: "3" },
    });

    const out = patch.mock.calls[0][0].spirits as Record<string, unknown>[];
    expect(out[0]).toMatchObject({ services: 3, hits: null, opposed_hits: null });
    expect(out[1]).toMatchObject({ services: 2, hits: 4 }); // the other is untouched
  });

  it("binding a spirit through the kind select does not bind the other", () => {
    const patch = vi.fn();
    const { container } = renderTab(SpiritsTab, character(), patch);

    fireEvent.change(within(rows(container)[1]).getByRole("combobox", { name: "種類" }), {
      target: { value: "bound" },
    });

    const out = patch.mock.calls[0][0].spirits as { id: string; bound: boolean }[];
    expect(out.find((r) => r.id === "s1")?.bound).toBe(false);
    expect(out.find((r) => r.id === "s2")?.bound).toBe(true);
  });

  it("dismissing one spirit keeps the other", () => {
    const patch = vi.fn();
    const { container } = renderTab(SpiritsTab, character(), patch);

    fireEvent.click(within(rows(container)[0]).getByRole("button", { name: "削除" }));

    expect((patch.mock.calls[0][0].spirits as { id: string }[]).map((r) => r.id)).toEqual(["s2"]);
  });
});

describe("<FociTab> bonded foci", () => {
  const focus = (id: string, name: string, over: Record<string, unknown> = {}) => ({
    id,
    focus_id: `c-${id}`,
    name,
    force: 2,
    force_min: 1,
    force_max: 6,
    nuyen: 4000,
    karma: 2,
    source: "SR5",
    ...over,
  });
  const owning = (list: Record<string, unknown>[]) =>
    makeCharacter({ foci: list, derived: { foci: list } } as any);

  it("Force on the second focus leaves the first alone", () => {
    const patch = vi.fn();
    const { container } = renderTab(
      FociTab,
      owning([focus("f1", "Power Focus"), focus("f2", "Spell Focus")]),
      patch,
    );

    fireEvent.change(within(rows(container)[1]).getByRole("spinbutton", { name: "Force" }), {
      target: { value: "4" },
    });

    const out = patch.mock.calls[0][0].foci as { id: string; force: number }[];
    expect(out.find((r) => r.id === "f1")?.force).toBe(2);
    expect(out.find((r) => r.id === "f2")?.force).toBe(4);
  });

  /** A weapon focus is bonded *to* a weapon; until one is chosen the row says
   *  so, and clearing the select stores null rather than "". */
  it("binds a weapon focus to a weapon, and clears it back to null", () => {
    const patch = vi.fn();
    const weapon = {
      needs_weapon: true,
      weapon_type: "Melee",
      weapon_options: [{ id: "w1", name: "Katana" }],
    };
    renderTab(FociTab, owning([focus("f1", "Weapon Focus", weapon)]), patch);

    const select = screen.getAllByRole("combobox")[0];
    fireEvent.change(select, { target: { value: "w1" } });
    expect((patch.mock.calls[0][0].foci as { extra: string }[])[0].extra).toBe("w1");

    fireEvent.change(select, { target: { value: "" } });
    expect((patch.mock.calls[1][0].foci as { extra: string | null }[])[0].extra).toBeNull();
  });

  it("a crafted focus can switch its formula between bought and designed", () => {
    const patch = vi.fn();
    renderTab(
      FociTab,
      owning([focus("f1", "Power Focus", { crafted: true, formula_bought: true })]),
      patch,
    );

    fireEvent.change(screen.getByRole("combobox", { name: "術式" }), {
      target: { value: "design" },
    });

    expect((patch.mock.calls[0][0].foci as { formula_bought: boolean }[])[0].formula_bought).toBe(
      false,
    );
  });

  it("unbonding one focus keeps the other", () => {
    const patch = vi.fn();
    const { container } = renderTab(
      FociTab,
      owning([focus("f1", "First"), focus("f2", "Second")]),
      patch,
    );

    fireEvent.click(within(rows(container)[1]).getByRole("button", { name: "削除" }));

    expect((patch.mock.calls[0][0].foci as { id: string }[]).map((r) => r.id)).toEqual(["f1"]);
  });
});
