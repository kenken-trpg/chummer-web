"use client";
import { useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import { dropTree } from "@/lib/character/gear";

export function CommlinkGear({ catalog, character: ch, d, tr, patch }: TabPanelProps) {
  const [gearSearch, setGearSearch] = useState("");
  const [slotPick, setSlotPick] = useState<Record<string, string>>({});
  const [extraPick, setExtraPick] = useState<Record<string, string>>({});

  return (
    <>
      <>
        {(d.commlinks || []).map((item) => (
          <div className="cyber-item" key={item.id}>
            <div>
              <b>{tr(item.name)}</b>
              <div className="muted">
                {item.name}
                {item.category && item.category !== "Commlinks" ? ` / ${tr(item.category)}` : ""}
                {" / "}DR {item.device_rating} / DP {item.dataprocessing} / FW {item.firewall} /{" "}
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
                          commlinks: (ch.commlinks || []).map((row) =>
                            row.id === item.id ? { ...row, rating: Number(e.target.value) } : row,
                          ),
                        })
                      }
                    />
                  </label>
                </div>
              ) : null}
              {(d.apps || [])
                .filter((app) => app.parent_id === item.id)
                .map((app) => (
                  <div className="muted" key={app.id} style={{ marginTop: 6 }}>
                    {tr(app.label || app.name)}
                    {app.nuyen ? ` / ${app.nuyen.toLocaleString()}¥` : ""}{" "}
                    <button
                      className="btn danger"
                      onClick={() =>
                        patch({
                          apps: (ch.apps || []).filter((row) => row.id !== app.id),
                        })
                      }
                    >
                      外す
                    </button>
                    {app.rating_max > 0 ? (
                      <label>
                        Rating
                        <input
                          type="number"
                          min={1}
                          max={app.rating_max}
                          value={app.rating}
                          onChange={(e) =>
                            patch({
                              apps: (ch.apps || []).map((row) =>
                                row.id === app.id
                                  ? { ...row, rating: Number(e.target.value) }
                                  : row,
                              ),
                            })
                          }
                        />
                      </label>
                    ) : null}
                    {app.extra_kind === "skill" ? (
                      <label>
                        技能
                        <select
                          value={app.extra || ""}
                          onChange={(e) =>
                            patch({
                              apps: (ch.apps || []).map((row) =>
                                row.id === app.id ? { ...row, extra: e.target.value } : row,
                              ),
                            })
                          }
                        >
                          <option value="">選択</option>
                          {(app.extra_options || []).map((name) => (
                            <option key={name} value={name}>
                              {tr(name)}
                            </option>
                          ))}
                        </select>
                      </label>
                    ) : null}
                    {app.extra_kind === "text" ? (
                      <label>
                        対象
                        <input
                          value={app.extra || ""}
                          onChange={(e) =>
                            patch({
                              apps: (ch.apps || []).map((row) =>
                                row.id === app.id ? { ...row, extra: e.target.value } : row,
                              ),
                            })
                          }
                        />
                      </label>
                    ) : null}
                  </div>
                ))}
              <div className="cyber-controls">
                <select
                  value={slotPick[item.id] || ""}
                  onChange={(e) => setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
                >
                  <option value="">アプリを追加</option>
                  {(catalog.apps || [])
                    .filter((app) => app.source === "SR5")
                    .filter(
                      (app) =>
                        app.needs_extra ||
                        !(d.apps || []).some(
                          (row) => row.parent_id === item.id && row.gear_id === app.id,
                        ),
                    )
                    .map((app) => (
                      <option key={app.id} value={app.id}>
                        {tr(app.name)} ({app.cost}¥)
                      </option>
                    ))}
                </select>
                {(() => {
                  const spec = (catalog.apps || []).find((app) => app.id === slotPick[item.id]);
                  if (spec?.extra_kind !== "skill") return null;
                  return (
                    <select
                      value={extraPick[item.id] || ""}
                      onChange={(e) =>
                        setExtraPick((cur) => ({ ...cur, [item.id]: e.target.value }))
                      }
                    >
                      <option value="">技能</option>
                      {(spec.extra_options || []).map((name) => (
                        <option key={name} value={name}>
                          {tr(name)}
                        </option>
                      ))}
                    </select>
                  );
                })()}
                <button
                  className="btn"
                  disabled={!slotPick[item.id]}
                  onClick={() => {
                    const wareId = slotPick[item.id];
                    const spec = (catalog.apps || []).find((app) => app.id === wareId);
                    if (!spec) return;
                    patch({
                      apps: [
                        ...(ch.apps || []),
                        {
                          gear_id: spec.id,
                          rating: Math.max(1, spec.minrating || 1),
                          parent_id: item.id,
                          extra: extraPick[item.id] || undefined,
                        },
                      ],
                    });
                    setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
                    setExtraPick((cur) => ({ ...cur, [item.id]: "" }));
                  }}
                >
                  装着
                </button>
              </div>
              {(d.gear || [])
                .filter((acc) => acc.parent_id === item.id)
                .map((acc) => (
                  <div className="muted" key={acc.id} style={{ marginTop: 6 }}>
                    {tr(acc.label || acc.name)}
                    {acc.included ? " / 付属" : ` / ${acc.nuyen.toLocaleString()}¥`}{" "}
                    <button
                      className="btn danger"
                      onClick={() =>
                        patch({
                          gear: dropTree(ch.gear || [], acc.id),
                        })
                      }
                    >
                      外す
                    </button>
                  </div>
                ))}
              <div className="cyber-controls">
                <select
                  value={slotPick[`${item.id}-acc`] || ""}
                  onChange={(e) =>
                    setSlotPick((cur) => ({ ...cur, [`${item.id}-acc`]: e.target.value }))
                  }
                >
                  <option value="">アクセサリを追加</option>
                  {(catalog.gear || [])
                    .filter(
                      (mod) =>
                        mod.category === "Commlink Accessories" ||
                        (mod.required_categories || []).includes("Commlinks") ||
                        (item.category === "PI-Tac" && mod.category === "PI-Tac Programs"),
                    )
                    .filter(
                      (mod) =>
                        gearSearch.trim() ||
                        mod.source === "SR5" ||
                        (item.category === "PI-Tac" && mod.category === "PI-Tac Programs"),
                    )
                    .filter(
                      (mod) =>
                        !(d.gear || []).some(
                          (row) => row.parent_id === item.id && row.gear_id === mod.id,
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
                  disabled={!slotPick[`${item.id}-acc`]}
                  onClick={() => {
                    const wareId = slotPick[`${item.id}-acc`];
                    const spec = (catalog.gear || []).find((mod) => mod.id === wareId);
                    if (!spec) return;
                    patch({
                      gear: [
                        ...(ch.gear || []),
                        {
                          gear_id: spec.id,
                          rating: Math.max(1, spec.minrating || 1),
                          parent_id: item.id,
                        },
                      ],
                    });
                    setSlotPick((cur) => ({ ...cur, [`${item.id}-acc`]: "" }));
                  }}
                >
                  装着
                </button>
              </div>
            </div>
            <button
              className="btn danger"
              onClick={() =>
                patch({
                  commlinks: (ch.commlinks || []).filter((row) => row.id !== item.id),
                  apps: (ch.apps || []).filter((row) => row.parent_id !== item.id),
                  gear: dropTree(ch.gear || [], item.id),
                })
              }
            >
              削除
            </button>
          </div>
        ))}
      </>

      <input
        type="search"
        placeholder="通信機を検索"
        value={gearSearch}
        onChange={(e) => setGearSearch(e.target.value)}
      />

      <div className="quality-list">
        {(catalog.commlinks || [])
          .filter((item) => {
            const q = gearSearch.trim().toLowerCase();
            if (q)
              return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
            return item.source === "SR5";
          })
          .slice(0, 40)
          .map((item) => (
            <div className="quality-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / DR {item.devicerating} / DP {item.dataprocessing} / FW{" "}
                  {item.firewall} / {item.cost}¥ / {item.avail || "-"} / {item.source}
                </div>
              </div>
              <button
                className="btn primary"
                onClick={() =>
                  patch({
                    commlinks: [
                      ...(ch.commlinks || []),
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
