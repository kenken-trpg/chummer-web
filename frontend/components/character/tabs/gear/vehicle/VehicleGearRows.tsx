"use client";
import { SlotPicker } from "@/components/character/tabs/gear/vehicle/SlotPicker";
import type { VehicleRowProps } from "@/components/character/tabs/gear/vehicle/types";
import { useBookFilter } from "@/lib/character/books";
import { dropTree, vehicleInteriorFits } from "@/lib/character/gear";

/** Gear carried inside one vehicle — a medkit in the glovebox rather than
 *  anything bolted to the chassis. */
export function VehicleGearRows({
  item,
  catalog,
  character: ch,
  tr,
  ui,
  patch,
  slotPick,
  setSlotPick,
}: VehicleRowProps) {
  const byBook = useBookFilter();
  const interior = byBook(catalog.gear || []).filter(
    (mod) =>
      vehicleInteriorFits(mod) &&
      String(mod.cost || "").trim() !== "0" &&
      !(item.gear || []).some((row) => row.gear_id === mod.id),
  );
  return (
    <>
      {(item.gear || []).map((acc) => (
        <div className="muted" key={acc.id} style={{ marginTop: 6 }}>
          {tr(acc.label || acc.name)}
          {acc.rating_max > 0 ? ` R${acc.rating}` : ""}
          {acc.included ? ` / ${ui("common.included")}` : ` / ${acc.nuyen.toLocaleString()}¥`}
          {acc.included ? null : (
            <>
              {" "}
              <button
                className="btn danger"
                onClick={() =>
                  patch({
                    gear: dropTree(ch.gear || [], acc.id),
                  })
                }
              >
                {ui("common.remove")}
              </button>
            </>
          )}
          {acc.rating_max > 0 && !acc.included ? (
            <label title={ui("common.ratingHint")}>
              {ui("common.rating")}
              <input
                type="number"
                min={1}
                max={acc.rating_max}
                value={acc.rating}
                onChange={(e) =>
                  patch({
                    gear: (ch.gear || []).map((row) =>
                      row.id === acc.id ? { ...row, rating: Number(e.target.value) } : row,
                    ),
                  })
                }
              />
            </label>
          ) : null}
        </div>
      ))}
      <SlotPicker
        pickKey={`${item.id}-gear`}
        rowName={tr(item.name)}
        label={ui("veh.addInteriorGear")}
        options={interior}
        onAdd={(spec) =>
          patch({
            gear: [
              ...(ch.gear || []),
              { gear_id: spec.id, rating: Math.max(1, spec.minrating || 1), parent_id: item.id },
            ],
          })
        }
        tr={tr}
        ui={ui}
        slotPick={slotPick}
        setSlotPick={setSlotPick}
      />
    </>
  );
}
