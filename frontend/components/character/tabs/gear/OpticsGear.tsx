"use client";
import { AddonSelect } from "@/components/character/AddonSelect";
import { CatalogPicker } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { OPTICS_DEVICE_CATS } from "@/lib/character/constants";
import { dropTree } from "@/lib/character/gear";

export function OpticsGear({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  return (
    <>
      {(d.optics || [])
        .filter((item) => !item.parent_id)
        .map((item) => {
          const childrenItems = (d.optics || []).filter((child) => child.parent_id === item.id);
          const addons = (catalog.optics || []).filter(
            (mod) =>
              (item.addoncategories || []).includes(mod.category) &&
              Boolean(mod.requireparent) &&
              !childrenItems.some((child) => child.gear_id === mod.id),
          );
          return (
            <div className="cyber-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / {tr(item.category)}
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
                            optics: (ch.optics || []).map((row) =>
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
                          onClick={() =>
                            patch({
                              optics: (ch.optics || []).filter((row) => row.id !== child.id),
                            })
                          }
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
                              optics: (ch.optics || []).map((row) =>
                                row.id === child.id
                                  ? { ...row, rating: Number(e.target.value) }
                                  : row,
                              ),
                            })
                          }
                        />
                      </label>
                    ) : null}
                  </div>
                ))}
                <AddonSelect
                  rowName={tr(item.name)}
                  prompt={ui("gear.addMod")}
                  options={addons}
                  tr={tr}
                  onAdd={(mod) =>
                    patch({
                      optics: [
                        ...(ch.optics || []),
                        {
                          gear_id: mod.id,
                          rating: Math.max(1, mod.minrating || 1),
                          parent_id: item.id,
                        },
                      ],
                    })
                  }
                />
              </div>
              <button
                className="btn danger"
                aria-label={ui("common.deleteLabel", { name: tr(item.name) })}
                onClick={() => patch({ optics: dropTree(ch.optics || [], item.id) })}
              >
                {ui("common.delete")}
              </button>
            </div>
          );
        })}

      <CatalogPicker
        items={(catalog.optics || []).filter(
          (item) => OPTICS_DEVICE_CATS.has(item.category) && !item.requireparent,
        )}
        label={ui("gear.searchOptics")}
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
            optics: [
              ...(ch.optics || []),
              { gear_id: item.id, rating: Math.max(1, item.minrating || 1) },
            ],
          })
        }
      />
    </>
  );
}
