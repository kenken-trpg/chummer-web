"use client";

import type { InstalledWare, WareCatalogItem } from "@/lib/types";
import type { UiFn } from "@/lib/i18n";
import { modularMountCandidates, wareVehicleLabel } from "@/lib/character/ware";
import { sideLabel } from "@/lib/character/constants";

export function ModularMountSelect({
  item,
  rows,
  catalogItems,
  vehicleHosts = {},
  tr,
  ui,
  onChange,
}: {
  item: InstalledWare;
  rows: InstalledWare[];
  catalogItems: WareCatalogItem[];
  vehicleHosts?: Record<string, string>;
  tr: (name: string) => string;
  ui: UiFn;
  onChange: (parentId: string | null) => void;
}) {
  if (
    !catalogItems.find((spec) => spec.id === item.ware_id)?.mounts_to ||
    item.included ||
    item.granted_by ||
    !rows.some((row) => row.id === item.id)
  )
    return null;
  const candidates = modularMountCandidates(item, rows, catalogItems, vehicleHosts);
  const label = (row: InstalledWare) => {
    const vehicle = wareVehicleLabel(row, rows, vehicleHosts);
    return `${vehicle ? `${vehicle} / ` : ""}${tr(row.name)}${row.side ? ` (${sideLabel(row.side, ui)})` : ""} #${rows.indexOf(row) + 1}`;
  };
  const current = rows.find((row) => row.id === item.parent_id);
  return (
    <label className="option-row">
      {ui("ware.modularMount")}
      <select
        aria-label={ui("ware.modularMountFor", { name: tr(item.name) })}
        value={item.parent_id || ""}
        onChange={(event) => onChange(event.target.value || null)}
      >
        <option value="">{ui("ware.modularDetached")}</option>
        {item.parent_id && !candidates.some((host) => host.id === item.parent_id) ? (
          <option value={item.parent_id} disabled>
            {ui("ware.modularCurrentInvalid", { name: current ? label(current) : item.parent_id })}
          </option>
        ) : null}
        {candidates.map((host) => (
          <option key={host.id} value={host.id}>
            {label(host)}
          </option>
        ))}
      </select>
      <span className="muted">
        {ui(item.modular_equipped === false ? "ware.modularInactive" : "ware.modularActive")}
      </span>
    </label>
  );
}
