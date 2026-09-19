"use client";
import { CatalogPicker } from "@/components/character/CatalogPicker";
import { DiscountToggle } from "@/components/character/DiscountToggle";
import { AppRows } from "@/components/character/tabs/gear/AppRows";
import { AutosoftRows } from "@/components/character/tabs/gear/AutosoftRows";
import { LooseProgramRows } from "@/components/character/tabs/gear/LooseProgramRows";
import { MatrixModRows } from "@/components/character/tabs/gear/MatrixModRows";
import type { TabPanelProps } from "@/components/character/types";
import { dropTree } from "@/lib/character/gear";
import { HelpTip } from "@/components/help/HelpTip";

export function RccGear({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  return (
    <>
      <LooseProgramRows kind="rccs" character={ch} d={d} tr={tr} ui={ui} patch={patch} />
      <>
        {(d.rccs || []).map((item) => (
          <div className="cyber-item" key={item.id}>
            <div>
              <b>{tr(item.name)}</b>
              <div className="muted">
                <HelpTip
                  label={ui("help.open", { label: tr(item.name) })}
                  lines={[
                    { label: ui("help.matrix.deviceRating") },
                    { label: ui("help.matrix.dataprocessing") },
                    { label: ui("help.matrix.firewall") },
                  ]}
                >
                  {ui("help.matrix.statsLabel")}
                </HelpTip>{" "}
                {item.name} / DR {item.device_rating} / DP {item.dataprocessing} / FW{" "}
                {item.firewall}
                {ui("gear.programs", {
                  used: item.program_used ?? 0,
                  max: item.program_max ?? item.programs ?? 0,
                })}{" "}
                / {item.nuyen.toLocaleString()}¥ / {item.source}
              </div>
              <div className="cyber-controls">
                <DiscountToggle list="rccs" id={item.id} ch={ch} d={d} ui={ui} patch={patch} />
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
                          rccs: (ch.rccs || []).map((row) =>
                            row.id === item.id ? { ...row, rating: Number(e.target.value) } : row,
                          ),
                        })
                      }
                    />
                  </label>
                </div>
              ) : null}
              <AutosoftRows
                hostId={item.id}
                hostName={tr(item.name)}
                catalog={catalog}
                character={ch}
                d={d}
                tr={tr}
                ui={ui}
                patch={patch}
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
                  rccs: (ch.rccs || []).filter((row) => row.id !== item.id),
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
