import { fireEvent, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Catalog } from "@/lib/types";
import { makeCharacter } from "@/tests/fixtures";
import { ArmorGear } from "./ArmorGear";
import { CommlinkGear } from "./CommlinkGear";
import { CyberdeckGear } from "./CyberdeckGear";
import { RccGear } from "./RccGear";
import type { Panel } from "./gear-addons.helpers";
import { renderPanel, host } from "./gear-addons.helpers";

/**
 * Mods and carried gear on armor, and electronic modifications on a device —
 * split out of `gear-addons.test.tsx`, which covers programs and nested rows.
 */

describe("<ArmorGear> mods on a piece", () => {
  const piece = (id: string, name: string, mods: Record<string, unknown>[] = []) => ({
    id,
    armor_id: `c-${id}`,
    name,
    armor_value: 9,
    contributes: 9,
    equipped: true,
    rating: 1,
    rating_max: 0,
    nuyen: 900,
    capacity_max: 6,
    capacity_used: 0,
    source: "SR5",
    mods,
  });
  const mod = (
    id: string,
    name: string,
    parent_id: string,
    over: Record<string, unknown> = {},
  ) => ({
    id,
    mod_id: `c-${id}`,
    name,
    parent_id,
    rating: 1,
    rating_max: 1,
    nuyen: 250,
    included: false,
    source: "SR5",
    ...over,
  });

  const character = (mods: Record<string, unknown>[]) =>
    makeCharacter({
      armor: [piece("a1", "Lined Coat"), piece("a2", "Armor Jacket")],
      armor_mods: mods,
      derived: {
        armor_items: [
          piece(
            "a1",
            "Lined Coat",
            mods.filter((m) => m.parent_id === "a1"),
          ),
          piece(
            "a2",
            "Armor Jacket",
            mods.filter((m) => m.parent_id === "a2"),
          ),
        ],
        armor_mods: mods,
      },
    } as never);

  /** A mod that came with the piece is not separately owned: it cannot be
   *  removed or re-rated, only listed. */
  it("shows an included mod without a remove button", () => {
    const { container } = renderPanel(
      ArmorGear,
      character([mod("m1", "Fire Resistance", "a1", { included: true })]),
      vi.fn(),
    );

    const row = [...container.querySelectorAll<HTMLElement>(".cyber-item")][0];
    expect(row.textContent).toContain("Fire Resistance");
    expect(within(row).queryByRole("button", { name: "外す" })).toBeNull();
  });

  it("re-rating a mod edits that mod alone", () => {
    const patch = vi.fn();
    renderPanel(
      ArmorGear,
      character([
        mod("m1", "Fire Resistance", "a1", { rating_max: 6 }),
        mod("m2", "Nonconductivity", "a2", { rating_max: 6 }),
      ]),
      patch,
    );

    fireEvent.change(screen.getAllByRole("spinbutton")[1], { target: { value: "4" } });

    const out = patch.mock.calls[0][0].armor_mods as { id: string; rating: number }[];
    expect(out.find((r) => r.id === "m1")?.rating).toBe(1);
    expect(out.find((r) => r.id === "m2")?.rating).toBe(4);
  });

  it("deleting a piece takes its own mods and only its own", () => {
    const patch = vi.fn();
    renderPanel(
      ArmorGear,
      character([mod("m1", "Fire Resistance", "a1"), mod("m2", "Nonconductivity", "a2")]),
      patch,
    );

    fireEvent.click(screen.getByRole("button", { name: "Lined Coat を削除" }));

    const body = patch.mock.calls[0][0];
    expect((body.armor as { id: string }[]).map((r) => r.id)).toEqual(["a2"]);
    expect((body.armor_mods as { id: string }[]).map((r) => r.id)).toEqual(["m2"]);
  });

  /** Custom Fit (Stack) names the *other* piece it was tailored to, so the
   *  picker offers every piece but its own, and the pick lands on that mod. */
  it("Custom Fit (Stack) picks another piece to stack with", () => {
    const patch = vi.fn();
    renderPanel(
      ArmorGear,
      character([
        mod("m1", "Custom Fit (Stack)", "a1", { included: true, select_armor: true }),
        mod("m2", "Nonconductivity", "a2"),
      ]),
      patch,
    );

    const picker = screen.getByRole("combobox", { name: "重ねる防具" });
    const options = within(picker)
      .getAllByRole("option")
      .map((o) => o.textContent);
    expect(options).toEqual(["—", "Armor Jacket"]);

    fireEvent.change(picker, { target: { value: "Armor Jacket" } });

    const out = patch.mock.calls[0][0].armor_mods as { id: string; stack_with?: string }[];
    expect(out.find((r) => r.id === "m1")?.stack_with).toBe("Armor Jacket");
    expect(out.find((r) => r.id === "m2")?.stack_with).toBeUndefined();
  });
});

describe("<ArmorGear> gear carried in a piece", () => {
  const piece = (id: string, name: string, gear: Record<string, unknown>[] = []) => ({
    id,
    armor_id: `c-${id}`,
    name,
    armor_value: 9,
    contributes: 9,
    equipped: true,
    rating: 1,
    rating_max: 0,
    nuyen: 900,
    capacity_max: 6,
    capacity_used: 3,
    source: "SR5",
    mods: [],
    gear,
  });
  const holster = {
    id: "g1",
    gear_id: "c-holster",
    name: "Holster",
    parent_id: "a1",
    rating: 1,
    rating_max: 0,
    qty: 1,
    nuyen: 150,
    armor_capacity: 3,
    included: false,
  };
  const medkit = {
    id: "g2",
    gear_id: "c-medkit",
    name: "Medkit",
    parent_id: "a2",
    rating: 1,
    rating_max: 6,
    qty: 1,
    nuyen: 250,
    armor_capacity: 5,
    included: false,
  };
  const character = () =>
    makeCharacter({
      armor: [piece("a1", "Lined Coat"), piece("a2", "Armor Jacket")],
      gear: [holster, medkit, { id: "g3", gear_id: "c-x", name: "Rope" }],
      derived: {
        armor_items: [piece("a1", "Lined Coat", [holster]), piece("a2", "Armor Jacket", [medkit])],
      },
    } as never);
  const catalog = {
    gear: [
      {
        id: "c-holster",
        name: "Holster",
        category: "Armor Enhancements",
        cost: "150",
        armor_capacity: "[3]",
      },
      { id: "c-rope", name: "Rope", category: "Survival Gear", cost: "10" },
    ] as never,
  };

  it("lists each piece's own gear and offers only gear that fits in armor", () => {
    const patch = vi.fn();
    const { container } = renderPanel(ArmorGear, character(), patch, catalog);
    const [coat, jacket] = [...container.querySelectorAll<HTMLElement>(".cyber-item")];
    expect(coat.textContent).toContain("Holster");
    expect(coat.textContent).not.toContain("Medkit");
    expect(jacket.textContent).toContain("Medkit");

    const picker = screen.getByRole("combobox", { name: "Armor Jacket: ギアを入れる" });
    expect(within(picker).queryByText(/Rope/)).toBeNull();
    fireEvent.change(picker, { target: { value: "c-holster" } });
    fireEvent.click(screen.getByRole("button", { name: "Armor Jacket: 入れる" }));
    const added = (patch.mock.calls[0][0].gear as { gear_id: string; parent_id?: string }[]).at(-1);
    expect(added).toMatchObject({ gear_id: "c-holster", parent_id: "a2" });
  });

  it("a vision enhancement goes in the optics list, on the helmet it is put in", () => {
    const patch = vi.fn();
    renderPanel(ArmorGear, character(), patch, {
      ...catalog,
      optics: [
        {
          id: "c-vm",
          name: "Vision Magnification",
          category: "Vision Enhancements",
          cost: "250",
          armor_capacity: "[1]",
        },
      ] as never,
      sensors: [
        {
          id: "c-ss",
          name: "Single Sensor",
          category: "Sensors",
          cost: "100",
          armor_capacity: "[1]",
        },
        {
          id: "c-sf",
          name: "Vision Magnification",
          category: "Sensor Functions",
          cost: "250",
          armor_capacity: "[1]",
        },
      ] as never,
    });
    const picker = screen.getByRole("combobox", { name: "Lined Coat: ギアを入れる" });
    // a sensor function goes in its housing, not straight in the armor
    expect(
      within(picker)
        .getAllByRole("option")
        .filter((o) => o.textContent?.startsWith("Vision Magnification")),
    ).toHaveLength(1);
    fireEvent.change(picker, { target: { value: "c-vm" } });
    fireEvent.click(screen.getByRole("button", { name: "Lined Coat: 入れる" }));
    expect(patch.mock.calls[0][0]).toEqual({
      optics: [{ gear_id: "c-vm", parent_id: "a1", rating: 1 }],
    });
  });

  it("a sensor carried in armor takes its functions there", () => {
    const patch = vi.fn();
    const sensor = {
      id: "s1",
      gear_id: "c-ss",
      name: "Single Sensor",
      parent_id: "a1",
      rating: 1,
      rating_max: 0,
      nuyen: 100,
      armor_capacity: 1,
      bucket: "sensors" as const,
      addoncategories: ["Sensor Functions"],
      included: false,
    };
    const fn = {
      id: "s2",
      gear_id: "c-cam",
      name: "Camera",
      parent_id: "s1",
      rating: 1,
      rating_max: 0,
      nuyen: 50,
      capacity_cost: 1,
      included: false,
    };
    const ch = makeCharacter({
      armor: [piece("a1", "Lined Coat")],
      sensors: [sensor, fn],
      derived: {
        armor_items: [piece("a1", "Lined Coat", [sensor])],
        sensors: [sensor, fn],
      },
    } as never);
    renderPanel(ArmorGear, ch, patch, {
      sensors: [
        { id: "c-cam", name: "Camera", category: "Sensor Functions", cost: "50", source: "SR5" },
        {
          id: "c-mic",
          name: "Microphone",
          category: "Sensor Functions",
          cost: "50",
          source: "SR5",
        },
      ] as never,
    });

    expect(screen.getByText(/Camera/)).toBeTruthy();
    // the one already in it is not offered again
    const picker = screen.getByRole("combobox", { name: "Single Sensor: 機能を追加" });
    expect(
      within(picker)
        .getAllByRole("option")
        .map((o) => o.textContent),
    ).toEqual(["機能を追加", "Microphone (50¥)"]);
    fireEvent.change(picker, { target: { value: "c-mic" } });
    fireEvent.click(screen.getByRole("button", { name: "Single Sensor: 装着" }));
    const out = patch.mock.calls[0][0].sensors as { gear_id: string; parent_id?: string }[];
    expect(out.at(-1)).toMatchObject({ gear_id: "c-mic", parent_id: "s1" });
  });

  it("deleting a piece takes the gear carried in it and only that", () => {
    const patch = vi.fn();
    renderPanel(ArmorGear, character(), patch, catalog);
    fireEvent.click(screen.getByRole("button", { name: "Lined Coat を削除" }));
    expect((patch.mock.calls[0][0].gear as { id: string }[]).map((r) => r.id)).toEqual([
      "g2",
      "g3",
    ]);
  });
});

/**
 * A Data Trails Electronic Modification (DT p.66) is soldered into a device
 * rather than plugged into it, and all three device panels take one. The
 * commlink panel already listed its gear children for accessories, so the
 * thing to keep true there is that a modification is not drawn twice.
 */
const MOD_HOSTS: [string, Panel, string, string][] = [
  ["CommlinkGear", CommlinkGear, "commlinks", "commlinks"],
  ["CyberdeckGear", CyberdeckGear, "cyberdecks", "cyberdecks"],
  ["RccGear", RccGear, "rccs", "rccs"],
];

const modCatalog = {
  gear: [
    {
      id: "m1",
      name: "Increase Attack Modification",
      category: "Electronic Modification",
      cost: "0",
      avail: "0",
      source: "DT",
      page: "66",
      minrating: 0,
      maxrating: 0,
    },
  ],
} as Partial<Catalog>;

describe.each(MOD_HOSTS)("<%s> electronic modifications", (_name, Panel, chKey, dKey) => {
  const installed = {
    id: "g1",
    gear_id: "m1",
    name: "Increase Attack Modification",
    category: "Electronic Modification",
    rating: 1,
    rating_max: 0,
    parent_id: "h1",
    qty: 1,
    nuyen: 0,
    source: "DT",
  };
  const character = () =>
    makeCharacter({
      [chKey]: [host("h1", "First"), host("h2", "Second")],
      gear: [installed],
      derived: {
        [dKey]: [host("h1", "First"), host("h2", "Second")],
        gear: [installed],
      },
    } as never);

  it("draws the modification once, under the device it names", () => {
    const { container } = renderPanel(Panel, character(), vi.fn(), modCatalog);

    // the name is also an <option> in every device's select, so what says a
    // modification is *installed* here is its own remove button
    const label = "Increase Attack Modification を外す";
    const rows = [...container.querySelectorAll<HTMLElement>(".cyber-item")];
    expect(within(rows[0]).getAllByRole("button", { name: label })).toHaveLength(1);
    expect(within(rows[1]).queryByRole("button", { name: label })).toBeNull();
  });

  it("adds one to the device the select belongs to", () => {
    const patch = vi.fn();
    const { container } = renderPanel(Panel, character(), patch, modCatalog);

    const second = container.querySelectorAll<HTMLElement>(".cyber-item")[1];
    const select = within(second).getByRole("combobox", { name: "Second: 改造を追加" });
    fireEvent.change(select, { target: { value: "m1" } });
    // the panels carry several "装着" buttons; this one is the select's own
    fireEvent.click(within(select.parentElement!).getByRole("button"));

    const added = (patch.mock.calls[0][0].gear as { gear_id: string; parent_id: string }[]).at(-1);
    expect(added).toMatchObject({ gear_id: "m1", parent_id: "h2" });
  });

  it("deleting the device takes its modifications with it", () => {
    const patch = vi.fn();
    const { container } = renderPanel(Panel, character(), patch, modCatalog);

    const first = container.querySelectorAll<HTMLElement>(".cyber-item")[0];
    fireEvent.click(within(first).getByRole("button", { name: "削除" }));

    expect(patch.mock.calls[0][0].gear).toEqual([]);
  });
});
