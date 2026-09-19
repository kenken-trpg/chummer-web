"use client";
import { AddonSelect } from "@/components/character/AddonSelect";
import { CatalogPicker } from "@/components/character/CatalogPicker";
import { DiscountToggle } from "@/components/character/DiscountToggle";
import { AppRows } from "@/components/character/tabs/gear/AppRows";
import { LooseProgramRows } from "@/components/character/tabs/gear/LooseProgramRows";
import { MatrixModRows } from "@/components/character/tabs/gear/MatrixModRows";
import { HelpTip } from "@/components/help/HelpTip";
import type { TabPanelProps } from "@/components/character/types";
import { DEFAULT_ARRAY_ORDER, MATRIX_ATTRS } from "@/lib/character/constants";
import { dropTree, swapMatrixOrder } from "@/lib/character/gear";

export function CyberdeckGear({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  return (
    <>
      <LooseProgramRows kind="cyberdecks" character={ch} d={d} tr={tr} ui={ui} patch={patch} />
      <>
        {(d.cyberdecks || []).length ? <p className="muted">{ui("deck.arrayNote")}</p> : null}
        {(d.cyberdecks || []).map((item) => (
          <div className="cyber-item" key={item.id}>
            <div>
              <b>{tr(item.name)}</b>
              <div className="muted">
                {item.name} / DR {item.device_rating} / ATK {item.attack} / SLZ {item.sleaze} / DP{" "}
                {item.dataprocessing} / FW {item.firewall}
                {ui("gear.programs", {
                  used: item.program_used ?? 0,
                  max: item.program_max ?? item.programs ?? 0,
                })}{" "}
                / {item.nuyen.toLocaleString()}¥ / {item.source}
              </div>
              <div className="cyber-controls">
                <DiscountToggle
                  list="cyberdecks"
                  id={item.id}
                  ch={ch}
                  d={d}
                  ui={ui}
                  patch={patch}
                />
              </div>
              {item.rating_max > 0 ? (
                <div className="cyber-controls">
                  <label title={ui("common.ratingHint")}>
                    {ui("common.rating")}
                    <input
                      type="number"
                      min={1}
                      max={item.rating_max}
                      value={item.rating}
                      onChange={(e) =>
                        patch({
                          cyberdecks: (ch.cyberdecks || []).map((row) =>
                            row.id === item.id ? { ...row, rating: Number(e.target.value) } : row,
                          ),
                        })
                      }
                    />
                  </label>
                </div>
              ) : null}
              {item.can_reorder && (item.array || []).length === 4 ? (
                <div className="matrix-array">
                  {MATRIX_ATTRS.map(([key, label]) => (
                    <label key={key}>
                      <HelpTip
                        label={ui("help.open", { label })}
                        lines={[
                          { label: ui(`help.matrix.${key}`) },
                          { label: ui("help.matrix.array") },
                        ]}
                      >
                        {label}
                      </HelpTip>
                      <select
                        aria-label={label}
                        value={String((item.array_order || DEFAULT_ARRAY_ORDER).indexOf(key))}
                        onChange={(e) =>
                          patch({
                            cyberdecks: (ch.cyberdecks || []).map((row) =>
                              row.id === item.id
                                ? {
                                    ...row,
                                    array_order: swapMatrixOrder(
                                      item.array_order,
                                      key,
                                      Number(e.target.value),
                                    ),
                                  }
                                : row,
                            ),
                          })
                        }
                      >
                        {(item.array || []).map((n, i) => (
                          <option key={`${key}-${i}`} value={i}>
                            {n}
                          </option>
                        ))}
                      </select>
                    </label>
                  ))}
                </div>
              ) : null}
              {(d.programs || [])
                .filter((prog) => prog.parent_id === item.id)
                .map((prog) => (
                  <div className="muted" key={prog.id} style={{ marginTop: 6 }}>
                    <HelpTip
                      label={ui("help.open", { label: tr(prog.name) })}
                      lines={[
                        { label: ui("help.program.slot") },
                        { label: ui("help.program.rating") },
                      ]}
                    >
                      {ui("help.program.statsLabel")}
                    </HelpTip>{" "}
                    {tr(prog.name)}
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
                      <label title={ui("common.ratingHint")}>
                        {ui("common.rating")}
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
                  </div>
                ))}
              <AddonSelect
                rowName={tr(item.name)}
                prompt={ui("gear.addProgram")}
                tr={tr}
                options={(catalog.programs || []).filter(
                  (prog) =>
                    prog.program_host === "cyberdecks" &&
                    prog.source === "SR5" &&
                    !(d.programs || []).some(
                      (row) => row.parent_id === item.id && row.gear_id === prog.id,
                    ),
                )}
                onAdd={(prog) =>
                  patch({
                    programs: [
                      ...(ch.programs || []),
                      {
                        gear_id: prog.id,
                        rating: Math.max(1, prog.minrating || 1),
                        parent_id: item.id,
                      },
                    ],
                  })
                }
              />
              <AppRows
                hostId={item.id}
                hostName={item.name}
                catalog={catalog}
                character={ch}
                d={d}
                tr={tr}
                ui={ui}
                patch={patch}
              />
              <MatrixModRows
                hostId={item.id}
                hostName={tr(item.name)}
                catalog={catalog}
                character={ch}
                d={d}
                tr={tr}
                ui={ui}
                patch={patch}
              />
            </div>
            <button
              className="btn danger"
              onClick={() =>
                patch({
                  cyberdecks: (ch.cyberdecks || []).filter((row) => row.id !== item.id),
                  programs: (ch.programs || []).filter((row) => row.parent_id !== item.id),
                  apps: (ch.apps || []).filter((row) => row.parent_id !== item.id),
                  gear: dropTree(ch.gear || [], item.id),
                })
              }
            >
              {ui("common.delete")}
            </button>
          </div>
        ))}
      </>

      <CatalogPicker
        items={catalog.cyberdecks || []}
        label={ui("gear.searchCyberdeck")}
        tr={tr}
        describe={(item) => (
          <>
            {item.name} / DR {item.devicerating}
            {item.attributearray ? ` / ${item.attributearray}` : ""}
            {ui("gear.programCount", { count: item.programs ?? "" })} / {item.cost}¥ /{" "}
            {item.avail || "-"} / {item.source}
          </>
        )}
        onAdd={(item) =>
          patch({
            cyberdecks: [
              ...(ch.cyberdecks || []),
              { gear_id: item.id, rating: Math.max(1, item.minrating || 1) },
            ],
          })
        }
      />
    </>
  );
}
