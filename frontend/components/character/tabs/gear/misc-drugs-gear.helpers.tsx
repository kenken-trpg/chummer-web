import { render } from "@testing-library/react";
import type { Character } from "@/lib/types";
import { BooksProvider } from "@/lib/character/books";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";
import { MiscDrugsGear } from "./MiscDrugsGear";

/**
 * One component, two tabs. `mode` decides whether a row belongs here at all,
 * and the test for it is a category check written out three times over —
 * `Drugs`, `Toxins`, `Chemicals`, `BTLs` — in the owned list, in the category tabs
 * and in each picker. Get one of the three wrong and a drug is invisible in
 * both tabs, or shows up in both.
 *
 * The rest is the gear tree: `d.gear` is flat, parentage lives in
 * `parent_id`, and every control maps or filters that one list. Two other
 * things here read from `ch.gear` rather than `d.gear` on purpose — the drug
 * "in use" checkbox, because the derived row does not carry the flag back —
 * and that distinction is invisible on screen.
 *
 * `gear-owned.test.tsx` covers the plain nesting case in misc mode. The `misc-*.test.tsx` files
 * cover the mode split, the pickers, and the "extra" plumbing that appears
 * in four separate places with four separate pieces of state.
 */

export const gear = (id: string, name: string, over: Record<string, unknown> = {}) => ({
  id,
  name,
  gear_id: `c-${id}`,
  category: "Electronics",
  qty: 1,
  rating: 1,
  rating_max: 0,
  nuyen: 100,
  source: "SR5",
  included: false,
  ...over,
});

export const drug = (id: string, name: string, over: Record<string, unknown> = {}) =>
  gear(id, name, { category: "Drugs", is_drug: true, ...over });

export function renderPanel(
  ch: Character,
  patch: (b: Record<string, unknown>) => void,
  mode: "misc" | "drugs" = "misc",
  catalog = makeCatalog(),
  books?: string[],
) {
  return render(
    <BooksProvider books={books}>
      <MiscDrugsGear {...panelProps(ch, { catalog, patch })} mode={mode} />
    </BooksProvider>,
  );
}

/** A catalog whose gear entry `id` offers these picks. */
export const withOptions = (id: string, extra_options: string[]) =>
  makeCatalog({
    gear: [{ id, name: id, category: "Electronics", cost: "0", source: "SR5", extra_options }],
  } as never);

/** A character owning these gear rows, mirrored into `derived`. */
export function owning(
  rows: Record<string, unknown>[],
  over: Record<string, unknown> = {},
): Character {
  return makeCharacter({ gear: rows, ...over, derived: { gear: rows } } as never);
}

export const ownedNames = (container: HTMLElement) =>
  [...container.querySelectorAll(".cyber-item > div > b")].map((el) => el.textContent);
