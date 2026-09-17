"use client";
import { SlotPicker } from "@/components/character/tabs/gear/vehicle/SlotPicker";
import type { VehicleRowProps } from "@/components/character/tabs/gear/vehicle/types";
import { WareRow } from "@/components/character/WareRow";
import { r5SlotLabel } from "@/lib/character/constants";
import { vehicleFits, vehicleForbidden, wareFitsVehicleMod } from "@/lib/character/gear";
import { removeWareTree, wareBounds } from "@/lib/character/ware";

/** The vehicle mods fitted to one vehicle, and the picker that adds another.
 *
 *  A mod can host cyberware of its own (a Rigger Interface's subsystems), so
 *  each row may carry a `WareRow` tree under it. */
export function VehicleModRows({
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
  const addons = (catalog.vehicle_mods || []).filter(
    (mod) =>
      mod.purchasable !== false &&
      String(mod.cost || "").trim() !== "0" &&
      vehicleFits(mod.required, item) &&
      !vehicleForbidden(mod.forbidden, item) &&
      !(item.mods || []).some((row) => row.mod_id === mod.id),
  );
  return (
    <>
      {(item.mods || []).map((mod) => {
        const hosted = (d.cyberware || []).filter((row) => row.parent_id === mod.id);
        const wareOptions = (mod.subsystems || []).length
          ? catalog.cyberware.items.filter((ware) => wareFitsVehicleMod(ware, mod))
          : [];
        const warePickKey = `${mod.id}-ware`;
        const chosenWare = slotPick[warePickKey] || wareOptions[0]?.id || "";
        return (
          <div className="muted" key={mod.id} style={{ marginTop: 6 }}>
            {tr(mod.name)}
            {mod.rating_max > 0 ? ` R${mod.rating}` : ""}
            {mod.included ? ` / ${ui("common.included")}` : ` / ${mod.nuyen.toLocaleString()}¥`}
            {mod.slots ? ui("veh.slotCost", { slots: mod.slots }) : ""}
            {mod.capacity_max
              ? ui("gear.capacity", {
                  used: mod.capacity_used ?? 0,
                  max: mod.capacity_max,
                })
              : ""}
            {r5SlotLabel(mod.category, ui) ? ` / ${r5SlotLabel(mod.category, ui)}` : null}
            {mod.included ? null : (
              <>
                {" "}
                <button
                  className="btn danger"
                  onClick={() =>
                    patch({
                      vehicle_mods: (ch.vehicle_mods || []).filter((row) => row.id !== mod.id),
                      cyberware: removeWareTree(ch.cyberware || [], mod.id),
                    })
                  }
                >
                  {ui("common.remove")}
                </button>
              </>
            )}
            {mod.rating_max > 0 && !mod.included ? (
              <label title={ui("common.ratingHint")}>
                {ui("common.rating")}
                <input
                  type="number"
                  min={1}
                  max={mod.rating_max}
                  value={mod.rating}
                  onChange={(e) =>
                    patch({
                      vehicle_mods: (ch.vehicle_mods || []).map((row) =>
                        row.id === mod.id ? { ...row, rating: Number(e.target.value) } : row,
                      ),
                    })
                  }
                />
              </label>
            ) : null}
            {hosted.map((child) => (
              <WareRow
                key={child.id}
                item={child}
                childrenItems={(d.cyberware || []).filter((row) => row.parent_id === child.id)}
                catalogItems={catalog.cyberware.items}
                grades={catalog.cyberware.grades.filter(
                  (g) => !(d.disabled_cyberware_grades || []).includes(g.name),
                )}
                kind="cyberware"
                tr={tr}
                slotValue={slotPick[child.id] || ""}
                wareRanges={d.ware_ranges}
                nested
                onSlotChange={(wareId) => setSlotPick((cur) => ({ ...cur, [child.id]: wareId }))}
                onPatchRow={(id, next) =>
                  patch({
                    cyberware: (ch.cyberware || []).map((row) =>
                      row.id === id ? { ...row, ...next } : row,
                    ),
                  })
                }
                onRemove={(id) =>
                  patch({
                    cyberware: removeWareTree(ch.cyberware || [], id),
                  })
                }
                onAddChild={(wareId) => {
                  const spec = catalog.cyberware.items.find((w) => w.id === wareId);
                  if (!spec) return;
                  const range = wareBounds(spec, d.ware_ranges);
                  patch({
                    cyberware: [
                      ...(ch.cyberware || []),
                      {
                        ware_id: spec.id,
                        rating: range.min,
                        grade: child.grade,
                        wireless: true,
                        parent_id: child.id,
                      },
                    ],
                  });
                }}
              />
            ))}
            {wareOptions.length ? (
              <div className="slot-picker">
                <select
                  aria-label={`${tr(mod.name)}: ${ui("veh.addSubsystem")}`}
                  value={chosenWare}
                  onChange={(e) =>
                    setSlotPick((cur) => ({ ...cur, [warePickKey]: e.target.value }))
                  }
                >
                  {wareOptions.map((ware) => {
                    const range = wareBounds(ware, d.ware_ranges);
                    const showRange = range.max > range.min || range.max > 1;
                    return (
                      <option key={ware.id} value={ware.id}>
                        {tr(ware.name)} / {ware.capacity ? `[${ware.capacity}]` : ware.category}
                        {showRange ? ` R${range.min}-${range.max}` : ""}
                      </option>
                    );
                  })}
                </select>
                <button
                  className="btn primary"
                  disabled={!chosenWare}
                  onClick={() => {
                    const spec = wareOptions.find((w) => w.id === chosenWare);
                    if (!spec) return;
                    const range = wareBounds(spec, d.ware_ranges);
                    patch({
                      cyberware: [
                        ...(ch.cyberware || []),
                        {
                          ware_id: spec.id,
                          rating: range.min,
                          grade: "Standard",
                          wireless: true,
                          parent_id: mod.id,
                        },
                      ],
                    });
                    setSlotPick((cur) => ({ ...cur, [warePickKey]: "" }));
                  }}
                >
                  {ui("gear.addToSlot")}
                </button>
              </div>
            ) : null}
          </div>
        );
      })}
      <SlotPicker
        pickKey={item.id}
        rowName={tr(item.name)}
        label={ui("gear.addMod")}
        // used to lift as soon as the catalog search box below had text in
        // it, which nothing signposted
        options={addons.filter((mod) => mod.source === "SR5" || mod.source === "R5")}
        onAdd={(spec) =>
          patch({
            vehicle_mods: [
              ...(ch.vehicle_mods || []),
              { mod_id: spec.id, parent_id: item.id, rating: Math.max(1, spec.minrating || 1) },
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
