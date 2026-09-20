"use client";
import { AppRows } from "@/components/character/tabs/gear/AppRows";
import { AddonSelect } from "@/components/character/AddonSelect";
import { CatalogPicker } from "@/components/character/CatalogPicker";
import { DiscountToggle } from "@/components/character/DiscountToggle";
import { MatrixModRows } from "@/components/character/tabs/gear/MatrixModRows";
import type { TabPanelProps } from "@/components/character/types";
import { alreadySlotted, dropTree } from "@/lib/character/gear";
import { HelpTip } from "@/components/help/HelpTip";

export function CommlinkGear({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  return (
    <>
      <>
        {(d.commlinks || []).map((item) => (
          <div className="cyber-item" key={item.id}>
            <div>
              <b>{tr(item.name)}</b>
              <div className="muted">
                <HelpTip
                  label={ui("help.open", { label: tr(item.name) })}
                  lines={[
                    { label: ui("help.matrix.deviceRating") },
                    ...(item.attack ? [{ label: ui("help.matrix.attack") }] : []),
                    ...(item.sleaze ? [{ label: ui("help.matrix.sleaze") }] : []),
                    { label: ui("help.matrix.dataprocessing") },
                    { label: ui("help.matrix.firewall") },
                  ]}
                >
                  {ui("help.matrix.statsLabel")}
                </HelpTip>{" "}
                {item.name}
                {item.category && item.category !== "Commlinks" ? ` / ${tr(item.category)}` : ""}
                {" / "}DR {item.device_rating}
                {item.attack ? ` / A ${item.attack}` : ""}
                {item.sleaze ? ` / S ${item.sleaze}` : ""} / DP {item.dataprocessing} / FW{" "}
                {item.firewall} / {item.nuyen.toLocaleString()}¥ / {item.source}
              </div>
              <div className="cyber-controls">
                <DiscountToggle list="commlinks" id={item.id} ch={ch} d={d} ui={ui} patch={patch} />
              </div>
              <div className="cyber-controls">
                {item.rating_max > 0 ? (
                  <label title={ui("common.ratingHint")}>
                    {ui("common.rating")}
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
                ) : null}
                <label title={ui("common.qtyHint")}>
                  {ui("common.qty")}
                  <input
                    type="number"
                    min={1}
                    max={999}
                    value={item.qty ?? 1}
                    onChange={(e) =>
                      patch({
                        commlinks: (ch.commlinks || []).map((row) =>
                          row.id === item.id
                            ? { ...row, qty: Math.max(1, Number(e.target.value) || 1) }
                            : row,
                        ),
                      })
                    }
                  />
                </label>
              </div>
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
              {(d.gear || [])
                .filter(
                  (acc) => acc.parent_id === item.id && acc.category !== "Electronic Modification",
                )
                .map((acc) => (
                  <div className="muted" key={acc.id} style={{ marginTop: 6 }}>
                    {tr(acc.label || acc.name)}
                    {acc.included
                      ? ` / ${ui("common.included")}`
                      : ` / ${acc.nuyen.toLocaleString()}¥`}{" "}
                    <button
                      className="btn danger"
                      onClick={() =>
                        patch({
                          gear: dropTree(ch.gear || [], acc.id),
                        })
                      }
                    >
                      {ui("common.remove")}
                    </button>
                  </div>
                ))}
              <AddonSelect
                rowName={tr(item.name)}
                prompt={ui("gear.addAccessory")}
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
                    !alreadySlotted(
                      mod,
                      (d.gear || []).filter((row) => row.parent_id === item.id),
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
                  commlinks: (ch.commlinks || []).filter((row) => row.id !== item.id),
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
        items={catalog.commlinks || []}
        label={ui("gear.searchCommlink")}
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
