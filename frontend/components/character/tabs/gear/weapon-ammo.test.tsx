import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { makeCatalog } from "@/tests/fixtures";
import { weapon, ammoRow, renderWeapons, owning, installNextTo } from "./weapon-gear.helpers";

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
    } as never);

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
