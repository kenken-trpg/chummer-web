"use client";
import { useState } from "react";
import type { TabPanelProps } from "@/components/character/types";

export function RccGear({ catalog, character: ch, d, tr, patch }: TabPanelProps) {
  const [gearSearch, setGearSearch] = useState("");
  const [slotPick, setSlotPick] = useState<Record<string, string>>({});
  const [extraPick, setExtraPick] = useState<Record<string, string>>({});

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
              <div className="cyber-controls">
                <select
                  value={slotPick[item.id] || ""}
                  onChange={(e) => {
                    setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }));
                    setExtraPick((cur) => ({ ...cur, [item.id]: "" }));
                  }}
                >
                  <option value="">オートソフトを追加</option>
                  {(catalog.programs || [])
                    .filter((prog) => prog.program_host === "rccs")
                    .filter((prog) => prog.source === "SR5" || prog.source === "R5")
                    .filter(
                      (prog) =>
                        prog.needs_extra ||
                        !(d.programs || []).some(
                          (row) => row.parent_id === item.id && row.gear_id === prog.id,
                        ),
                    )
                    .map((prog) => (
                      <option key={prog.id} value={prog.id}>
                        {tr(prog.name)} ({prog.cost}¥)
                      </option>
                    ))}
                </select>
                {(() => {
                  const spec = (catalog.programs || []).find(
                    (prog) => prog.id === slotPick[item.id],
                  );
                  if (spec?.extra_kind === "skill" || spec?.extra_kind === "group") {
                    return (
                      <select
                        value={extraPick[item.id] || ""}
                        onChange={(e) =>
                          setExtraPick((cur) => ({ ...cur, [item.id]: e.target.value }))
                        }
                      >
                        <option value="">
                          {spec.extra_kind === "group" ? "グループ" : "技能"}
                        </option>
                        {(spec.extra_options || []).map((name) => (
                          <option key={name} value={name}>
                            {tr(name)}
                          </option>
                        ))}
                      </select>
                    );
                  }
                  if (spec?.extra_kind === "text") {
                    return (
                      <>
                        <input
                          list={`pick-extra-${item.id}`}
                          placeholder="対象"
                          value={extraPick[item.id] || ""}
                          onChange={(e) =>
                            setExtraPick((cur) => ({ ...cur, [item.id]: e.target.value }))
                          }
                        />
                        <datalist id={`pick-extra-${item.id}`}>
                          {(spec.extra_options || []).slice(0, 80).map((name) => (
                            <option key={name} value={name} />
                          ))}
                        </datalist>
                      </>
                    );
                  }
                  return null;
                })()}
                <button
                  className="btn"
                  disabled={!slotPick[item.id]}
                  onClick={() => {
                    const wareId = slotPick[item.id];
                    const spec = (catalog.programs || []).find((prog) => prog.id === wareId);
                    if (!spec) return;
                    patch({
                      programs: [
                        ...(ch.programs || []),
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

      <input
        type="search"
        placeholder="RCCを検索"
        aria-label="RCCを検索"
        value={gearSearch}
        onChange={(e) => setGearSearch(e.target.value)}
      />

      <div className="quality-list">
        {(catalog.rccs || [])
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
                  {item.firewall} / プログラム {item.programs} / {item.cost}¥ / {item.avail || "-"}{" "}
                  / {item.source}
                </div>
              </div>
              <button
                className="btn primary"
                onClick={() =>
                  patch({
                    rccs: [
                      ...(ch.rccs || []),
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
