import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Character } from "@/lib/types";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";
import { WeaponGear } from "./WeaponGear";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * A weapon row on screen is not necessarily a weapon in the character.
 *
 * `d.weapons` merges three sources: weapons the character bought, weapons that
 * come out of a piece of gear (`from_gear`), and weapons that are part of
 * cyberware (`from_ware`). They look identical in the list, and every control
 * on the row has to patch whichever list the row actually came from. Deleting
 * a gear-backed weapon by filtering `ch.weapons` removes nothing — the row is
 * regenerated from the gear on the next compute — so the bug is not a crash
 * but a button that visibly does nothing.
 *
 * `gear-owned.test.tsx` covers the plain case. This file covers the other two,
 * plus the accessory and ammunition subtrees, which patch `weapon_accessories`
 * and `gear` respectively while rendering underneath the weapon.
 */

const weapon = (id: string, name: string, over: Record<string, unknown> = {}) => ({
  id,
  name,
  weapon_id: `c-${id}`,
  category: "Heavy Pistols",
  type: "Ranged",
  weapon_type: "Heavy Pistols",
  damage: "8P",
  ap: "-1",
  accuracy: "5",
  mode: "SA",
  rc: "0",
  qty: 1,
  nuyen: 725,
  source: "SR5",
  mounts: ["Barrel", "Top", "Under"],
  accessories: [],
  ammo_gear: [],
  ...over,
});

const accessory = (id: string, name: string, over: Record<string, unknown> = {}) => ({
  id,
  name,
  accessory_id: `c-${id}`,
  mount: "Top",
  nuyen: 250,
  included: false,
  ...over,
});

const ammoRow = (id: string, name: string, over: Record<string, unknown> = {}) => ({
  id,
  name,
  gear_id: `c-${id}`,
  qty: 1,
  nuyen: 40,
  loaded: false,
  ammo_weapon_types: ["Heavy Pistols"],
  ...over,
});

function renderWeapons(
  ch: Character,
  patch: (b: Record<string, unknown>) => void,
  catalog = makeCatalog(),
) {
  return render(
    <WeaponGear
      catalog={catalog}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      trGroup={identityTr}
      t={((k: string) => k) as any}
      ui={testUi}
      patch={patch as any}
      setCharacter={() => {}}
    />,
  );
}

/** A character owning the given weapons, mirrored into `derived`. */
function owning(rows: Record<string, unknown>[], rest: Record<string, unknown> = {}): Character {
  const { derived = {}, ...top } = rest;
  return makeCharacter({
    weapons: rows,
    ...top,
    derived: { weapons: rows, ...(derived as object) },
  } as any);
}

/** The 装着 button belonging to one picker — a weapon has two. */
function installNextTo(select: HTMLElement) {
  return within(select.parentElement as HTMLElement).getByRole("button", { name: "装着" });
}

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

describe("<WeaponGear> accessories", () => {
  const catalog = () =>
    makeCatalog({
      weapons: [{ id: "c-w1", name: "Predator", cost: "725" }],
      weapon_accessories: [
        { id: "a-smart", name: "Smartgun System", cost: "200", source: "SR5", mounts: ["Top"] },
        {
          id: "a-laser",
          name: "Laser Sight",
          cost: "125",
          source: "SR5",
          mounts: ["Top", "Under"],
        },
        // a supplement accessory: kept out of the list
        { id: "a-sg", name: "Melee Hardening", cost: "50", source: "R5", mounts: ["Top"] },
        // a special modification is offered whatever book it comes from,
        // but only while the character has room left for one
        {
          id: "a-mod",
          name: "Custom Look",
          cost: "0",
          source: "R5",
          mounts: ["Internal"],
          specialmodification: true,
          special_modification_cost: 1,
        },
      ],
    } as any);

  it("offers core accessories plus special modifications, minus what is fitted", () => {
    renderWeapons(
      owning(
        [
          weapon("w1", "Predator", {
            accessories: [accessory("acc1", "Laser Sight", { accessory_id: "a-laser" })],
          }),
        ],
        {
          weapon_accessories: [{ id: "acc1", accessory_id: "a-laser", parent_id: "w1" }],
          derived: { special_modification_limit: { used: 0, max: 3 } },
        },
      ),
      vi.fn(),
      catalog(),
    );

    const select = screen.getByRole("combobox", { name: "Predator: アクセサリを追加" });
    const options = [...select.querySelectorAll("option")].map((o) => o.textContent);
    expect(options).toEqual(["アクセサリを追加", "Smartgun System (200¥)", "Custom Look (改造1)"]);
  });

  it("stops offering special modifications once the allowance is spent", () => {
    renderWeapons(
      owning([weapon("w1", "Predator")], {
        derived: { special_modification_limit: { used: 3, max: 3 } },
      }),
      vi.fn(),
      catalog(),
    );

    const select = screen.getByRole("combobox", { name: "Predator: アクセサリを追加" });
    const options = [...select.querySelectorAll("option")].map((o) => o.textContent);
    expect(options).not.toContain("Custom Look (改造1)");
  });

  it("shows the allowance only when the character has one", () => {
    const { container, unmount } = renderWeapons(owning([weapon("w1", "Predator")]), vi.fn());
    expect(container.textContent).not.toContain("Special Modifications");
    unmount();

    const withLimit = renderWeapons(
      owning([weapon("w1", "Predator")], {
        derived: { special_modification_limit: { used: 1, max: 3 } },
      }),
      vi.fn(),
    );
    expect(withLimit.container.textContent).toContain("Special Modifications 1 / 3");
  });

  it("installs the chosen accessory on that weapon", () => {
    const patch = vi.fn();
    renderWeapons(owning([weapon("w1", "Predator")]), patch, catalog());

    const select = screen.getByRole("combobox", { name: "Predator: アクセサリを追加" });
    fireEvent.change(select, { target: { value: "a-smart" } });
    fireEvent.click(installNextTo(select));

    expect(patch.mock.calls[0][0].weapon_accessories).toEqual([
      { accessory_id: "a-smart", parent_id: "w1" },
    ]);
  });

  it("removes one accessory and keeps the rest", () => {
    const patch = vi.fn();
    renderWeapons(
      owning(
        [
          weapon("w1", "Predator", {
            accessories: [accessory("acc1", "Laser Sight"), accessory("acc2", "Smartgun System")],
          }),
        ],
        {
          weapon_accessories: [
            { id: "acc1", accessory_id: "a-laser", parent_id: "w1" },
            { id: "acc2", accessory_id: "a-smart", parent_id: "w1" },
          ],
        },
      ),
      patch,
    );

    fireEvent.click(screen.getAllByRole("button", { name: "外す" })[1]);

    const rows = patch.mock.calls[0][0].weapon_accessories as { id: string }[];
    expect(rows.map((r) => r.id)).toEqual(["acc1"]);
  });

  it("an accessory that comes with the weapon cannot be removed", () => {
    renderWeapons(
      owning([
        weapon("w1", "Predator", {
          accessories: [accessory("acc1", "Smartgun System", { included: true })],
        }),
      ]),
      vi.fn(),
    );

    expect(screen.queryByRole("button", { name: "外す" })).toBeNull();
  });

  it("a gear-backed weapon takes no accessories", () => {
    renderWeapons(
      owning([weapon("w1", "Grenade", { from_gear: true, source_gear_id: "g1" })], { weapons: [] }),
      vi.fn(),
      catalog(),
    );

    expect(screen.queryByRole("combobox", { name: /アクセサリを追加/ })).toBeNull();
  });
});

describe("<WeaponGear> ammunition", () => {
  const catalog = () =>
    makeCatalog({
      gear: [
        {
          id: "g-reg",
          name: "Ammo: Regular",
          category: "Ammunition",
          cost: "20",
          costfor: 10,
          source: "SR5",
          ammo_weapon_types: ["Heavy Pistols"],
        },
        {
          id: "g-apds",
          name: "Ammo: APDS",
          category: "Ammunition",
          cost: "120",
          costfor: 10,
          source: "SR5",
          minrating: 2,
          ammo_weapon_types: ["Heavy Pistols"],
        },
        // for a different weapon type entirely
        {
          id: "g-shot",
          name: "Ammo: Shotgun Slug",
          category: "Ammunition",
          cost: "40",
          source: "SR5",
          ammo_weapon_types: ["Shotguns"],
        },
      ],
    } as any);

  it("offers only ammunition the weapon can chamber, minus what it already carries", () => {
    renderWeapons(
      owning(
        [
          weapon("w1", "Predator", {
            ammo_gear: [ammoRow("am1", "Ammo: Regular", { gear_id: "g-reg" })],
          }),
        ],
        {
          gear: [{ id: "am1", gear_id: "g-reg", parent_id: "w1" }],
        },
      ),
      vi.fn(),
      catalog(),
    );

    const select = screen.getByRole("combobox", { name: "Predator: 弾薬を追加" });
    const options = [...select.querySelectorAll("option")].map((o) => o.textContent);
    expect(options).toEqual(["弾薬を追加", "Ammo: APDS (120¥ / 10発)"]);
  });

  it("adds it at the catalog minimum rating, parented to the weapon", () => {
    const patch = vi.fn();
    renderWeapons(owning([weapon("w1", "Predator")]), patch, catalog());

    const select = screen.getByRole("combobox", { name: "Predator: 弾薬を追加" });
    fireEvent.change(select, { target: { value: "g-apds" } });
    fireEvent.click(installNextTo(select));

    expect(patch.mock.calls[0][0].gear).toEqual([
      { gear_id: "g-apds", rating: 2, parent_id: "w1" },
    ]);
  });

  it("loading a magazine marks that weapon only", () => {
    const patch = vi.fn();
    renderWeapons(
      owning(
        [
          weapon("w1", "Predator", { ammo_gear: [ammoRow("am1", "Ammo: APDS")] }),
          weapon("w2", "Warhawk", { ammo_gear: [ammoRow("am2", "Ammo: Regular")] }),
        ],
        {
          gear: [
            { id: "am1", parent_id: "w1" },
            { id: "am2", parent_id: "w2" },
          ],
        },
      ),
      patch,
    );

    fireEvent.click(screen.getAllByRole("button", { name: "装填" })[1]);

    const rows = patch.mock.calls[0][0].weapons as { id: string; loaded_ammo_id?: string }[];
    expect(rows.find((r) => r.id === "w1")?.loaded_ammo_id).toBeUndefined();
    expect(rows.find((r) => r.id === "w2")?.loaded_ammo_id).toBe("am2");
  });

  it("offers no load button for a magazine already in the gun", () => {
    renderWeapons(
      owning([
        weapon("w1", "Predator", { ammo_gear: [ammoRow("am1", "Ammo: APDS", { loaded: true })] }),
      ]),
      vi.fn(),
    );

    expect(screen.queryByRole("button", { name: "装填" })).toBeNull();
    expect(screen.getByText(/装填中/)).toBeDefined();
  });

  it("discarding the loaded magazine also unloads the weapon", () => {
    // a loaded_ammo_id pointing at a gear row that no longer exists is a
    // dangling reference the sheet renders as a blank
    const patch = vi.fn();
    renderWeapons(
      owning(
        [
          weapon("w1", "Predator", {
            loaded_ammo_id: "am1",
            ammo_gear: [ammoRow("am1", "Ammo: APDS", { loaded: true })],
          }),
        ],
        { gear: [{ id: "am1", parent_id: "w1" }], weapons: [{ id: "w1", loaded_ammo_id: "am1" }] },
      ),
      patch,
    );

    fireEvent.click(screen.getByRole("button", { name: "外す" }));

    const body = patch.mock.calls[0][0];
    expect(body.gear).toEqual([]);
    expect((body.weapons as { loaded_ammo_id?: string }[])[0].loaded_ammo_id).toBeUndefined();
  });

  it("discarding a magazine that is not loaded leaves the loaded one alone", () => {
    const patch = vi.fn();
    renderWeapons(
      owning(
        [
          weapon("w1", "Predator", {
            loaded_ammo_id: "am1",
            ammo_gear: [
              ammoRow("am1", "Ammo: APDS", { loaded: true }),
              ammoRow("am2", "Ammo: Regular"),
            ],
          }),
        ],
        {
          gear: [
            { id: "am1", parent_id: "w1" },
            { id: "am2", parent_id: "w1" },
          ],
          weapons: [{ id: "w1", loaded_ammo_id: "am1" }],
        },
      ),
      patch,
    );

    // the loaded one has no 装填 button, so 外す[1] is the spare magazine
    fireEvent.click(screen.getAllByRole("button", { name: "外す" })[1]);

    const body = patch.mock.calls[0][0];
    expect((body.gear as { id: string }[]).map((r) => r.id)).toEqual(["am1"]);
    expect((body.weapons as { loaded_ammo_id?: string }[])[0].loaded_ammo_id).toBe("am1");
  });

  it("changing one magazine's count leaves the other alone", () => {
    const patch = vi.fn();
    renderWeapons(
      owning(
        [
          weapon("w1", "Predator", {
            ammo_gear: [ammoRow("am1", "Ammo: APDS"), ammoRow("am2", "Ammo: Regular")],
          }),
        ],
        {
          gear: [
            { id: "am1", qty: 1 },
            { id: "am2", qty: 1 },
          ],
        },
      ),
      patch,
    );

    // spinbutton 0 is the weapon's own quantity
    fireEvent.change(screen.getAllByRole("spinbutton")[2], { target: { value: "4" } });

    const rows = patch.mock.calls[0][0].gear as { id: string; qty: number }[];
    expect(rows.find((r) => r.id === "am1")?.qty).toBe(1);
    expect(rows.find((r) => r.id === "am2")?.qty).toBe(4);
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
      } as any),
    );

    fireEvent.click(screen.getByRole("button", { name: /Grenade: Frag/ }));

    expect(patch.mock.calls[0][0]).toEqual({ gear: [{ gear_id: "g-gren", qty: 1 }] });
  });

  it("adds an ordinary weapon to weapons", () => {
    const patch = vi.fn();
    renderWeapons(
      owning([]),
      patch,
      makeCatalog({
        weapons: [{ id: "c-w1", name: "Predator", cost: "725", source: "SR5" }],
      } as any),
    );

    fireEvent.click(screen.getByRole("button", { name: /Predator/ }));

    expect(patch.mock.calls[0][0]).toEqual({ weapons: [{ weapon_id: "c-w1", qty: 1 }] });
  });
});
