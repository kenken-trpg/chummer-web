"use client";
import { AddonSelect } from "@/components/character/AddonSelect";
import { CatalogPicker } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";

export function RccGear({ catalog, character: ch, d, tr, patch }: TabPanelProps) {
  return (
    <>
      <>
        {(d.rccs || []).map((item) => (
          <div className="cyber-item" key={item.id}>
            <div>
              <b>{tr(item.name)}</b>
              <div className="muted">
                {item.name} / DR {item.device_rating} / DP {item.dataprocessing} / FW{" "}
                {item.firewall} / プログラム {item.program_used ?? 0}/
                {item.program_max ?? item.programs ?? 0} / {item.nuyen.toLocaleString()}¥ /{" "}
                {item.source}
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
                          rccs: (ch.rccs || []).map((row) =>
                            row.id === item.id ? { ...row, rating: Number(e.target.value) } : row,
                          ),
                        })
                      }
                    />
                  </label>
                </div>
              ) : null}
              {(d.programs || [])
                .filter((prog) => prog.parent_id === item.id)
                .map((prog) => (
                  <div className="muted" key={prog.id} style={{ marginTop: 6 }}>
                    {tr(prog.label || prog.name)}
                    {prog.rating_max > 0 ? ` R${prog.rating}` : ""}
                    {` / ${prog.nuyen.toLocaleString()}¥`}{" "}
                    <button
                      className="btn danger"
                      onClick={() =>
                        patch({
                          programs: (ch.programs || []).filter((row) => row.id !== prog.id),
                        })
                      }
                    >
                      外す
                    </button>
                    {prog.rating_max > 0 ? (
                      <label>
                        Rating
                        <input
                          type="number"
                          min={1}
                          max={prog.rating_max}
                          value={prog.rating}
                          onChange={(e) =>
                            patch({
                              programs: (ch.programs || []).map((row) =>
                                row.id === prog.id
                                  ? { ...row, rating: Number(e.target.value) }
                                  : row,
                              ),
                            })
                          }
                        />
                      </label>
                    ) : null}
                    {prog.extra_kind === "skill" ? (
                      <label>
                        技能
                        <select
                          value={prog.extra || ""}
                          onChange={(e) =>
                            patch({
                              programs: (ch.programs || []).map((row) =>
                                row.id === prog.id ? { ...row, extra: e.target.value } : row,
                              ),
                            })
                          }
                        >
                          <option value="">選択</option>
                          {(prog.extra_options || []).map((name) => (
                            <option key={name} value={name}>
                              {tr(name)}
                            </option>
                          ))}
                        </select>
                      </label>
                    ) : null}
                    {prog.extra_kind === "group" ? (
                      <label>
                        グループ
                        <select
                          value={prog.extra || ""}
                          onChange={(e) =>
                            patch({
                              programs: (ch.programs || []).map((row) =>
                                row.id === prog.id ? { ...row, extra: e.target.value } : row,
                              ),
                            })
                          }
                        >
                          <option value="">選択</option>
                          {(prog.extra_options || []).map((name) => (
                            <option key={name} value={name}>
                              {tr(name)}
                            </option>
                          ))}
                        </select>
                      </label>
                    ) : null}
                    {prog.extra_kind === "text" ? (
                      <label>
                        対象
                        <input
                          list={`prog-extra-${prog.id}`}
                          value={prog.extra || ""}
                          onChange={(e) =>
                            patch({
                              programs: (ch.programs || []).map((row) =>
                                row.id === prog.id ? { ...row, extra: e.target.value } : row,
                              ),
                            })
                          }
                        />
                        <datalist id={`prog-extra-${prog.id}`}>
                          {(prog.extra_options || []).slice(0, 80).map((name) => (
                            <option key={name} value={name} />
                          ))}
                        </datalist>
                      </label>
                    ) : null}
                  </div>
                ))}
              <AddonSelect
                rowName={tr(item.name)}
                prompt="オートソフトを追加"
                tr={tr}
                options={(catalog.programs || []).filter(
                  (prog) =>
                    prog.program_host === "rccs" &&
                    (prog.source === "SR5" || prog.source === "R5") &&
                    (prog.needs_extra ||
                      !(d.programs || []).some(
                        (row) => row.parent_id === item.id && row.gear_id === prog.id,
                      )),
                )}
                extraFor={(prog) => {
                  if (prog.extra_kind === "skill") {
                    return { label: "技能", values: prog.extra_options || [] };
                  }
                  if (prog.extra_kind === "group") {
                    return { label: "グループ", values: prog.extra_options || [] };
                  }
                  // a vehicle autosoft names a model, which is not a closed set
                  if (prog.extra_kind === "text") {
                    return { label: "対象", values: prog.extra_options || [], freeText: true };
                  }
                  return null;
                }}
                onAdd={(prog, extra) =>
                  patch({
                    programs: [
                      ...(ch.programs || []),
                      {
                        gear_id: prog.id,
                        rating: Math.max(1, prog.minrating || 1),
                        parent_id: item.id,
                        extra,
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
                  rccs: (ch.rccs || []).filter((row) => row.id !== item.id),
                  programs: (ch.programs || []).filter((row) => row.parent_id !== item.id),
                })
              }
            >
              削除
            </button>
          </div>
        ))}
      </>

      <CatalogPicker
        items={catalog.rccs || []}
        label="RCCを検索"
        tr={tr}
        describe={(item) => (
          <>
            {item.name} / DR {item.devicerating} / DP {item.dataprocessing} / FW {item.firewall} /{" "}
            プログラム {item.programs} / {item.cost}¥ / {item.avail || "-"} / {item.source}
          </>
        )}
        onAdd={(item) =>
          patch({
            rccs: [
              ...(ch.rccs || []),
              { gear_id: item.id, rating: Math.max(1, item.minrating || 1) },
            ],
          })
        }
      />
    </>
  );
}
