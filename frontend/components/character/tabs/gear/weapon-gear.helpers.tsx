import { render, within } from "@testing-library/react";
import type { Character } from "@/lib/types";
import { BooksProvider } from "@/lib/character/books";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";
import { WeaponGear } from "./WeaponGear";

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
 * `gear-owned.test.tsx` covers the plain case. The `weapon-*.test.tsx` files cover the other two,
 * plus the accessory and ammunition subtrees, which patch `weapon_accessories`
 * and `gear` respectively while rendering underneath the weapon.
 */

export const weapon = (id: string, name: string, over: Record<string, unknown> = {}) => ({
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

export const accessory = (id: string, name: string, over: Record<string, unknown> = {}) => ({
  id,
  name,
  accessory_id: `c-${id}`,
  mount: "Top",
  nuyen: 250,
  included: false,
  ...over,
});

export const ammoRow = (id: string, name: string, over: Record<string, unknown> = {}) => ({
  id,
  name,
  gear_id: `c-${id}`,
  qty: 1,
  nuyen: 40,
  loaded: false,
  ammo_weapon_types: ["Heavy Pistols"],
  ...over,
});

export function renderWeapons(
  ch: Character,
  patch: (b: Record<string, unknown>) => void,
  catalog = makeCatalog(),
  books?: string[],
) {
  return render(
    <BooksProvider books={books}>
      <WeaponGear {...panelProps(ch, { catalog, patch })} />
    </BooksProvider>,
  );
}

/** A character owning the given weapons, mirrored into `derived`. */
export function owning(
  rows: Record<string, unknown>[],
  rest: Record<string, unknown> = {},
): Character {
  const { derived = {}, ...top } = rest;
  return makeCharacter({
    weapons: rows,
    ...top,
    derived: { weapons: rows, ...(derived as object) },
  } as never);
}

/** The 装着 button belonging to one picker — a weapon has two. */
export function installNextTo(select: HTMLElement) {
  // eslint-disable-next-line no-restricted-syntax -- a test helper: the button's accessible name
  return within(select.parentElement as HTMLElement).getByRole("button", { name: "装着" });
}
