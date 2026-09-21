import { render } from "@testing-library/react";
import type { ComponentType } from "react";
import type { Catalog, Character } from "@/lib/types";
import type { TabPanelProps } from "@/components/character/types";
import { makeCatalog, panelProps } from "@/tests/fixtures";

/** Shared by `gear-addons.test.tsx` and `gear-mods.test.tsx`. */

// Each panel takes TabPanelProps plus its own extras, so the list is typed by
// what they share and the call site widens it back.
export type Panel = ComponentType<never>;

export function renderPanel(
  Panel: Panel,
  character: Character,
  patch: (b: Record<string, unknown>) => void,
  catalog: Partial<Catalog> = {},
) {
  const P = Panel as ComponentType<TabPanelProps>;
  return render(<P {...panelProps(character, { catalog: makeCatalog(catalog), patch })} />);
}

export const host = (id: string, name: string) => ({
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

export const program = (
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
