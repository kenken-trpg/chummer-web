"use client";
import { SlotPicker } from "@/components/character/tabs/gear/vehicle/SlotPicker";
import type { VehicleRowProps } from "@/components/character/tabs/gear/vehicle/types";
import { useBookFilter } from "@/lib/character/books";

/** The sensor housings on one vehicle and the functions slotted into each. */
export function VehicleSensorRows({
  item,
  catalog,
  character: ch,
  d,
  tr,
  ui,
  patch,
  slotPick,
  setSlotPick,
}: VehicleRowProps) {
  const byBook = useBookFilter();
  return (
    <>
      {(item.sensors || []).map((sensor) => {
        const functions = (d.sensors || []).filter((child) => child.parent_id === sensor.id);
        const sensorAddons = (catalog.sensors || []).filter(
          (mod) =>
            (sensor.addoncategories || []).includes(mod.category) &&
            mod.category !== "Custom" &&
            !functions.some((child) => child.gear_id === mod.id),
        );
        return (
          <div className="muted" key={sensor.id} style={{ marginTop: 6 }}>
            {tr(sensor.name)}
            {sensor.rating_max > 0 ? ` R${sensor.rating}` : ""}
            {sensor.capacity_max
              ? ui("gear.capacity", {
                  used: sensor.capacity_used ?? 0,
                  max: sensor.capacity_max ?? 0,
                })
              : ""}
            {sensor.included
              ? ` / ${ui("common.included")}`
              : ` / ${sensor.nuyen.toLocaleString()}¥`}
            {functions.map((child) => (
              <div key={child.id} style={{ marginTop: 4, marginLeft: 12 }}>
                {tr(child.name)}
                {child.capacity_cost
                  ? ` / ${ui("common.capacity")} ${child.capacity_cost}`
                  : ""}{" "}
                <button
                  className="btn danger"
                  onClick={() =>
                    patch({
                      sensors: (ch.sensors || []).filter((row) => row.id !== child.id),
                    })
                  }
                >
                  {ui("common.remove")}
                </button>
              </div>
            ))}
            <SlotPicker
              pickKey={sensor.id}
              rowName={tr(sensor.name)}
              label={ui("gear.addSensorFn")}
              options={byBook(sensorAddons)}
              onAdd={(spec) =>
                patch({
                  sensors: [
                    ...(ch.sensors || []),
                    {
                      gear_id: spec.id,
                      rating: Math.max(1, spec.minrating || 1),
                      parent_id: sensor.id,
                    },
                  ],
                })
              }
              tr={tr}
              ui={ui}
              slotPick={slotPick}
              setSlotPick={setSlotPick}
            />
          </div>
        );
      })}
    </>
  );
}
