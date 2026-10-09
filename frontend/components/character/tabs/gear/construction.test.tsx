import { fireEvent, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { makeCharacter } from "@/tests/fixtures";
import { CyberdeckGear } from "./CyberdeckGear";
import { installOneModule } from "./DeckModuleRows";
import { renderPanel, host } from "./gear-addons.helpers";

it("installing one spare module preserves the total owned and purchase choices", () => {
  const rows = [
    {
      id: "spare",
      gear_id: "module",
      qty: 3,
      rating: 1,
      extra: "Browse",
      discounted: true,
      cost: 900,
      equipped: false,
    },
  ];
  const out = installOneModule(rows, "spare", "deck");
  expect(out.reduce((n, r) => n + (r.qty || 0), 0)).toBe(3);
  expect(out[0]).toEqual({ ...rows[0], qty: 2 });
  expect(out[1]).toMatchObject({ ...rows[0], id: expect.any(String), qty: 1, parent_id: "deck" });
  expect(out[1].id).not.toBe("spare");
});

it("a pending modification requires an exact allocation before confirming construction", () => {
  const mod = {
    id: "mod",
    gear_id: "modify",
    name: "Modify",
    category: "Electronic Modification",
    parent_id: "deck",
    qty: 1,
    nuyen: 0,
    rating: 1,
    rating_max: 0,
    modification_status: "pending",
    modification_host_id: "deck",
    material_required_units: 16,
    material_available_units: 20,
  };
  const parts = {
    id: "parts",
    gear_id: "five",
    name: "Five-Pack",
    category: "Electronic Parts",
    qty: 5,
    rating: 1,
    rating_max: 0,
    nuyen: 1000,
    parts_available_units: 20,
    parts_purchased_units: 20,
    parts_remaining_units: 20,
  };
  const record = {
    id: "record",
    modification_id: "mod",
    gear_id: "modify",
    host_id: "deck",
    status: "pending",
    allocations: [],
    required_units: 16,
  };
  const ch = makeCharacter({
    cyberdecks: [host("deck", "Erika")],
    gear: [mod, parts],
    electronic_modification_records: [record],
    derived: { cyberdecks: [host("deck", "Erika")], gear: [mod, parts] },
  } as never);
  const patch = vi.fn();
  renderPanel(CyberdeckGear, ch, patch);
  const confirm = screen.getByRole("button", { name: "施工済みにする" }) as HTMLButtonElement;
  expect(confirm.disabled).toBe(true);
  fireEvent.change(screen.getByRole("spinbutton", { name: "Modify: Five-Pack" }), {
    target: { value: "4" },
  });
  expect(confirm.disabled).toBe(false);
  fireEvent.click(confirm);
  expect(patch.mock.calls[0][0].electronic_modification_records).toEqual([
    { ...record, status: "completed", allocations: [{ source_id: "parts", units: 16 }], note: "" },
  ]);
  expect(patch.mock.calls[0][0].gear).toBeUndefined();
});
