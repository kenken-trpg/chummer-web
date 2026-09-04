"use client";
import { AddonSelect } from "@/components/character/AddonSelect";
import { CatalogPicker } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";

export function RccGear({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  return (
    <>
      <>
        {(d.rccs || []).map((item) => (
          <div className="cyber-item" key={item.id}>
            <div>
              <b>{tr(item.name)}</b>
              <div className="muted">
                {item.name} / DR {item.device_rating} / DP {item.dataprocessing} / FW{" "}
                {item.firewall}
                {ui("gear.programs", {
                  used: item.program_used ?? 0,
                  max: item.program_max ?? item.programs ?? 0,
                })}{" "}
                / {item.nuyen.toLocaleString()}¥ / {item.source}
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
                      {ui("common.remove")}
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
                        {ui("common.skill")}
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
                          <option value="">{ui("common.selectShort")}</option>
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
                        {ui("common.group")}
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
                          <option value="">{ui("common.selectShort")}</option>
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
                        {ui("common.target")}
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
                prompt={ui("gear.addAutosoft")}
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
                    return { label: ui("common.skill"), values: prog.extra_options || [] };
                  }
                  if (prog.extra_kind === "group") {
                    return { label: ui("common.group"), values: prog.extra_options || [] };
                  }
                  // a vehicle autosoft names a model, which is not a closed set
                  if (prog.extra_kind === "text") {
                    return {
                      label: ui("common.target"),
                      values: prog.extra_options || [],
                      freeText: true,
                    };
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
              {ui("common.delete")}
            </button>
          </div>
        ))}
      </>

      <CatalogPicker
        items={catalog.rccs || []}
        label={ui("gear.searchRcc")}
        tr={tr}
        describe={(item) => (
          <>
            {item.name} / DR {item.devicerating} / DP {item.dataprocessing} / FW {item.firewall}
            {ui("gear.programCount", { count: item.programs ?? "" })} / {item.cost}¥ /{" "}
            {item.avail || "-"} / {item.source}
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
