import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { makeCatalog } from "@/tests/fixtures";
import { weapon, renderWeapons, owning } from "./weapon-gear.helpers";

describe("<WeaponGear> where a row actually lives", () => {
  it("deletes a bought weapon along with its accessories and its ammunition", () => {
    const patch = vi.fn();
    renderWeapons(
      owning([weapon("w1", "Predator"), weapon("w2", "Warhawk")], {
        weapon_accessories: [
          { id: "acc1", accessory_id: "ca1", parent_id: "w1" },
          { id: "acc2", accessory_id: "ca2", parent_id: "w2" },
        ],
        gear: [
          { id: "am1", gear_id: "cg1", parent_id: "w1" },
          { id: "am2", gear_id: "cg2", parent_id: "w2" },
        ],
      }),
      patch,
    );

    fireEvent.click(screen.getAllByRole("button", { name: "削除" })[0]);

    const body = patch.mock.calls[0][0];
    expect((body.weapons as { id: string }[]).map((r) => r.id)).toEqual(["w2"]);
    // an accessory or a magazine left behind belongs to a weapon that is gone
    expect((body.weapon_accessories as { id: string }[]).map((r) => r.id)).toEqual(["acc2"]);
    expect((body.gear as { id: string }[]).map((r) => r.id)).toEqual(["am2"]);
  });

  it("deletes a gear-backed weapon out of gear, because it is not in weapons", () => {
    // filtering ch.weapons here removes nothing: the row is regenerated from
    // the gear entry on the next compute, so the button just looks broken
    const patch = vi.fn();
    renderWeapons(
      owning([weapon("w1", "Grenade", { from_gear: true, source_gear_id: "g1" })], {
        weapons: [],
        gear: [
          { id: "g1", gear_id: "cg1" },
          { id: "g1a", gear_id: "cg2", parent_id: "g1" },
          { id: "g2", gear_id: "cg3" },
        ],
      }),
      patch,
    );

    fireEvent.click(screen.getByRole("button", { name: "削除" }));

    const body = patch.mock.calls[0][0];
    expect(body.weapons).toBeUndefined();
    // dropTree: whatever was plugged into the gear goes with it
    expect((body.gear as { id: string }[]).map((r) => r.id)).toEqual(["g2"]);
  });

  it("deletes a cyberware weapon by removing the ware it belongs to", () => {
    const patch = vi.fn();
    renderWeapons(
      owning([weapon("w1", "Spurs", { from_ware: true, source_ware_id: "cw1" })], {
        weapons: [],
        cyberware: [
          { id: "cw1", ware_id: "c1" },
          { id: "cw1a", ware_id: "c2", parent_id: "cw1" },
          { id: "cw2", ware_id: "c3" },
        ],
      }),
      patch,
    );

    fireEvent.click(screen.getByRole("button", { name: "削除" }));

    const body = patch.mock.calls[0][0];
    expect((body.cyberware as { id: string }[]).map((r) => r.id)).toEqual(["cw2"]);
  });

  it("deletes a bioware weapon out of bioware, not out of cyberware", () => {
    // Claws are `<addweapon>` bioware (CF p.72): the same `from_ware` row as a
    // cyberspur, but filtering `cyberware` for it would remove nothing.
    const patch = vi.fn();
    renderWeapons(
      owning(
        [weapon("w1", "Claws", { from_ware: true, source_ware_id: "bw1", ware_kind: "bioware" })],
        {
          weapons: [],
          bioware: [
            { id: "bw1", ware_id: "b1" },
            { id: "bw2", ware_id: "b2" },
          ],
        },
      ),
      patch,
    );

    fireEvent.click(screen.getByRole("button", { name: "削除" }));

    const body = patch.mock.calls[0][0];
    expect((body.bioware as { id: string }[]).map((r) => r.id)).toEqual(["bw2"]);
    expect(body.cyberware).toBeUndefined();
  });

  it("deletes a shield by dropping the armor it is, along with its mods", () => {
    const patch = vi.fn();
    renderWeapons(
      owning([weapon("w1", "Ballistic Shield", { from_armor: true, source_armor_id: "a1" })], {
        weapons: [],
        armor: [
          { id: "a1", armor_id: "ca1" },
          { id: "a2", armor_id: "ca2" },
        ],
        armor_mods: [
          { id: "am1", mod_id: "cm1", parent_id: "a1" },
          { id: "am2", mod_id: "cm2", parent_id: "a2" },
        ],
      }),
      patch,
    );

    fireEvent.click(screen.getByRole("button", { name: "削除" }));

    const body = patch.mock.calls[0][0];
    expect((body.armor as { id: string }[]).map((r) => r.id)).toEqual(["a2"]);
    expect((body.armor_mods as { id: string }[]).map((r) => r.id)).toEqual(["am2"]);
  });

  it("gives a shield no quantity of its own — the armor row owns that", () => {
    renderWeapons(
      owning([weapon("w1", "Ballistic Shield", { from_armor: true, source_armor_id: "a1" })], {
        weapons: [],
        armor: [{ id: "a1", armor_id: "ca1" }],
      }),
      vi.fn(),
    );

    expect(screen.queryByRole("spinbutton")).toBeNull();
  });

  it("sends a gear-backed weapon's quantity to the gear row, not the weapon", () => {
    const patch = vi.fn();
    renderWeapons(
      owning([weapon("w1", "Grenade", { from_gear: true, source_gear_id: "g1", qty: 2 })], {
        weapons: [],
        gear: [
          { id: "g1", gear_id: "cg1", qty: 2 },
          { id: "g2", gear_id: "cg2", qty: 1 },
        ],
      }),
      patch,
    );

    fireEvent.change(screen.getByRole("spinbutton"), { target: { value: "5" } });

    const rows = patch.mock.calls[0][0].gear as { id: string; qty: number }[];
    expect(rows.find((r) => r.id === "g1")?.qty).toBe(5);
    expect(rows.find((r) => r.id === "g2")?.qty).toBe(1);
  });

  it("gives a cyberware weapon no quantity at all — you have the ware or you don't", () => {
    renderWeapons(
      owning([weapon("w1", "Spurs", { from_ware: true, source_ware_id: "cw1" })], { weapons: [] }),
      vi.fn(),
    );

    expect(screen.queryByRole("spinbutton")).toBeNull();
  });
});

describe("<WeaponGear> buying from the catalog", () => {
  it("adds a weapon that is really a gear entry to gear instead", () => {
    // grenades and the like live in the weapon list but are bought as gear;
    // adding one to `weapons` produces a row the engine cannot price
    const patch = vi.fn();
    renderWeapons(
      owning([]),
      patch,
      makeCatalog({
        weapons: [
          {
            id: "c-gren",
            name: "Grenade: Frag",
            cost: "100",
            source: "SR5",
            add_gear_id: "g-gren",
          },
        ],
      } as never),
    );

    fireEvent.click(screen.getByRole("button", { name: /Grenade: Frag/ }));

    expect(patch.mock.calls[0][0]).toEqual({ gear: [{ gear_id: "g-gren", qty: 1 }] });
  });

  it("offers nothing to change on a weapon the character was born with", () => {
    // A `<naturalweapon>` row exists only in `derived` — there is no entry in
    // `weapons`, `gear` or `cyberware` behind it, so every control that patches
    // one of those lists would be a button that does nothing.
    const patch = vi.fn();
    renderWeapons(
      owning(
        [
          weapon("nat-0", "Bite (Ursine Form)", {
            weapon_id: "",
            category: "Unarmed",
            type: "Melee",
            damage: "({STR}+2)P",
            nuyen: 0,
            natural: true,
            natural_source: "Shapeshifter: Ursine",
          }),
        ],
        { weapons: [] },
      ),
      patch,
    );

    expect(screen.getByText(/Shapeshifter: Ursine/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "削除" })).toBeNull();
    // The "?" that explains the stat line patches nothing, so it belongs here;
    // what must not be is a *control* naming this weapon.
    expect(screen.getByLabelText("Bite (Ursine Form) の説明")).toBeTruthy();
    expect(
      screen
        .queryAllByLabelText(/Bite \(Ursine Form\)/)
        .filter((el) => el.className !== "help-tip-button"),
    ).toHaveLength(0);
    expect(screen.queryByRole("spinbutton")).toBeNull();
  });

  it("adds an ordinary weapon to weapons", () => {
    const patch = vi.fn();
    renderWeapons(
      owning([]),
      patch,
      makeCatalog({
        weapons: [{ id: "c-w1", name: "Predator", cost: "725", source: "SR5" }],
      } as never),
    );

    fireEvent.click(screen.getByRole("button", { name: /Predator/ }));

    expect(patch.mock.calls[0][0]).toEqual({ weapons: [{ weapon_id: "c-w1", qty: 1 }] });
  });
});
