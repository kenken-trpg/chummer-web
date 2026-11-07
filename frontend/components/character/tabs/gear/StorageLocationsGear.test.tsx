import { render, screen, within } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { describe, expect, it, vi } from "vitest";
import type { Updater } from "@/lib/character/patch-queue";
import type { Character } from "@/lib/types";
import { makeCharacter, panelProps } from "@/tests/fixtures";
import { StorageLocationsGear } from "./StorageLocationsGear";

/** What a patch made of `updater` sends, read against `ch`. */
function sent(patch: ReturnType<typeof vi.fn>, ch: Character) {
  const body = patch.mock.calls.at(-1)![0];
  return typeof body === "function" ? (body as Updater)(ch) : body;
}

function character() {
  const gear = [
    { id: "kit", gear_id: "g1", location: "bag" },
    { id: "supplies", gear_id: "g2", parent_id: "kit" },
    { id: "rope", gear_id: "g3", nickname: "Old Rope" },
  ];
  const commlinks = [{ id: "link", gear_id: "c1", location: "car" }];
  const armor = [{ id: "coat", armor_id: "a1", location: "closet" }];
  return makeCharacter({
    gear_locations: [
      { id: "bag", name: "Backpack", notes: "" },
      { id: "car", name: "Car", notes: "" },
    ],
    armor_locations: [{ id: "closet", name: "Closet", notes: "" }],
    gear,
    commlinks,
    armor,
    derived: {
      gear: [
        { id: "kit", name: "Medkit" },
        { id: "supplies", name: "Medkit Supplies", parent_id: "kit" },
        { id: "rope", name: "Rope" },
      ],
      commlinks: [{ id: "link", name: "Meta Link" }],
      armor_items: [{ id: "coat", name: "Armor Jacket" }],
    },
  } as never);
}

/** The box of the place called `name`. */
function place(name: string) {
  return screen
    .getByRole("textbox", { name: `${name} の名前` })
    .closest(".cyber-item") as HTMLElement;
}

describe("<StorageLocationsGear>", () => {
  it("shows each place with what is in it, and what is kept nowhere", () => {
    render(<StorageLocationsGear {...panelProps(character())} />);
    expect(within(place("Backpack")).getByText(/Medkit/)).toBeDefined();
    // what is inside the kit goes with the kit, and is not listed apart
    expect(screen.queryByText(/Medkit Supplies/)).toBeNull();
    expect(within(place("Car")).getByText(/Meta Link/)).toBeDefined();
    expect(within(place("Closet")).getByText(/Armor Jacket/)).toBeDefined();
    const nowhere = screen
      .getByText("どこにも入れていないもの")
      .closest(".cyber-item") as HTMLElement;
    expect(within(nowhere).getByText(/Rope（Old Rope）/)).toBeDefined();
  });

  it("moves one thing, against the character as saved", () => {
    const ch = character();
    const patch = vi.fn();
    render(<StorageLocationsGear {...panelProps(ch, { patch })} />);
    fireEvent.change(screen.getByRole("combobox", { name: "Rope（Old Rope） の保管場所" }), {
      target: { value: "car" },
    });
    // the kit was moved meanwhile, which this must not undo
    const saved = {
      ...ch,
      gear: ch.gear!.map((r) => (r.id === "kit" ? { ...r, location: null } : r)),
    };
    const rows = sent(patch, saved).gear as { id: string; location?: string | null }[];
    expect(rows.map((r) => [r.id, r.location ?? null])).toEqual([
      ["kit", null],
      ["supplies", null],
      ["rope", "car"],
    ]);
  });

  it("adds a place, and renames one on leaving its box", () => {
    const ch = character();
    const patch = vi.fn();
    render(<StorageLocationsGear {...panelProps(ch, { patch })} />);
    const box = screen.getByRole("textbox", { name: "装備: 新しい保管場所の名前" });
    fireEvent.change(box, { target: { value: "  Safehouse " } });
    fireEvent.click(within(box.parentElement!).getByRole("button", { name: "追加" }));
    const added = sent(patch, ch).gear_locations as { id: string; name: string }[];
    expect(added.map((p) => p.name)).toEqual(["Backpack", "Car", "Safehouse"]);
    expect(added[2].id).toMatch(/^[0-9a-f-]{36}$/);

    const name = screen.getByRole("textbox", { name: "Car の名前" });
    fireEvent.change(name, { target: { value: "Van" } });
    fireEvent.focusOut(name);
    expect((sent(patch, ch).gear_locations as { name: string }[]).map((p) => p.name)).toEqual([
      "Backpack",
      "Van",
    ]);
  });

  it("deleting a place leaves what was in it kept nowhere", () => {
    const ch = character();
    const patch = vi.fn();
    render(<StorageLocationsGear {...panelProps(ch, { patch })} />);
    fireEvent.click(screen.getByRole("button", { name: "Car を削除" }));
    const body = sent(patch, ch);
    expect((body.gear_locations as { id: string }[]).map((p) => p.id)).toEqual(["bag"]);
    expect((body.commlinks as { location: string | null }[])[0].location).toBeNull();
    // only the lists that had something there; armor has places of its own
    expect(Object.keys(body).sort()).toEqual(["commlinks", "gear_locations"]);
  });
});
