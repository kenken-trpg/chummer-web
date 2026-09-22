import type { InstalledGear } from "./gear";

// Cyberware and bioware: row shapes listed in `Derived` (../derived.ts).

export interface InstalledWare {
  id: string;
  ware_id: string;
  name: string;
  category: string;
  rating: number;
  grade: string;
  wireless: boolean;
  parent_id?: string | null;
  included?: boolean;
  /** `<addware>`: the quality that came with this implant (Busted Cyberware). */
  granted_by?: string;
  essence: number;
  nuyen: number;
  /** the price picked for a `Variable(lo-hi)` piece; null for a fixed one */
  cost?: number | null;
  cost_range?: [number, number] | null;
  capacity_used?: number;
  capacity_max?: number;
  rating_min?: number;
  rating_max?: number;
  limb_str?: number;
  limb_agi?: number;
  limb_armor?: number;
  selectside?: boolean;
  side?: string | null;
  /** `<selectcyberware>`: this implant is keyed to another one, named in `extra`. */
  select_ware?: boolean;
  select_ware_category?: string;
  extra?: string;
  avail?: string;
  device_rating?: number;
  source?: string;
  /** `<allowgear>`: the gear categories it holds (a Chemical Gland's chemical). */
  allow_gear?: string[];
  /** what it holds, as gear rows */
  gear?: InstalledGear[];
}
