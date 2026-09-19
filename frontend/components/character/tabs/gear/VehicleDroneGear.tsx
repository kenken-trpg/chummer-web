"use client";
import { useState } from "react";
import { HelpTip } from "@/components/help/HelpTip";
import { AutosoftRows } from "@/components/character/tabs/gear/AutosoftRows";
import { CatalogPicker } from "@/components/character/CatalogPicker";
import { DiscountToggle } from "@/components/character/DiscountToggle";
import { VehicleGearRows } from "@/components/character/tabs/gear/vehicle/VehicleGearRows";
import { VehicleModRows } from "@/components/character/tabs/gear/vehicle/VehicleModRows";
import { VehicleMountRows } from "@/components/character/tabs/gear/vehicle/VehicleMountRows";
import { VehicleSensorRows } from "@/components/character/tabs/gear/vehicle/VehicleSensorRows";
import type { TabPanelProps } from "@/components/character/types";
import { dropDrone } from "@/lib/character/gear";
import { useWareCompact } from "@/lib/character/useWareCompact";
import { vehicleSlotLabel } from "@/lib/engine-notices";

export function VehicleDroneGear({
  catalog,
  character: ch,
  d,
  tr,
  patch,
  mode,
  ui,
}: TabPanelProps & { mode: "drone" | "vehicle" }) {
  const [slotPick, setSlotPick] = useState<Record<string, string>>({});
  const [compact, setCompact] = useWareCompact("vehicleCompact");
  const owned = (mode === "drone" ? d.drones : d.vehicles) || [];

  return (
    <>
      {owned.length ? (
        <label className="option-row">
          <input type="checkbox" checked={compact} onChange={(e) => setCompact(e.target.checked)} />
          {ui("ware.compact")}
        </label>
      ) : null}
      <>
        {owned.map((item) => {
          const rowProps = {
            item,
            catalog,
            character: ch,
            d,
            tr,
            ui,
            patch,
            slotPick,
            setSlotPick,
          };
          const deleteButton = (
            <button
              className="btn danger"
              onClick={() =>
                patch(dropDrone(ch, item.id, mode === "vehicle" ? "vehicles" : "drones"))
              }
            >
              {ui("common.delete")}
            </button>
          );
          if (compact) {
            // Names only: what is fitted to the vehicle, none of the controls.
            const fitted = [
              ...(item.mods || []).map((mod) => tr(mod.name)),
              ...(item.weapon_mounts || []).map((mount) => tr(mount.label || mount.name)),
              ...(item.sensors || []).map((sensor) => tr(sensor.name)),
              ...(item.gear || []).map((acc) => tr(acc.label || acc.name)),
              ...(d.programs || [])
                .filter((prog) => prog.parent_id === item.id)
                .map((prog) => tr(prog.label || prog.name)),
            ];
            return (
              <div className="cyber-item compact" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  {fitted.length ? (
                    <div className="muted">{fitted.join(ui("common.listSep"))}</div>
                  ) : null}
                </div>
                {deleteButton}
              </div>
            );
          }
          return (
            <div className="cyber-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="cyber-controls">
                  <DiscountToggle
                    list={mode === "vehicle" ? "vehicles" : "drones"}
                    id={item.id}
                    ch={ch}
                    d={d}
                    ui={ui}
                    patch={patch}
                  />
                </div>
                <div className="muted">
                  <HelpTip
                    label={ui("help.open", { label: tr(item.name) })}
                    lines={[
                      { label: ui("help.vehicle.stats") },
                      { label: ui("help.vehicle.pilot") },
                      { label: ui("help.vehicle.body") },
                      {
                        label: ui(
                          (item.slot_tracks || []).length
                            ? "help.vehicle.slots"
                            : "help.vehicle.slotsDrone",
                        ),
                      },
                    ]}
                  >
                    {ui("help.vehicle.statsLabel")}
                  </HelpTip>{" "}
                  {item.name} / {tr(item.category)} / HND {item.handling} / SPD {item.speed} / ACC{" "}
                  {item.accel} / BOD {item.body} / ARM {item.armor} / PLT {item.pilot} / SNR{" "}
                  {item.sensor}
                  {item.seats ? ` / SEAT ${item.seats}` : ""}
                  {(item.slot_tracks || []).length
                    ? ` / ${(item.slot_tracks || [])
                        .map(
                          (track) =>
                            `${vehicleSlotLabel(track.category, ui)} ${track.used}/${track.max}`,
                        )
                        .join(" · ")}`
                    : item.slots_max
                      ? ui("veh.slots", { used: item.slots_used ?? 0, max: item.slots_max })
                      : ""}
                  {" / "}
                  {item.nuyen.toLocaleString()}¥ / {item.source}
                </div>
                <VehicleModRows {...rowProps} />
                <VehicleMountRows {...rowProps} />
                <VehicleSensorRows {...rowProps} />
                <VehicleGearRows {...rowProps} />
                <AutosoftRows
                  hostId={item.id}
                  hostName={tr(item.name)}
                  catalog={catalog}
                  character={ch}
                  d={d}
                  tr={tr}
                  ui={ui}
                  patch={patch}
                />
              </div>
              {deleteButton}
            </div>
          );
        })}
      </>

      {mode === "drone" ? (
        <CatalogPicker
          items={catalog.drones || []}
          label={ui("veh.searchDrones")}
          tr={tr}
          describe={(item) => (
            <>
              {item.name} / {tr(item.category)} / HND {item.handling} / SPD {item.speed} / PLT{" "}
              {item.pilot} / SNR {item.sensor} / {item.cost}¥ / {item.avail || "-"} / {item.source}
            </>
          )}
          onAdd={(item) => patch({ drones: [...(ch.drones || []), { gear_id: item.id }] })}
        />
      ) : (
        <CatalogPicker
          items={catalog.vehicles || []}
          label={ui("veh.searchVehicles")}
          tr={tr}
          describe={(item) => (
            <>
              {item.name} / {tr(item.category)} / HND {item.handling} / SPD {item.speed} / SEAT{" "}
              {item.seats || "-"} / {item.cost}¥ / {item.avail || "-"} / {item.source}
            </>
          )}
          onAdd={(item) => patch({ vehicles: [...(ch.vehicles || []), { gear_id: item.id }] })}
        />
      )}
    </>
  );
}
