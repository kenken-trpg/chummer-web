"use client";

import { useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import { OPTICS_DEVICE_CATS } from "@/lib/character/constants";
import { dropTree } from "@/lib/character/gear";

export function OpticsGear({ catalog, character: ch, d, tr, patch, setCharacter }: TabPanelProps) {
  const [gearSearch, setGearSearch] = useState("");
  const [gearCat, setGearCat] = useState("all");
  const [slotPick, setSlotPick] = useState<Record<string, string>>({});
  const [extraPick, setExtraPick] = useState<Record<string, string>>({});


  return (
    <>
              <>
                {(d.optics || []).filter((item) => !item.parent_id).map((item) => {
                  const childrenItems = (d.optics || []).filter((child) => child.parent_id === item.id);
                  const addons = (catalog.optics || []).filter((mod) => (
                    (item.addoncategories || []).includes(mod.category) && Boolean(mod.requireparent)
                  ));
                  return (
                    <div className="cyber-item" key={item.id}>
                      <div>
                        <b>{tr(item.name)}</b>
                        <div className="muted">
                          {item.name} / {tr(item.category)}
                          {item.capacity_max ? ` / 容量 ${item.capacity_used}/${item.capacity_max}` : ""}
                          {" / "}{item.nuyen.toLocaleString()}¥ / {item.source}
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
                                onChange={(e) => patch({
                                  optics: (ch.optics || []).map((row) => (
                                    row.id === item.id ? { ...row, rating: Number(e.target.value) } : row
                                  )),
                                })}
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
                                <button className="btn danger" onClick={() => patch({
                                  optics: (ch.optics || []).filter((row) => row.id !== child.id),
                                })}>外す</button>
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
                                  onChange={(e) => patch({
                                    optics: (ch.optics || []).map((row) => (
                                      row.id === child.id ? { ...row, rating: Number(e.target.value) } : row
                                    )),
                                  })}
                                />
                              </label>
                            ) : null}
                          </div>
                        ))}
                        {addons.length ? (
                          <div className="cyber-controls">
                            <select
                              value={slotPick[item.id] || ""}
                              onChange={(e) => setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
                            >
                              <option value="">改造を追加</option>
                              {addons
                                .filter((mod) => !childrenItems.some((child) => child.gear_id === mod.id))
                                .map((mod) => (
                                  <option key={mod.id} value={mod.id}>{tr(mod.name)} ({mod.cost}¥)</option>
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
                                  optics: [...(ch.optics || []), { gear_id: spec.id, rating: Math.max(1, spec.minrating || 1), parent_id: item.id }],
                                });
                                setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
                              }}
                            >
                              装着
                            </button>
                          </div>
                        ) : null}
                      </div>
                      <button className="btn danger" onClick={() => {
                        const drop = new Set<string>([item.id]);
                        let grew = true;
                        const rows = ch.optics || [];
                        while (grew) {
                          grew = false;
                          for (const row of rows) {
                            if (row.parent_id && drop.has(row.parent_id) && row.id && !drop.has(row.id)) {
                              drop.add(row.id);
                              grew = true;
                            }
                          }
                        }
                        patch({ optics: rows.filter((row) => !row.id || !drop.has(row.id)) });
                      }}>削除</button>
                    </div>
                  );
                })}
              </>

      <div className="option-row">
        <button className={`tab ${gearCat === "all" ? "active" : ""}`} onClick={() => setGearCat("all")}>すべて</button>
        {[...new Set((catalog.optics || []).filter((item) => OPTICS_DEVICE_CATS.has(item.category)).map((item) => item.category))].sort().map((cat) => (
          <button key={cat} className={`tab ${gearCat === cat ? "active" : ""}`} onClick={() => setGearCat(cat)}>{tr(cat)}</button>
        ))}
      </div>
      <input
        type="search"
        placeholder="視覚／聴覚を検索"
        value={gearSearch}
        onChange={(e) => setGearSearch(e.target.value)}
      />

      <div className="quality-list">
{(catalog.optics || [])
                .filter((item) => OPTICS_DEVICE_CATS.has(item.category) && !item.requireparent)
                .filter((item) => gearCat === "all" || item.category === gearCat)
                .filter((item) => {
                  const q = gearSearch.trim().toLowerCase();
                  if (q) return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q) || item.category.toLowerCase().includes(q);
                  return item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">
                        {item.name} / {tr(item.category)}{item.maxrating > 0 ? ` / R${item.minrating || 1}-${item.maxrating}` : ""} / {item.cost}¥ / {item.avail || "-"} / {item.source}
</div>
                    </div>
                    <button className="btn primary" onClick={() => patch({
                      optics: [...(ch.optics || []), { gear_id: item.id, rating: Math.max(1, item.minrating || 1) }],
                    })}>購入</button>
                  </div>
                ))}
      </div>
    </>
  );
}
