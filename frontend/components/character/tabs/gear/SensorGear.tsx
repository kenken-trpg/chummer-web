"use client";
import { AddonSelect } from "@/components/character/AddonSelect";
import { CatalogPicker } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { SENSOR_DEVICE_CATS } from "@/lib/character/constants";
import { dropTree } from "@/lib/character/gear";
import { deviceRatingBit } from "@/lib/character/format";

export function SensorGear({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  /** Sensor housings nest two deep: housing → sensor → upgrade. */
  const install = (gearId: string, parentId: string, minrating: number) =>
    patch({
      sensors: [
        ...(ch.sensors || []),
        { gear_id: gearId, rating: Math.max(1, minrating || 1), parent_id: parentId },
      ],
    });

  return (
    <>
      {(d.sensors || [])
        .filter((item) => !item.parent_id)
        .map((item) => {
          const childrenItems = (d.sensors || []).filter((child) => child.parent_id === item.id);
          const addons = (catalog.sensors || []).filter(
            (mod) =>
              (item.addoncategories || []).includes(mod.category) &&
              mod.category !== "Custom" &&
              mod.source === "SR5" &&
              !childrenItems.some((child) => child.gear_id === mod.id),
          );
          return (
            <div className="cyber-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / {tr(item.category)}
                  {deviceRatingBit(item)}
                  {item.capacity_max
                    ? ui("gear.capacity", {
                        used: item.capacity_used ?? 0,
                        max: item.capacity_max,
                      })
                    : ""}
                  {" / "}
                  {item.nuyen.toLocaleString()}¥ / {item.source}
                </div>
                {item.rating_max > 0 ? (
                  <div className="cyber-controls">
                    <label>
                      Rating
                      <input
                        type="number"
                        min={1}
                        max={item.rating_max}
                        value={item.rating}
                        onChange={(e) =>
                          patch({
                            sensors: (ch.sensors || []).map((row) =>
                              row.id === item.id ? { ...row, rating: Number(e.target.value) } : row,
                            ),
                          })
                        }
                      />
                    </label>
                  </div>
                ) : null}
                {childrenItems.map((child) => (
                  <div className="muted" key={child.id} style={{ marginTop: 6 }}>
                    {tr(child.name)}
                    {child.rating_max > 0 ? ` R${child.rating}` : ""}
                    {child.included
                      ? ` / ${ui("common.included")}`
                      : ` / ${child.nuyen.toLocaleString()}¥`}
                    {child.capacity_cost
                      ? ui("gear.capacityCost", { cost: child.capacity_cost })
                      : ""}
                    {child.included ? null : (
                      <>
                        {" "}
                        <button
                          className="btn danger"
                          aria-label={ui("common.removeLabel", { name: tr(child.name) })}
                          onClick={() => patch({ sensors: dropTree(ch.sensors || [], child.id) })}
                        >
                          {ui("common.remove")}
                        </button>
                      </>
                    )}
                    {child.rating_max > 0 && !child.included ? (
                      <label>
                        Rating
                        <input
                          type="number"
                          min={1}
                          max={child.rating_max}
                          value={child.rating}
                          onChange={(e) =>
                            patch({
                              sensors: (ch.sensors || []).map((row) =>
                                row.id === child.id
                                  ? { ...row, rating: Number(e.target.value) }
                                  : row,
                              ),
                            })
                          }
                        />
                      </label>
                    ) : null}
                    {(d.sensors || [])
                      .filter((grand) => grand.parent_id === child.id)
                      .map((grand) => (
                        <div key={grand.id} style={{ marginTop: 4, marginLeft: 12 }}>
                          {tr(grand.name)}
                          {grand.capacity_cost
                            ? ui("gear.capacityCost", { cost: grand.capacity_cost })
                            : ""}{" "}
                          <button
                            className="btn danger"
                            aria-label={ui("common.removeLabel", { name: tr(grand.name) })}
                            onClick={() =>
                              patch({
                                sensors: (ch.sensors || []).filter((row) => row.id !== grand.id),
                              })
                            }
                          >
                            {ui("common.remove")}
                          </button>
                        </div>
                      ))}
                    <AddonSelect
                      rowName={tr(child.name)}
                      prompt={ui("gear.addSensorFn")}
                      tr={tr}
                      options={(catalog.sensors || []).filter(
                        (mod) =>
                          (child.addoncategories || []).includes(mod.category) &&
                          mod.category !== "Custom" &&
                          mod.source === "SR5" &&
                          !(d.sensors || []).some(
                            (row) => row.parent_id === child.id && row.gear_id === mod.id,
                          ),
                      )}
                      onAdd={(mod) => install(mod.id, child.id, mod.minrating)}
                    />
                  </div>
                ))}
                <AddonSelect
                  rowName={tr(item.name)}
                  prompt={ui("gear.addSensorOrFn")}
                  tr={tr}
                  options={addons}
                  onAdd={(mod) => install(mod.id, item.id, mod.minrating)}
                />
              </div>
              <button
                className="btn danger"
                aria-label={ui("common.deleteLabel", { name: tr(item.name) })}
                onClick={() => patch({ sensors: dropTree(ch.sensors || [], item.id) })}
              >
                {ui("common.delete")}
              </button>
            </div>
          );
        })}

      <CatalogPicker
        items={(catalog.sensors || []).filter(
          (item) => SENSOR_DEVICE_CATS.has(item.category) && !item.requireparent,
        )}
        label={ui("gear.searchSensor")}
        tr={tr}
        describe={(item) => (
          <>
            {item.name} / {tr(item.category)}
            {item.maxrating > 0 ? ` / R${item.minrating || 1}-${item.maxrating}` : ""} / {item.cost}
            ¥ / {item.avail || "-"} / {item.source}
          </>
        )}
        onAdd={(item) =>
          patch({
            sensors: [
              ...(ch.sensors || []),
              { gear_id: item.id, rating: Math.max(1, item.minrating || 1) },
            ],
          })
        }
      />
    </>
  );
}
