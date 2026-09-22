import { fireEvent, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { makeCatalog } from "@/tests/fixtures";
import { weapon, accessory, renderWeapons, owning, installNextTo } from "./weapon-gear.helpers";

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
        // a supplement accessory: on the list unless the settings drop R5
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
    } as never);

  // The list used to be `specialmodification || source === "SR5"` — a book
  // list written in code, which no setting could reach: 110 of the 136
  // accessories in the real catalog were unreachable however the GM set up
  // the table.
  const fitted = () =>
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
    );
  const accessoryOptions = () =>
    [
      ...screen
        .getByRole("combobox", { name: "Predator: アクセサリを追加" })
        .querySelectorAll("option"),
    ].map((o) => o.textContent);

  it("offers every accessory the books allow, minus what is fitted", () => {
    renderWeapons(fitted(), vi.fn(), catalog());
    expect(accessoryOptions()).toEqual([
      "アクセサリを追加",
      "Smartgun System (200¥)",
      "Melee Hardening (50¥)",
      "Custom Look (改造1)",
    ]);
  });

  it("drops the accessories whose book the settings turned off", () => {
    renderWeapons(fitted(), vi.fn(), catalog(), ["SR5"]);
    expect(accessoryOptions()).toEqual(["アクセサリを追加", "Smartgun System (200¥)"]);
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
