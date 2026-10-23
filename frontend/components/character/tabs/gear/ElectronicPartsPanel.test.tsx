/**
 * The panel that books electronic parts a character did not buy — salvaged,
 * supplied with a shop, handed over by the GM — and buys the ones they did.
 *
 * It had no test of its own: what coverage it had came from a parent tab
 * rendering it. Everything it writes goes straight into the character through
 * `patch`, so a wrong unit conversion or a dropped `equipment_id` is saved and
 * silently priced from then on. Units are quarter-packs in the save and packs
 * on screen, which is where that kind of mistake hides.
 */
import { fireEvent, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { makeCharacter } from "@/tests/fixtures";
import { ElectronicPartsPanel } from "./ElectronicPartsPanel";
import { renderPanel } from "./gear-addons.helpers";

const ONE_PACK = "f56affe6-0159-4f7a-ba4d-b5283bd25c44";
const FIVE_PACK = "ec53ae4e-086f-4817-8cc2-ec574aa7cd51";
/** The two gear rows a shop is: a kit (x2 packs) and a facility (x10). */
const KIT = "4edec80a-e8df-4817-9728-4a6fc04d183e";
const FACILITY = "d0c85aa4-5686-452b-9f1a-7c603ac43258";

const catalog = {
  gear: [
    { id: ONE_PACK, name: "Electronic Parts", cost: 100 },
    { id: FIVE_PACK, name: "Electronic Parts (5)", cost: 450 },
  ],
} as never;

const shop = (id: string, gear_id: string, name: string, qty = 1) => ({
  id,
  gear_id,
  name,
  category: "Tools",
  extra: "Hardware",
  qty,
  rating: 1,
  rating_max: 0,
  nuyen: 500,
});

function panel(over: Record<string, unknown> = {}) {
  const patch = vi.fn();
  const ch = makeCharacter(over as never);
  renderPanel(ElectronicPartsPanel as never, ch, patch, catalog);
  return patch;
}

const add = () => screen.getByRole("button", { name: "調達した部品を登録" }) as HTMLButtonElement;
const supplyNote = () => screen.getByRole("textbox", { name: "調達の説明" });
const historyNote = () => screen.getByRole("textbox", { name: "訂正の理由" });

// The two note fields do different things — one explains where parts came
// from, the other why a record is being cancelled — and used to share one
// label, which a screen reader reads out identically.
it("names its two note fields apart", () => {
  panel({ derived: { gear: [] } });
  expect(supplyNote()).not.toBe(historyNote());
});

it("explains how parts are counted, where they come from, and the history", () => {
  panel({ derived: { gear: [] } });
  expect(screen.getByRole("button", { name: "部品の数え方 の説明" })).toBeDefined();
  expect(screen.getByText(/予約は準備中の施工に配分した量/)).toBeDefined();
  expect(screen.getByRole("button", { name: "調達方法の違い の説明" })).toBeDefined();
  expect(screen.getByText(/Tool Shop（Hardware）は 1 台につき 2 パック/)).toBeDefined();
  expect(screen.getByRole("button", { name: "施工・消費履歴 の説明" })).toBeDefined();
});

it("counts a purchased row in packs, not in the quarters it is stored as", () => {
  const row = {
    id: "p1",
    gear_id: ONE_PACK,
    name: "Electronic Parts",
    category: "Electronic Parts",
    qty: 1,
    rating: 1,
    rating_max: 0,
    nuyen: 1200,
    parts_purchased_units: 20,
    parts_remaining_units: 9,
    parts_used_units: 8,
    parts_reserved_units: 3,
  };
  panel({ gear: [row], derived: { gear: [row] } });

  expect(
    screen.getByText(/部品残量 2.25パック \/ 購入 5 \/ 使用済み 2 \/ 予約 0.75/),
  ).toBeDefined();
  expect(screen.getByText(/1,200¥/)).toBeDefined();
});

// A supply has no counters of its own: what is left is its own size less what
// the records drew from it, and a pending record only reserves.
it("takes completed and pending allocations off a supply, and names where it came from", () => {
  const supplies = [
    { id: "s1", kind: "salvaged", units: 20, note: "廃ビルから回収" },
    { id: "s2", kind: "gm", units: 8, note: "ジョンソン氏の差し入れ" },
  ];
  panel({
    electronic_parts_supplies: supplies,
    electronic_modification_records: [
      { id: "r1", status: "completed", allocations: [{ source_id: "s1", units: 8 }] },
      { id: "r2", status: "pending", allocations: [{ source_id: "s1", units: 4 }] },
      // another supply's draw must not count against this one
      { id: "r3", status: "completed", allocations: [{ source_id: "s2", units: 4 }] },
    ],
    derived: { gear: [] },
  });

  expect(screen.getByText(/回収: 廃ビルから回収 \/ 部品残量 3パック/)).toBeDefined();
  expect(screen.getByText(/回収: 廃ビルから回収.*使用済み 2 \/ 予約 1/)).toBeDefined();
  expect(screen.getByText(/GM指定: ジョンソン氏の差し入れ \/ 部品残量 1パック/)).toBeDefined();
});

it("refuses a supply with no explanation or a part-pack that is not a quarter", () => {
  panel({ derived: { gear: [] } });
  const packs = screen.getByRole("spinbutton", { name: "使用パック数（0.25刻み）" });
  const note = supplyNote();

  expect(add().disabled).toBe(true); // no note
  fireEvent.change(note, { target: { value: "回収" } });
  expect(add().disabled).toBe(false);

  fireEvent.change(packs, { target: { value: "0" } });
  expect(add().disabled).toBe(true);
  fireEvent.change(packs, { target: { value: "0.3" } }); // 1.2 quarters
  expect(add().disabled).toBe(true);
  fireEvent.change(packs, { target: { value: "0.25" } });
  expect(add().disabled).toBe(false);
});

it("books a salvaged supply in quarter-packs and clears the note it was given", () => {
  const patch = panel({ derived: { gear: [] } });
  fireEvent.change(screen.getByRole("spinbutton", { name: "使用パック数（0.25刻み）" }), {
    target: { value: "2.5" },
  });
  const note = supplyNote();
  fireEvent.change(note, { target: { value: "廃ビルから回収" } });
  fireEvent.click(add());

  expect(patch).toHaveBeenCalledTimes(1);
  expect(patch.mock.calls[0][0].electronic_parts_supplies).toEqual([
    {
      id: expect.any(String),
      kind: "salvaged",
      units: 10,
      note: "廃ビルから回収",
      equipment_id: null,
    },
  ]);
  expect((note as HTMLInputElement).value).toBe("");
});

it("asks which shop the parts came with, and sizes the supply from it", () => {
  const kit = shop("kit", KIT, "Hardware kit", 2);
  const facility = shop("fac", FACILITY, "Hardware facility");
  const patch = panel({
    gear: [kit, facility],
    derived: { gear: [kit, facility] },
  });
  // only once the kind says a shop is involved
  expect(screen.queryByRole("combobox", { name: "対象" })).toBeNull();
  fireEvent.change(screen.getByRole("combobox", { name: "調達方法" }), {
    target: { value: "equipment" },
  });
  const target = screen.getByRole("combobox", { name: "対象" });
  const packs = screen.getByRole("spinbutton", { name: "使用パック数（0.25刻み）" });
  fireEvent.change(supplyNote(), { target: { value: "工房付属" } });
  // a shop has to be named before this can be booked
  expect(add().disabled).toBe(true);

  // a kit is two packs per unit owned, a facility ten
  fireEvent.change(target, { target: { value: "kit" } });
  expect((packs as HTMLInputElement).value).toBe("4");
  fireEvent.change(target, { target: { value: "fac" } });
  expect((packs as HTMLInputElement).value).toBe("10");

  fireEvent.click(add());
  expect(patch.mock.calls[0][0].electronic_parts_supplies[0]).toMatchObject({
    kind: "equipment",
    units: 40,
    equipment_id: "fac",
  });
});

it("drops a shop from the list once it has already supplied its parts", () => {
  const kit = shop("kit", KIT, "Hardware kit");
  const facility = shop("fac", FACILITY, "Hardware facility");
  panel({
    gear: [kit, facility],
    electronic_parts_supplies: [
      { id: "s1", kind: "equipment", units: 4, note: "済", equipment_id: "kit" },
    ],
    derived: { gear: [kit, facility] },
  });
  fireEvent.change(screen.getByRole("combobox", { name: "調達方法" }), {
    target: { value: "equipment" },
  });

  const options = Array.from(
    screen.getByRole("combobox", { name: "対象" }).querySelectorAll("option"),
  ).map((o) => o.textContent);
  expect(options).toEqual(["選択", "Hardware facility"]);
});

it("prices a purchase by the pack count the chosen row actually carries", () => {
  const patch = panel({ derived: { gear: [] } });
  const qty = screen.getByRole("spinbutton", { name: "購入販売単位数" });
  const buy = () => screen.getAllByRole("button", { name: "電子部品を追加購入" }).at(-1)!;

  expect(screen.getByText("1パック / 100¥（割引前）")).toBeDefined();
  fireEvent.change(qty, { target: { value: "3" } });
  expect(screen.getByText("3パック / 300¥（割引前）")).toBeDefined();

  // the five-pack is one sales unit and five packs
  fireEvent.change(screen.getByRole("combobox", { name: "電子部品を追加購入" }), {
    target: { value: FIVE_PACK },
  });
  expect(screen.getByText("15パック / 1350¥（割引前）")).toBeDefined();

  fireEvent.click(buy());
  expect(patch.mock.calls[0][0].gear).toEqual([{ gear_id: FIVE_PACK, qty: 3, rating: 1 }]);
});

it("offers no purchase at all when the catalog has no parts to sell", () => {
  const patch = vi.fn();
  renderPanel(
    ElectronicPartsPanel as never,
    makeCharacter({ derived: { gear: [] } } as never),
    patch,
  );
  expect(screen.queryByRole("combobox", { name: "電子部品を追加購入" })).toBeNull();
  expect(screen.queryByRole("spinbutton", { name: "購入販売単位数" })).toBeNull();
});

// Parts are spent for good, so a mistake is corrected by cancelling the record
// with a reason — and only for work whose modification is no longer owned.
it("cancels a mistaken record, with a reason, once its modification is gone", () => {
  const records = [
    {
      id: "r1",
      gear_id: ONE_PACK,
      modification_id: "gone",
      status: "completed",
      required_units: 16,
      note: "誤って施工済みにした",
      allocations: [],
    },
    {
      id: "r2",
      gear_id: ONE_PACK,
      modification_id: "kept",
      status: "completed",
      required_units: 8,
      note: "正しい施工",
      allocations: [],
    },
  ];
  const patch = panel({
    gear: [{ id: "kept", gear_id: "mod", qty: 1, rating: 1 }],
    electronic_modification_records: records,
    derived: { gear: [] },
  });

  expect(screen.getByText(/誤って施工済みにした \/ 対象改造は取り外し済み/)).toBeDefined();
  // the record whose modification is still fitted is not correctable
  const correct = screen.getAllByRole("button", { name: "誤入力として履歴取消" });
  expect(correct).toHaveLength(1);
  expect((correct[0] as HTMLButtonElement).disabled).toBe(true);

  fireEvent.change(historyNote(), { target: { value: "GM 確認済み、入力ミス" } });
  fireEvent.click(screen.getByRole("button", { name: "誤入力として履歴取消" }));

  expect(patch.mock.calls[0][0].electronic_modification_records).toEqual([
    { ...records[0], status: "cancelled", note: "GM 確認済み、入力ミス" },
    records[1],
  ]);
});
