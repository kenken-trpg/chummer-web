import { render, within } from "@testing-library/react";
import type { Character } from "@/lib/types";
import { BooksProvider } from "@/lib/character/books";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";
import { VehicleDroneGear } from "./VehicleDroneGear";

/**
 * `gear-owned.test.tsx` pins this panel's backbone — mods, weapon mounts, and
 * the vehicle/drone split. The `vehicle-drone-*.test.tsx` files cover the trees hanging off it,
 * each with its own picker and its own idea of what "the parent" means:
 * cyberware hosted inside a mod, subsystem slots, sensor functions, and
 * interior gear.
 *
 * What makes them worth their own file is that **they all patch top-level
 * character lists** — `ch.cyberware`, `ch.sensors`, `ch.gear` — while what is
 * on screen is a nested row. The only thing tying a row to its place in the
 * tree is `parent_id`, so an install that parents to the vehicle instead of
 * the mod, or a removal that filters one row out of a subtree, still renders
 * plausibly and is wrong. Every test in them therefore asserts the `parent_id`
 * that came back, not just that something was added.
 */

export const GRADES = [{ name: "Standard", ess: 1, cost: 1 }];

export const vehicle = (id: string, name: string, over: Record<string, unknown> = {}) => ({
  id,
  name,
  vehicle_id: `c-${id}`,
  category: "Cars",
  handling: "4",
  speed: "3",
  accel: "2",
  body: "11",
  armor: "6",
  pilot: "1",
  sensor: "2",
  nuyen: 16000,
  source: "SR5",
  mods: [],
  weapon_mounts: [],
  sensors: [],
  gear: [],
  ...over,
});

export const mod = (id: string, name: string, over: Record<string, unknown> = {}) => ({
  id,
  name,
  mod_id: `c-${id}`,
  category: "Powertrain",
  rating: 1,
  rating_max: 0,
  nuyen: 1000,
  slots: 2,
  included: false,
  subsystems: [],
  ...over,
});

/** An installed cyberware row, shaped far enough for `<WareRow>` to render. */
export const ware = (
  id: string,
  name: string,
  parent_id: string,
  over: Record<string, unknown> = {},
) => ({
  id,
  name,
  ware_id: `cat-${name}`,
  category: "Cyberlimb Enhancement",
  essence: 0,
  nuyen: 5000,
  source: "SR5",
  avail: "6R",
  rating: 1,
  grade: "Standard",
  wireless: true,
  parent_id,
  ...over,
});

export function renderVehicle(
  ch: Character,
  patch: (b: Record<string, unknown>) => void,
  catalog = makeCatalog(),
  mode: "vehicle" | "drone" = "vehicle",
  books?: string[],
) {
  return render(
    <BooksProvider books={books}>
      <VehicleDroneGear {...panelProps(ch, { catalog, patch })} mode={mode} />
    </BooksProvider>,
  );
}

/**
 * The 装着 button belonging to one picker. A vehicle has four of them on
 * screen at once (mods, mounts, sensor functions, interior gear), so every
 * install has to be aimed at the select it sits next to.
 */
export function installNextTo(select: HTMLElement) {
  // eslint-disable-next-line no-restricted-syntax -- a test helper: the button's accessible name
  return within(select.parentElement as HTMLElement).getByRole("button", { name: "装着" });
}

/** A character owning one vehicle, mirrored into `derived` with its subtrees. */
export function owning(v: Record<string, unknown>, rest: Record<string, unknown> = {}): Character {
  const { derived = {}, ...top } = rest;
  return makeCharacter({
    vehicles: [v],
    ...top,
    derived: { vehicles: [v], ...(derived as object) },
  } as never);
}
