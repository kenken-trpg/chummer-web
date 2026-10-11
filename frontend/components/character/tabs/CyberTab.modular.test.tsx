import { fireEvent, render, screen } from "@testing-library/react";
import { CyberTab } from "./CyberTab";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";
import type { Derived, InstalledWare, WareCatalogItem } from "@/lib/types";
import { modularMountCandidates } from "@/lib/character/ware";

const spec = (id: string, extra: Partial<WareCatalogItem> = {}): WareCatalogItem => ({
  id,
  name: id,
  category: "Cyberlimb",
  ess: "0",
  cost: "0",
  minrating: 1,
  maxrating: 1,
  plugin: false,
  has_wireless: false,
  source: "CF",
  page: "0",
  ...extra,
});
const catalogItems = [
  spec("hip", { modular_mount: "hip" }),
  spec("knee", { modular_mount: "knee" }),
  spec("leg", { mounts_to: "hip", allow_subsystems: ["Enhancement"] }),
  spec("enhancement", { category: "Enhancement", plugin: true }),
  spec("enhancement2", { category: "Enhancement", plugin: true }),
  spec("nested", { modular_mount: "hip" }),
];
const row = (id: string, ware_id: string, extra: Partial<InstalledWare> = {}): InstalledWare => ({
  id,
  ware_id,
  name: ware_id,
  category: "Cyberlimb",
  grade: "Standard",
  rating: 1,
  wireless: true,
  essence: 0,
  nuyen: 1000,
  side: "Left",
  ...extra,
});
const rows = [
  row("hip1", "hip"),
  row("hip2", "hip"),
  row("right", "hip", { side: "Right" }),
  row("alpha", "hip", { grade: "Alphaware" }),
  row("wrong", "knee"),
  row("busy", "hip"),
  row("other-leg", "leg", { parent_id: "busy" }),
  row("leg1", "leg", { parent_id: "hip1", modular_equipped: true }),
  row("child", "enhancement", { parent_id: "leg1" }),
  row("descendant", "nested", { parent_id: "child" }),
];

beforeEach(() => localStorage.setItem("wareCompact", "0"));

function renderRows(owned = rows) {
  const patch = vi.fn();
  const ch = makeCharacter({ cyberware: owned.map(({ name: _name, ...rest }) => rest) });
  const catalog = makeCatalog({
    cyberware: {
      items: catalogItems,
      grades: [{ name: "Standard", ess: 1, ess_adapsin: 0.9, cost: 1 }],
    },
  });
  render(
    <CyberTab
      {...panelProps(ch, { catalog, patch, d: { ...ch.derived, cyberware: owned } as Derived })}
    />,
  );
  return { patch, ch };
}

it("offers separate same-named hosts, preserving the current one; filters type, grade, side, occupied and descendants", () => {
  renderRows();
  const select = screen
    .getAllByRole("combobox", { name: "leg: モジュラー接続先" })
    .find((el) => (el as HTMLSelectElement).value === "hip1") as HTMLSelectElement;
  expect([...select.options].map((option) => option.value)).toEqual(["", "hip1", "hip2"]);
  expect(select.options[1].text).not.toBe(select.options[2].text);
});

it("detaches and moves only the purchase parent; keeps IDs, descendants, price and wireless preference", () => {
  const { patch, ch } = renderRows();
  const select = screen
    .getAllByRole("combobox", { name: "leg: モジュラー接続先" })
    .find((el) => (el as HTMLSelectElement).value === "hip1")!;
  fireEvent.change(select, { target: { value: "" } });
  expect(patch).toHaveBeenLastCalledWith({
    cyberware: ch.cyberware!.map((owned) =>
      owned.id === "leg1" ? { ...owned, parent_id: null } : owned,
    ),
  });
  fireEvent.change(select, { target: { value: "hip2" } });
  expect(patch).toHaveBeenLastCalledWith({
    cyberware: ch.cyberware!.map((owned) =>
      owned.id === "leg1" ? { ...owned, parent_id: "hip2" } : owned,
    ),
  });
  // No gear, accessories or skill-pick deletion patch accompanies detachment.
  expect(Object.keys(patch.mock.calls[0][0])).toEqual(["cyberware"]);
  expect(screen.getByText("enhancement")).toBeDefined();
  expect(screen.getByText("nested")).toBeDefined();
});

it("allows reconnecting a detached purchase, and displays its inactive state", () => {
  renderRows(
    rows.map((owned) =>
      owned.id === "leg1" ? { ...owned, parent_id: null, modular_equipped: false } : owned,
    ),
  );
  expect(screen.getByText("切り離し状態・改善効果は無効")).toBeDefined();
  const select = screen
    .getAllByRole("combobox", { name: "leg: モジュラー接続先" })
    .find((el) => (el as HTMLSelectElement).value === "") as HTMLSelectElement;
  expect([...select.options].map((option) => option.value)).toEqual(["", "hip1", "hip2"]);
});

it("keeps an invalid saved host visible and still permits detachment", () => {
  const { patch } = renderRows(
    rows.map((owned) => (owned.id === "leg1" ? { ...owned, parent_id: "wrong" } : owned)),
  );
  const select = screen
    .getAllByRole("combobox", { name: "leg: モジュラー接続先" })
    .find((el) => (el as HTMLSelectElement).value === "wrong") as HTMLSelectElement;
  expect(select.selectedOptions[0].disabled).toBe(true);
  expect(select.selectedOptions[0].text).toContain("条件不一致");
  fireEvent.change(select, { target: { value: "" } });
  expect(patch).toHaveBeenCalled();
});

it("fails closed on cyclic or vehicle-rooted candidates; accepts a side-less plug", () => {
  const plug = row("plug", "leg", { side: null });
  const hosts = [
    row("ok", "hip", { side: "Right" }),
    row("vehicle", "hip", { parent_id: "vehicle-mod" }),
    row("cycle1", "hip", { parent_id: "cycle2" }),
    row("cycle2", "hip", { parent_id: "cycle1" }),
  ];
  expect(
    modularMountCandidates(plug, [plug, ...hosts], catalogItems).map((host) => host.id),
  ).toEqual(["ok"]);
});

it("offers no connection controls on bundled modular ware", () => {
  renderRows(rows.map((owned) => (owned.ware_id === "leg" ? { ...owned, included: true } : owned)));
  expect(screen.queryByRole("combobox", { name: "leg: モジュラー接続先" })).toBeNull();
});

it("adds a selected enhancement to a nested modular limb rather than its connector", () => {
  const { patch, ch } = renderRows();
  const mount = screen
    .getAllByRole("combobox", { name: "leg: モジュラー接続先" })
    .find((el) => (el as HTMLSelectElement).value === "hip1")!;
  const picker = mount.closest(".cyber-item")!.querySelector(".slot-picker")!;
  fireEvent.change(picker.querySelector("select")!, { target: { value: "enhancement2" } });
  fireEvent.click(picker.querySelector("button")!);
  expect(patch).toHaveBeenCalledWith({
    cyberware: [
      ...ch.cyberware!,
      {
        ware_id: "enhancement2",
        rating: 1,
        grade: "Standard",
        wireless: true,
        parent_id: "leg1",
      },
    ],
  });
});
