import type { TabPanelProps } from "@/components/character/types";
import type { InstalledDrone } from "@/lib/types";

/** What every row under a vehicle needs: the vehicle itself, the usual tab
 *  plumbing, and the shared `slotPick` map.
 *
 *  `slotPick` is one piece of state for the whole panel — every "pick
 *  something, then press 装着" control on the page reads and writes it under a
 *  key of its own — so it is threaded down rather than split per row. */
export type VehicleRowProps = Pick<
  TabPanelProps,
  "catalog" | "character" | "d" | "tr" | "ui" | "patch"
> & {
  item: InstalledDrone;
  slotPick: Record<string, string>;
  setSlotPick: (next: (cur: Record<string, string>) => Record<string, string>) => void;
};
