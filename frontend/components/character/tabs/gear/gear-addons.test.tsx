import { fireEvent, render, screen, within } from "@testing-library/react";
import type { ComponentType } from "react";
import { describe, expect, it, vi } from "vitest";
import type { Catalog, Character } from "@/lib/types";
import type { TabPanelProps } from "@/components/character/types";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";
import { ArmorGear } from "./ArmorGear";
import { CommlinkGear } from "./CommlinkGear";
import { CyberdeckGear } from "./CyberdeckGear";
import { OpticsGear } from "./OpticsGear";
import { RccGear } from "./RccGear";
import { SensorGear } from "./SensorGear";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * `gear-panels.test.tsx` covers buying, `gear-owned.test.tsx` the top-level
 * owned row. This covers what hangs *off* a row: programs on a deck or an RCC,
 * sensors inside a housing, upgrades inside a sight.
 *
 * Two things go wrong here and nowhere else. A child is drawn under whichever
 * host `parent_id` names, so a panel that filters on the wrong id renders the
 * same list under every host and no single-host test can tell. And deleting a
 * host has to take its own children with it and *only* its own — a filter on
 * `parent_id !== item.id` is right for a flat list and wrong for a nested one,
 * where `dropTree` walks the subtree. So every case here has **two** hosts.
 */

type Panel = ComponentType<TabPanelProps> | ComponentType<any>;

function renderPanel(
  Panel: Panel,
  character: Character,
  patch: (b: Record<string, unknown>) => void,
  catalog: Partial<Catalog> = {},
) {
  return render(<Panel {...panelProps(character, { catalog: makeCatalog(catalog), patch })} />);
}

const host = (id: string, name: string) => ({
  id,
  gear_id: `c-${id}`,
  name,
  category: "",
  rating: 1,
  rating_max: 0,
  device_rating: 1,
  attack: 1,
  sleaze: 1,
  dataprocessing: 1,
  firewall: 1,
  programs: 2,
  nuyen: 1000,
  source: "SR5",
});

const program = (
  id: string,
  name: string,
  parent_id: string,
  over: Record<string, unknown> = {},
) => ({
  id,
  gear_id: `c-${id}`,
  name,
  category: "Common Programs",
  rating: 1,
  rating_max: 0,
  parent_id,
  nuyen: 80,
  source: "SR5",
  ...over,
});

// The two panels that hang a flat list of programs off a host.
const PROGRAM_HOSTS: [string, Panel, string, string][] = [
  ["CyberdeckGear", CyberdeckGear, "cyberdecks", "cyberdecks"],
  ["RccGear", RccGear, "rccs", "rccs"],
];

describe.each(PROGRAM_HOSTS)("<%s> programs on a host", (_name, Panel, chKey, dKey) => {
  const character = () =>
    makeCharacter({
      [chKey]: [host("h1", "First"), host("h2", "Second")],
      programs: [
        program("p1", "Browse", "h1"),
        program("p2", "Toolbox", "h2"),
        program("p3", "Edit", "h2"),
      ],
      derived: {
        [dKey]: [host("h1", "First"), host("h2", "Second")],
        programs: [
          program("p1", "Browse", "h1"),
          program("p2", "Toolbox", "h2"),
          program("p3", "Edit", "h2"),
        ],
      },
    } as any);

  it("draws each program under the host it names, not under both", () => {
    const { container } = renderPanel(Panel, character(), vi.fn());

    const rows = [...container.querySelectorAll<HTMLElement>(".cyber-item")];
    expect(rows).toHaveLength(2);
    expect(rows[0].textContent).toContain("Browse");
    expect(rows[0].textContent).not.toContain("Toolbox");
    expect(rows[1].textContent).toContain("Toolbox");
    expect(rows[1].textContent).toContain("Edit");
  });

  it("removing one program leaves the others and every host", () => {
    const patch = vi.fn();
    const { container } = renderPanel(Panel, character(), patch);

    const second = container.querySelectorAll<HTMLElement>(".cyber-item")[1];
    fireEvent.click(within(second).getAllByRole("button", { name: "外す" })[0]);

    const body = patch.mock.calls[0][0];
    expect((body.programs as { id: string }[]).map((r) => r.id)).toEqual(["p1", "p3"]);
    expect(body[chKey]).toBeUndefined(); // the host list is untouched
  });

  it("deleting a host takes its own programs and only its own", () => {
    const patch = vi.fn();
    const { container } = renderPanel(Panel, character(), patch);

    const second = container.querySelectorAll<HTMLElement>(".cyber-item")[1];
    fireEvent.click(within(second).getByRole("button", { name: "削除" }));

    const body = patch.mock.calls[0][0];
    expect((body[chKey] as { id: string }[]).map((r) => r.id)).toEqual(["h1"]);
    expect((body.programs as { id: string }[]).map((r) => r.id)).toEqual(["p1"]);
  });

  it("a rated program's rating box edits that program alone", () => {
    const rows = [program("p1", "Browse", "h1", { rating_max: 6, rating: 2 })];
    const ch = makeCharacter({
      [chKey]: [host("h1", "First")],
      programs: [...rows, program("p9", "Elsewhere", "h9", { rating_max: 6, rating: 2 })],
      derived: {
        [dKey]: [host("h1", "First")],
        programs: [...rows, program("p9", "Elsewhere", "h9", { rating_max: 6, rating: 2 })],
      },
    } as any);
    const patch = vi.fn();
    renderPanel(Panel, ch, patch);

    // the host itself has no rating box here (rating_max 0), so this is p1's
    fireEvent.change(screen.getByRole("spinbutton"), { target: { value: "5" } });

    const out = patch.mock.calls[0][0].programs as { id: string; rating: number }[];
    expect(out.find((r) => r.id === "p1")?.rating).toBe(5);
    expect(out.find((r) => r.id === "p9")?.rating).toBe(2);
  });
});

/**
 * An autosoft names the thing it covers — a skill, a skill group, or a vehicle
 * model that no catalog can enumerate. `AddonSelect` renders a different
 * control for each, and the RCC panel is the only place all three appear.
 */
describe("<RccGear> an autosoft that needs a target", () => {
  const rcc = () =>
    makeCharacter({
      rccs: [host("h1", "Gridlink")],
      programs: [],
      derived: { rccs: [host("h1", "Gridlink")], programs: [] },
    } as any);

  const autosoft = (id: string, name: string, extra_kind: string, options: string[]) => ({
    id,
    name,
    category: "Autosofts",
    cost: 500,
    avail: "4",
    source: "SR5",
    minrating: 1,
    maxrating: 6,
    program_host: "rccs",
    needs_extra: true,
    extra_kind,
    extra_options: options,
  });

  it.each([
    ["skill", "技能", "Gunnery"],
    ["group", "グループ", "Gunnery"],
  ])("picks the %s from a closed list and stores it on the program", (kind, label, value) => {
    const patch = vi.fn();
    renderPanel(RccGear, rcc(), patch, {
      programs: [autosoft("a1", "Targeting", kind, ["Gunnery", "Perception"])] as any,
    });

    fireEvent.change(screen.getByRole("combobox", { name: "Gridlink: オートソフトを追加" }), {
      target: { value: "a1" },
    });
    fireEvent.change(screen.getByRole("combobox", { name: `Gridlink: ${label}` }), {
      target: { value },
    });
    fireEvent.click(screen.getByRole("button", { name: "Gridlink: 装着" }));

    const rows = patch.mock.calls[0][0].programs as { gear_id: string; extra: string }[];
    expect(rows).toEqual([{ gear_id: "a1", rating: 1, parent_id: "h1", extra: value }]);
  });

  it("takes a free-text target for a model the catalog cannot enumerate", () => {
    const patch = vi.fn();
    renderPanel(RccGear, rcc(), patch, {
      programs: [autosoft("a2", "Clearsight", "text", ["Rotodrone"])] as any,
    });

    fireEvent.change(screen.getByRole("combobox", { name: "Gridlink: オートソフトを追加" }), {
      target: { value: "a2" },
    });
    // `<input list>` is a combobox to the a11y tree, not a textbox
    fireEvent.change(screen.getByRole("combobox", { name: "Gridlink: 対象" }), {
      target: { value: "Steel Lynx" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Gridlink: 装着" }));

    const rows = patch.mock.calls[0][0].programs as { extra: string }[];
    expect(rows[0].extra).toBe("Steel Lynx");
  });

  it("still offers a targeted autosoft that is already installed, but not a plain one", () => {
    // one Targeting per skill is the point of the exemption; a second copy of
    // a plain program is not
    const installed = program("p1", "Plain", "h1", { gear_id: "plain" });
    const ch = makeCharacter({
      rccs: [host("h1", "Gridlink")],
      programs: [installed],
      derived: { rccs: [host("h1", "Gridlink")], programs: [installed] },
    } as any);
    renderPanel(RccGear, ch, vi.fn(), {
      programs: [
        autosoft("a1", "Targeting", "skill", ["Gunnery"]),
        {
          id: "plain",
          name: "Plain",
          category: "Common Programs",
          cost: 80,
          source: "SR5",
          minrating: 0,
          maxrating: 0,
          program_host: "rccs",
        },
      ] as any,
    });

    const options = [
      ...screen
        .getByRole("combobox", { name: "Gridlink: オートソフトを追加" })
        .querySelectorAll("option"),
    ].map((o) => o.textContent);
    expect(options).toContain("Targeting (500¥)");
    expect(options).not.toContain("Plain (80¥)");
  });
});

describe("<CyberdeckGear> the matrix attribute array", () => {
  const deck = (over: Record<string, unknown> = {}) => ({
    ...host("d1", "Erika MCD-1"),
    rating_max: 0,
    can_reorder: true,
    array: [4, 3, 2, 1],
    array_order: ["attack", "sleaze", "dataprocessing", "firewall"],
    ...over,
  });

  it("swaps two attributes rather than shifting the whole array", () => {
    const ch = makeCharacter({
      cyberdecks: [deck()],
      derived: { cyberdecks: [deck()] },
    } as any);
    const patch = vi.fn();
    renderPanel(CyberdeckGear, ch, patch);

    // put ATK where FW is (position 3): the two trade places, the rest hold
    fireEvent.change(screen.getByRole("combobox", { name: "ATK" }), { target: { value: "3" } });

    const rows = patch.mock.calls[0][0].cyberdecks as { array_order: string[] }[];
    expect(rows[0].array_order).toEqual(["firewall", "sleaze", "dataprocessing", "attack"]);
  });

  it("offers no reordering for a deck whose array is fixed", () => {
    const ch = makeCharacter({
      cyberdecks: [deck({ can_reorder: false })],
      derived: { cyberdecks: [deck({ can_reorder: false })] },
    } as any);
    renderPanel(CyberdeckGear, ch, vi.fn());

    expect(screen.queryByRole("combobox", { name: "ATK" })).toBeNull();
  });
});

/**
 * Sensors and optics nest: a housing holds sensors, a sight holds upgrades.
 * Deleting the middle of that chain has to take the subtree with it, which is
 * `dropTree` rather than a one-level filter — the case a flat list never hits.
 */
describe.each([
  ["SensorGear", SensorGear, "sensors", "sensors"],
  ["OpticsGear", OpticsGear, "optics", "optics"],
])("<%s> nested rows", (_name, Panel, chKey, dKey) => {
  const node = (id: string, name: string, parent_id: string | null = null) => ({
    id,
    gear_id: `c-${id}`,
    name,
    category: "Sensors",
    rating: 1,
    rating_max: 0,
    nuyen: 100,
    source: "SR5",
    parent_id,
    addoncategories: [],
  });
  const tree = () => [
    node("t1", "Housing"),
    node("t2", "Camera", "t1"),
    node("t3", "Low Light", "t2"),
    node("t4", "Elsewhere"),
  ];
  const character = () => makeCharacter({ [chKey]: tree(), derived: { [dKey]: tree() } } as any);

  it("shows only the roots as rows, with the rest nested inside", () => {
    const { container } = renderPanel(Panel, character(), vi.fn());

    const rows = [...container.querySelectorAll<HTMLElement>(".cyber-item")];
    expect(rows).toHaveLength(2);
    expect(rows[0].textContent).toContain("Camera");
    expect(rows[1].textContent).not.toContain("Camera");
  });

  it("deleting a root drops its whole subtree, not just its children", () => {
    const patch = vi.fn();
    renderPanel(Panel, character(), patch);

    fireEvent.click(screen.getAllByRole("button", { name: /削除/ })[0]);

    const rows = patch.mock.calls[0][0][chKey] as { id: string }[];
    expect(rows.map((r) => r.id)).toEqual(["t4"]); // t1, t2 *and* the grandchild t3
  });
});

describe("<CommlinkGear> apps on a commlink", () => {
  const link = (id: string, name: string) => ({ ...host(id, name), programs: undefined });
  const app = (
    id: string,
    name: string,
    parent_id: string,
    over: Record<string, unknown> = {},
  ) => ({
    id,
    gear_id: `c-${id}`,
    name,
    category: "Software",
    rating: 1,
    rating_max: 0,
    parent_id,
    nuyen: 100,
    source: "SR5",
    ...over,
  });
  const character = (apps: Record<string, unknown>[]) =>
    makeCharacter({
      commlinks: [link("l1", "Meta Link"), link("l2", "Sony Emperor")],
      apps,
      derived: {
        commlinks: [link("l1", "Meta Link"), link("l2", "Sony Emperor")],
        apps,
      },
    } as any);

  it("draws each app under its own commlink", () => {
    const { container } = renderPanel(
      CommlinkGear,
      character([app("a1", "Mapsoft", "l1"), app("a2", "Tutorsoft", "l2")]),
      vi.fn(),
    );

    const rows = [...container.querySelectorAll<HTMLElement>(".cyber-item")];
    expect(rows[0].textContent).toContain("Mapsoft");
    expect(rows[0].textContent).not.toContain("Tutorsoft");
    expect(rows[1].textContent).toContain("Tutorsoft");
  });

  /** An app row prefers `label` — the engine puts the chosen target in it, so
   *  two Tutorsofts on one link are told apart by what they teach. */
  it("names an app by its label when the engine supplied one", () => {
    renderPanel(
      CommlinkGear,
      character([app("a1", "Tutorsoft", "l1", { label: "Tutorsoft (Pistols)" })]),
      vi.fn(),
    );

    expect(screen.getByText(/Tutorsoft \(Pistols\)/)).toBeDefined();
  });

  it("removing one app leaves the other", () => {
    const patch = vi.fn();
    renderPanel(
      CommlinkGear,
      character([app("a1", "Mapsoft", "l1"), app("a2", "Tutorsoft", "l2")]),
      patch,
    );

    fireEvent.click(screen.getAllByRole("button", { name: "外す" })[1]);

    expect((patch.mock.calls[0][0].apps as { id: string }[]).map((r) => r.id)).toEqual(["a1"]);
  });

  it("stores the skill an app is bought for", () => {
    const patch = vi.fn();
    renderPanel(
      CommlinkGear,
      character([
        app("a1", "Tutorsoft", "l1", { extra_kind: "skill", extra_options: ["Pistols", "Blades"] }),
      ]),
      patch,
    );

    fireEvent.change(screen.getByRole("combobox", { name: "技能" }), {
      target: { value: "Blades" },
    });

    expect((patch.mock.calls[0][0].apps as { extra: string }[])[0].extra).toBe("Blades");
  });
});

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
    } as any);

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
    } as any);
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
    ] as any,
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
      ] as any,
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
      ] as any,
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
    } as any);
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
      ] as any,
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
    } as any);

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
