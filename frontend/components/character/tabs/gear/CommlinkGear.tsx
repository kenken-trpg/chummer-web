"use client";
import { AddonSelect } from "@/components/character/AddonSelect";
import { CatalogPicker } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { dropTree } from "@/lib/character/gear";

export function CommlinkGear({ catalog, character: ch, d, tr, patch }: TabPanelProps) {
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
              <AddonSelect
                rowName={tr(item.name)}
                prompt="アプリを追加"
                tr={tr}
                options={(catalog.apps || []).filter(
                  (app) =>
                    app.source === "SR5" &&
                    (app.needs_extra ||
                      !(d.apps || []).some(
                        (row) => row.parent_id === item.id && row.gear_id === app.id,
                      )),
                )}
                extraFor={(app) =>
                  app.extra_kind === "skill"
                    ? { label: "技能", values: app.extra_options || [] }
                    : null
                }
                onAdd={(app, extra) =>
                  patch({
                    apps: [
                      ...(ch.apps || []),
                      {
                        gear_id: app.id,
                        rating: Math.max(1, app.minrating || 1),
                        parent_id: item.id,
                        extra,
                      },
                    ],
                  })
                }
              />
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
              <AddonSelect
                rowName={tr(item.name)}
                prompt="アクセサリを追加"
                tr={tr}
                // PI-Tac programs are core to that device even though they are
                // not SR5-sourced, so they come through regardless. The rest
                // used to appear only while the catalog search box below had
                // text in it — two unrelated controls wired together.
                options={(catalog.gear || []).filter(
                  (mod) =>
                    (mod.category === "Commlink Accessories" ||
                      (mod.required_categories || []).includes("Commlinks") ||
                      (item.category === "PI-Tac" && mod.category === "PI-Tac Programs")) &&
                    !(d.gear || []).some(
                      (row) => row.parent_id === item.id && row.gear_id === mod.id,
                    ),
                )}
                onAdd={(mod) =>
                  patch({
                    gear: [
                      ...(ch.gear || []),
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

      <CatalogPicker
        items={catalog.commlinks || []}
        label="通信機を検索"
        tr={tr}
        describe={(item) => (
          <>
            {item.name} / DR {item.devicerating} / DP {item.dataprocessing} / FW {item.firewall} /{" "}
            {item.cost}¥ / {item.avail || "-"} / {item.source}
          </>
        )}
        onAdd={(item) =>
          patch({
            commlinks: [
              ...(ch.commlinks || []),
              { gear_id: item.id, rating: Math.max(1, item.minrating || 1) },
            ],
          })
        }
      />
    </>
  );
}
