/**
 * The module slots on a cyberdeck. `installOneModule` has a test in
 * `construction.test.tsx`; the component around it had none of its own, and
 * nearly every control on it writes to `ch.gear` — the *saved* rows — while
 * being rendered from `d.gear`, the derived ones. Mixing those two up is the
 * mistake this file is here to catch.
 */
import { fireEvent, render, screen, within } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";
import { DeckModuleRows } from "./DeckModuleRows";

const DECK = "deck";

const moduleRow = (over: Record<string, unknown> = {}) => ({
  id: "m1",
  gear_id: "g-module",
  name: "Browse Module",
  category: "Cyberdeck Modules",
  parent_id: DECK,
  qty: 1,
  rating: 1,
  rating_max: 0,
  nuyen: 1200,
  equipped: true,
  module_valid: true,
  module_effect_supported: true,
  ...over,
});

const catalog = {
  gear: [
    { id: "g-module", name: "Browse Module", category: "Cyberdeck Modules" },
    {
      id: "g-targeted",
      name: "Targeting Module",
      category: "Cyberdeck Modules",
      needs_extra: true,
      extra_options: ["Attack", "Sleaze"],
    },
    { id: "g-other", name: "Medkit", category: "Medical" },
  ],
};

function renderRows(
  rows: Record<string, unknown>[],
  over: { used?: number; max?: number; hardwired?: boolean } = {},
) {
  const patch = vi.fn<(body: Record<string, unknown>) => void>();
  const ch = makeCharacter({ gear: rows, derived: { gear: rows } } as never);
  const { container } = render(
    <DeckModuleRows
      {...panelProps(ch, { catalog: makeCatalog(catalog as never), patch })}
      hostId={DECK}
      hostName="Erika MCD-1"
      hardwired={over.hardwired}
      used={over.used ?? 1}
      max={over.max ?? 3}
    />,
  );
  return { patch, ui: within(container) };
}

it("names the pool it is and how full it is", () => {
  renderRows([], { used: 2, max: 4 });
  expect(screen.getByText(/通常／資質枠 \/ モジュール 2\/4/)).toBeDefined();
});

it("says when the pool is the hardwired one", () => {
  renderRows([], { hardwired: true });
  expect(screen.getByText(/直結枠/)).toBeDefined();
});

it("flags a module the engine could not validate or could not apply", () => {
  renderRows([
    moduleRow({
      qty: 2,
      label: "Browse (×2)",
      module_valid: false,
      module_effect_supported: false,
    }),
  ]);
  expect(screen.getByText(/Browse \(×2\) ×2 \/ 1,200¥/)).toBeDefined();
  expect(screen.getByText(/搭載構成が無効/)).toBeDefined();
  expect(screen.getByText(/個別効果は手動で管理/)).toBeDefined();
});

// Switching a module off leaves it fitted: it still costs a slot, which is
// what the help text on the panel promises.
it("turns a fitted module off without taking it out", () => {
  const { patch } = renderRows([moduleRow()]);
  fireEvent.click(screen.getByRole("checkbox", { name: "Browse Module：モジュール効果を有効化" }));
  expect(patch).toHaveBeenCalledWith({ gear: [expect.objectContaining({ equipped: false })] });
  expect(screen.getByText(/停止中でも搭載枠を使います/)).toBeDefined();
});

it("takes a module out without giving it up, and deletes it when asked to", () => {
  const { patch } = renderRows([moduleRow(), moduleRow({ id: "m2", name: "Other" })]);

  fireEvent.click(screen.getByRole("button", { name: "Browse Module：取り外す" }));
  expect(patch).toHaveBeenLastCalledWith({
    gear: [
      expect.objectContaining({ id: "m1", parent_id: null }),
      expect.objectContaining({ id: "m2", parent_id: DECK }),
    ],
  });

  fireEvent.click(screen.getByRole("button", { name: "Browse Module を削除" }));
  expect(patch).toHaveBeenLastCalledWith({ gear: [expect.objectContaining({ id: "m2" })] });
});

it("offers the catalog's choices for a module that needs a target, and saves the typed one", () => {
  const { patch } = renderRows([
    moduleRow({ gear_id: "g-targeted", needs_extra: true, extra: "Attack" }),
  ]);
  const field = screen.getByRole("combobox", { name: "対象" }) as HTMLInputElement;
  expect(field.value).toBe("Attack");

  const options = Array.from(document.querySelectorAll(`#module-picks-m1 option`)).map((o) =>
    o.getAttribute("value"),
  );
  expect(options).toEqual(["Attack", "Sleaze"]);

  // free text, so a target the catalog never listed is allowed through
  fireEvent.change(field, { target: { value: "Data Processing" } });
  expect(patch).toHaveBeenCalledWith({
    gear: [expect.objectContaining({ extra: "Data Processing" })],
  });
});

it("asks for no target for a module that does not take one", () => {
  const { ui } = renderRows([moduleRow()]);
  expect(ui.queryByRole("combobox", { name: "対象" })).toBeNull();
});

// A spare bought earlier sits in the inventory with no parent. Fitting one
// splits the stack rather than moving all of it.
it("fits one spare out of the inventory, and offers none when there are none", () => {
  const { patch } = renderRows([
    moduleRow(),
    moduleRow({ id: "spare", parent_id: null, qty: 2, name: "Spare Module" }),
  ]);
  fireEvent.change(screen.getByRole("combobox", { name: "購入済みの予備モジュールを搭載" }), {
    target: { value: "spare" },
  });
  const written = patch.mock.calls[0][0].gear as Record<string, unknown>[];
  expect(written).toHaveLength(3);
  expect(written[1]).toMatchObject({ id: "spare", qty: 1, parent_id: null });
  expect(written[2]).toMatchObject({ qty: 1, parent_id: DECK, name: "Spare Module" });

  const { ui } = renderRows([moduleRow()]);
  expect(ui.queryByRole("combobox", { name: "購入済みの予備モジュールを搭載" })).toBeNull();
});

it("buys a module straight into this deck, and only lists modules", () => {
  const { patch } = renderRows([]);
  const buy = screen.getByRole("combobox", { name: "Erika MCD-1: モジュールを購入・搭載" });
  const offered = Array.from(buy.querySelectorAll("option")).map((o) => o.textContent);
  expect(offered).toContain("Browse Module");
  expect(offered).not.toContain("Medkit");

  // a module that needs a target asks for one alongside the picker
  fireEvent.change(buy, { target: { value: "g-targeted" } });
  const target = screen.getByRole("combobox", { name: "Erika MCD-1: 対象" }) as HTMLInputElement;
  fireEvent.change(target, { target: { value: "Sleaze" } });
  fireEvent.click(screen.getByRole("button", { name: "Erika MCD-1: 装着" }));
  expect(patch).toHaveBeenCalledWith({
    gear: [{ gear_id: "g-targeted", rating: 1, qty: 1, parent_id: DECK, extra: "Sleaze" }],
  });
});

it("stops offering anything once the slots are full", () => {
  renderRows([moduleRow()], { used: 3, max: 3 });
  expect(screen.getByText(/搭載枠が埋まっています/)).toBeDefined();
  expect(
    screen.queryByRole("combobox", { name: "Erika MCD-1: モジュールを購入・搭載" }),
  ).toBeNull();
  // the fitted module can still be taken out — that is how a slot is freed
  expect(screen.getByRole("button", { name: "Browse Module：取り外す" })).toBeDefined();
});
