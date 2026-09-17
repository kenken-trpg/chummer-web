// Vehicles and drones: row shapes listed in `Derived` (../derived.ts).

import type { InstalledGear, InstalledOptics } from "./gear";
import type { InstalledWare } from "./ware";

export interface InstalledVehicleMod {
  id: string;
  mod_id: string;
  name: string;
  category: string;
  parent_id?: string | null;
  included?: boolean;
  rating: number;
  rating_max: number;
  slots: number;
  nuyen: number;
  avail?: string;
  source?: string;
  capacity_used?: number;
  capacity_max?: number;
  subsystems?: string[];
  cyberware?: InstalledWare[];
}

export interface InstalledWeaponMount {
  id: string;
  parent_id?: string | null;
  size_id: string;
  visibility_id?: string;
  flexibility_id?: string;
  control_id?: string;
  included?: boolean;
  name: string;
  label: string;
  slots: number;
  nuyen: number;
  weapon_install_id?: string | null;
  weapon_name?: string;
  allowedweapons?: string;
  source?: string;
}

export interface InstalledDrone {
  id: string;
  gear_id: string;
  name: string;
  category: string;
  handling: string;
  speed: string;
  accel: string;
  body: string;
  armor: string;
  pilot: string;
  sensor: string;
  seats?: string;
  nuyen: number;
  slots_used?: number;
  slots_max?: number;
  slot_tracks?: { category: string; used: number; max: number }[];
  mods?: InstalledVehicleMod[];
  weapon_mounts?: InstalledWeaponMount[];
  sensors?: InstalledOptics[];
  gear?: InstalledGear[];
  avail?: string;
  source?: string;
}
