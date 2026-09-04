import { fireEvent, render, screen } from "@testing-library/react";
import type { ComponentType } from "react";
import { describe, expect, it, vi } from "vitest";
import type { Catalog } from "@/lib/types";
import type { TabPanelProps } from "@/components/character/types";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";
import { ArmorGear } from "./ArmorGear";
import { CommlinkGear } from "./CommlinkGear";
import { CyberdeckGear } from "./CyberdeckGear";
import { LifestyleGear } from "./LifestyleGear";
import { OpticsGear } from "./OpticsGear";
import { RccGear } from "./RccGear";
import { SensorGear } from "./SensorGear";

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * The seven panels that buy from the catalog through `<CatalogPicker>`. They
 * are near-identical by construction now, so they are covered as one table:
 * what each still owns is its catalog key, its search label and the shape of
 * the patch it emits, and that is exactly what is asserted here.
 */
const base = { avail: "4", cost: 500, source: "SR5", minrating: 0, maxrating: 0 };

const PANELS: {
  name: string;
  Panel: ComponentType<TabPanelProps>;
  label: string;
  catalog: Partial<Catalog>;
  /** the core-rulebook row that shows with an empty search box */
  core: string;
  /** the supplement row that only a search reaches */
  supplement: string;
  patch: Record<string, unknown>;
}[] = [
  {
    name: "ArmorGear",
    Panel: ArmorGear,
    label: "防具を検索",
    catalog: {
      armor: [
        { ...base, id: "a1", name: "Lined Coat", category: "Armor", armor: "9" },
        { ...base, id: "a2", name: "Chameleon Suit", category: "Armor", source: "RG", armor: "9" },
      ] as any,
    },
    core: "Lined Coat",
    supplement: "Chameleon Suit",
    patch: { armor: [{ armor_id: "a1", rating: 1, equipped: true }] },
  },
  {
    name: "CommlinkGear",
    Panel: CommlinkGear,
    label: "通信機を検索",
    catalog: {
      commlinks: [
        { ...base, id: "c1", name: "Meta Link", devicerating: 1 },
        { ...base, id: "c2", name: "Hermes Ikon", source: "DT", devicerating: 5 },
      ] as any,
    },
    core: "Meta Link",
    supplement: "Hermes Ikon",
    patch: { commlinks: [{ gear_id: "c1", rating: 1 }] },
  },
  {
    name: "CyberdeckGear",
    Panel: CyberdeckGear,
    label: "サイバーデッキを検索",
    catalog: {
      cyberdecks: [
        { ...base, id: "d1", name: "Erika MCD-1", devicerating: 1, programs: 1 },
        { ...base, id: "d2", name: "Novatech Navi", source: "DT", devicerating: 3, programs: 3 },
      ] as any,
    },
    core: "Erika MCD-1",
    supplement: "Novatech Navi",
    patch: { cyberdecks: [{ gear_id: "d1", rating: 1 }] },
  },
  {
    name: "LifestyleGear",
    Panel: LifestyleGear,
    label: "ライフスタイルを検索",
    catalog: {
      lifestyles: [
        { ...base, id: "l1", name: "Medium", cost: 5000, increment: "month", lp: 3 },
        { ...base, id: "l2", name: "Hospitalized", cost: 500, increment: "month", lp: 0 },
      ] as any,
    },
    // lifestyles filter on a hand-picked core set, not on `source`
    core: "Medium",
    supplement: "Hospitalized",
    patch: { lifestyles: [{ lifestyle_id: "l1", months: 1, quality_ids: [] }] },
  },
  {
    name: "OpticsGear",
    Panel: OpticsGear,
    label: "視覚／聴覚を検索",
    catalog: {
      optics: [
        { ...base, id: "o1", name: "Goggles", category: "Vision Devices" },
        { ...base, id: "o2", name: "Ear Buds", category: "Audio Devices", source: "RG" },
      ] as any,
    },
    core: "Goggles",
    supplement: "Ear Buds",
    patch: { optics: [{ gear_id: "o1", rating: 1 }] },
  },
  {
    name: "RccGear",
    Panel: RccGear,
    label: "RCCを検索",
    catalog: {
      rccs: [
        { ...base, id: "r1", name: "Sony Emperor", devicerating: 2, programs: 2 },
        { ...base, id: "r2", name: "Proteus Poseidon", source: "R5", devicerating: 6, programs: 6 },
      ] as any,
    },
    core: "Sony Emperor",
    supplement: "Proteus Poseidon",
    patch: { rccs: [{ gear_id: "r1", rating: 1 }] },
  },
  {
    name: "SensorGear",
    Panel: SensorGear,
    label: "センサーを検索",
    catalog: {
      sensors: [
        { ...base, id: "s1", name: "Motion Sensor", category: "Sensors" },
        {
          ...base,
          id: "s2",
          name: "Micro Drone Housing",
          category: "Sensor Housings",
          source: "R5",
        },
      ] as any,
    },
    core: "Motion Sensor",
    supplement: "Micro Drone Housing",
    patch: { sensors: [{ gear_id: "s1", rating: 1 }] },
  },
];

function renderPanel(entry: (typeof PANELS)[number], patch: (b: Record<string, unknown>) => void) {
  const ch = makeCharacter();
  render(
    <entry.Panel
      catalog={makeCatalog(entry.catalog)}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      t={(k) => k}
      ui={testUi}
      patch={patch}
      setCharacter={() => {}}
    />,
  );
}

describe.each(PANELS)("<$name>", (entry) => {
  it("lists the core-rulebook rows, and says why the rest are missing", () => {
    renderPanel(entry, vi.fn());
    expect(screen.getByRole("searchbox", { name: entry.label })).toBeDefined();
    expect(screen.getByText(entry.core)).toBeDefined();
    expect(screen.queryByText(entry.supplement)).toBeNull();
    expect(screen.getByRole("status").textContent).toMatch(/表示中/);
  });

  it("reaches the supplement rows through the search box", () => {
    renderPanel(entry, vi.fn());
    fireEvent.change(screen.getByRole("searchbox", { name: entry.label }), {
      target: { value: entry.supplement.slice(0, 5) },
    });
    expect(screen.getByText(entry.supplement)).toBeDefined();
  });

  it("buys the row its button is named after", () => {
    const patch = vi.fn();
    renderPanel(entry, patch);
    fireEvent.click(screen.getByRole("button", { name: `${entry.core} を購入` }));
    expect(patch).toHaveBeenCalledWith(entry.patch);
  });
});
