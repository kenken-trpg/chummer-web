"use client";
import { useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import { SENSOR_DEVICE_CATS } from "@/lib/character/constants";
import { dropTree } from "@/lib/character/gear";
import { deviceRatingBit } from "@/lib/character/format";

export function SensorGear({ catalog, character: ch, d, tr, patch }: TabPanelProps) {
  const [gearSearch, setGearSearch] = useState("");
  const [gearCat, setGearCat] = useState("all");
  const [slotPick, setSlotPick] = useState<Record<string, string>>({});

  return (
    <>
      <>
        {(d.sensors || [])
          .filter((item) => !item.parent_id)
          .map((item) => {
            const childrenItems = (d.sensors || []).filter((child) => child.parent_id === item.id);
            const addons = (catalog.sensors || []).filter(
              (mod) =>
                (item.addoncategories || []).includes(mod.category) && mod.category !== "Custom",
            );
            return (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name} / {tr(item.category)}
                    {deviceRatingBit(item)}
                    {item.capacity_max ? ` / 容量 ${item.capacity_used}/${item.capacity_max}` : ""}
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
                                row.id === item.id
                                  ? { ...row, rating: Number(e.target.value) }
                                  : row,
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
                      {child.included ? " / 付属" : ` / ${child.nuyen.toLocaleString()}¥`}
                      {child.capacity_cost ? ` / 容量 ${child.capacity_cost}` : ""}
                      {child.included ? null : (
                        <>
                          {" "}
                          <button
                            className="btn danger"
                            onClick={() =>
                              patch({
                                sensors: dropTree(ch.sensors || [], child.id),
                              })
                            }
                          >
                            外す
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
                            {grand.capacity_cost ? ` / 容量 ${grand.capacity_cost}` : ""}{" "}
                            <button
                              className="btn danger"
                              onClick={() =>
                                patch({
                                  sensors: (ch.sensors || []).filter((row) => row.id !== grand.id),
                                })
                              }
                            >
                              外す
                            </button>
                          </div>
                        ))}
                      {(child.addoncategories || []).length ? (
                        <div className="cyber-controls">
                          <select
                            value={slotPick[child.id] || ""}
                            onChange={(e) =>
                              setSlotPick((cur) => ({ ...cur, [child.id]: e.target.value }))
                            }
                          >
                            <option value="">機能を追加</option>
                            {(catalog.sensors || [])
                              .filter((mod) => (child.addoncategories || []).includes(mod.category))
                              .filter((mod) => mod.category !== "Custom")
                              .filter((mod) => mod.source === "SR5")
                              .filter(
                                (mod) =>
                                  !(d.sensors || []).some(
                                    (row) => row.parent_id === child.id && row.gear_id === mod.id,
                                  ),
                              )
                              .map((mod) => (
                                <option key={mod.id} value={mod.id}>
                                  {tr(mod.name)} ({mod.cost}¥)
                                </option>
                              ))}
                          </select>
                          <button
                            className="btn"
                            disabled={!slotPick[child.id]}
                            onClick={() => {
                              const wareId = slotPick[child.id];
                              const spec = (catalog.sensors || []).find((mod) => mod.id === wareId);
                              if (!spec) return;
                              patch({
                                sensors: [
                                  ...(ch.sensors || []),
                                  {
                                    gear_id: spec.id,
                                    rating: Math.max(1, spec.minrating || 1),
                                    parent_id: child.id,
                                  },
                                ],
                              });
                              setSlotPick((cur) => ({ ...cur, [child.id]: "" }));
                            }}
                          >
                            装着
                          </button>
                        </div>
                      ) : null}
                    </div>
                  ))}
                  {addons.length ? (
                    <div className="cyber-controls">
                      <select
                        value={slotPick[item.id] || ""}
                        onChange={(e) =>
                          setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))
                        }
                      >
                        <option value="">機能／センサーを追加</option>
                        {addons
                          .filter((mod) => mod.source === "SR5")
                          .filter((mod) => !childrenItems.some((child) => child.gear_id === mod.id))
                          .map((mod) => (
                            <option key={mod.id} value={mod.id}>
                              {tr(mod.name)} ({mod.cost}¥)
                            </option>
                          ))}
                      </select>
                      <button
                        className="btn"
                        disabled={!slotPick[item.id]}
                        onClick={() => {
                          const wareId = slotPick[item.id];
                          const spec = addons.find((mod) => mod.id === wareId);
                          if (!spec) return;
                          patch({
                            sensors: [
                              ...(ch.sensors || []),
                              {
                                gear_id: spec.id,
                                rating: Math.max(1, spec.minrating || 1),
                                parent_id: item.id,
                              },
                            ],
                          });
                          setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
                        }}
                      >
                        装着
                      </button>
                    </div>
                  ) : null}
                </div>
                <button
                  className="btn danger"
                  onClick={() =>
                    patch({
                      sensors: dropTree(ch.sensors || [], item.id),
                    })
                  }
                >
                  削除
                </button>
              </div>
            );
          })}
      </>

      <div className="option-row">
        <button
          className={`tab ${gearCat === "all" ? "active" : ""}`}
          onClick={() => setGearCat("all")}
        >
          すべて
        </button>
        {[
          ...new Set(
            (catalog.sensors || [])
              .filter((item) => SENSOR_DEVICE_CATS.has(item.category))
              .map((item) => item.category),
          ),
        ]
          .sort()
          .map((cat) => (
            <button
              key={cat}
              className={`tab ${gearCat === cat ? "active" : ""}`}
              onClick={() => setGearCat(cat)}
            >
              {tr(cat)}
            </button>
          ))}
      </div>
      <input
        type="search"
        placeholder="センサーを検索"
        value={gearSearch}
        onChange={(e) => setGearSearch(e.target.value)}
      />

      <div className="quality-list">
        {(catalog.sensors || [])
          .filter((item) => SENSOR_DEVICE_CATS.has(item.category) && !item.requireparent)
          .filter((item) => gearCat === "all" || item.category === gearCat)
          .filter((item) => {
            const q = gearSearch.trim().toLowerCase();
            if (q)
              return (
                item.name.toLowerCase().includes(q) ||
                tr(item.name).toLowerCase().includes(q) ||
                item.category.toLowerCase().includes(q)
              );
            return item.source === "SR5";
          })
          .slice(0, 40)
          .map((item) => (
            <div className="quality-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / {tr(item.category)}
                  {item.maxrating > 0 ? ` / R${item.minrating || 1}-${item.maxrating}` : ""} /{" "}
                  {item.cost}¥ / {item.avail || "-"} / {item.source}
                </div>
              </div>
              <button
                className="btn primary"
                onClick={() =>
                  patch({
                    sensors: [
                      ...(ch.sensors || []),
                      { gear_id: item.id, rating: Math.max(1, item.minrating || 1) },
                    ],
                  })
                }
              >
                購入
              </button>
            </div>
          ))}
      </div>
    </>
  );
}
