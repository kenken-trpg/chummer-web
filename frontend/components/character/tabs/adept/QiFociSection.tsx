"use client";
import { useState } from "react";
import { PickerList } from "@/components/character/CatalogPicker";
import { optionLabel, selectLabel } from "@/components/character/ExtraSelect";
import type { TabPanelProps } from "@/components/character/types";
import { HelpTip } from "@/components/help/HelpTip";
import { sourceBit } from "@/lib/character/format";
import { editRow } from "@/lib/character/rows";

/** Qi foci: the ones bound, with their Force, power rating and choice, and a
 *  searchable list of the powers one can hold. */
export function QiFociSection({
  catalog,
  character: ch,
  d,
  tr,
  t,
  ui,
  patch,
}: Pick<TabPanelProps, "catalog" | "character" | "d" | "tr" | "t" | "ui" | "patch">) {
  const [qiSearch, setQiSearch] = useState("");
  return (
    <>
      <h3>
        <HelpTip
          label={ui("help.open", { label: ui("adept.qiTitle") })}
          lines={[
            { label: ui("help.adept.qiCost") },
            { label: ui("help.adept.qiBinding") },
            { label: ui("help.adept.qiPower") },
          ]}
        >
          {ui("adept.qiTitle")}
        </HelpTip>
      </h3>
      <p className="muted">{ui("adept.qiNote")}</p>
      {(d.qi_foci || []).map((item) => (
        <div className="cyber-item" key={item.id}>
          <div>
            <b>Qi Focus F{item.rating}</b>
            <div className="muted">
              {tr(item.name)}
              {item.extra ? `（${tr(item.extra)}）` : ""} / R{item.power_rating}
              {" / "}
              {item.nuyen.toLocaleString()}¥{ui("adept.qiBinding", { karma: item.karma })}
            </div>
            <div className="cyber-controls">
              <label>
                {ui("common.force")}
                <input
                  type="number"
                  min={item.rating_min}
                  max={item.rating_max}
                  value={item.rating}
                  onChange={(e) =>
                    patch({
                      qi_foci: editRow(ch.qi_foci, item.id, { rating: Number(e.target.value) }),
                    })
                  }
                />
              </label>
              {item.power_rating_max > 1 ? (
                <label>
                  {ui("adept.qiPowerRating")}
                  <input
                    type="number"
                    min={1}
                    max={item.power_rating_max}
                    value={item.power_rating}
                    onChange={(e) =>
                      patch({
                        qi_foci: editRow(ch.qi_foci, item.id, {
                          power_rating: Number(e.target.value),
                        }),
                      })
                    }
                  />
                </label>
              ) : null}
              {item.select ? (
                <label>
                  {ui(selectLabel(item.select))}
                  <select
                    value={item.extra || ""}
                    onChange={(e) =>
                      patch({ qi_foci: editRow(ch.qi_foci, item.id, { extra: e.target.value }) })
                    }
                  >
                    <option value="">{ui("common.choose")}</option>
                    {item.options.map((name) => (
                      <option key={name} value={name}>
                        {optionLabel(name, item.select, tr, t, ui)}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}
            </div>
          </div>
          <button
            className="btn danger"
            onClick={() =>
              patch({
                qi_foci: (ch.qi_foci || []).filter((row) => row.id !== item.id),
              })
            }
          >
            {ui("common.delete")}
          </button>
        </div>
      ))}
      <input
        type="search"
        placeholder={ui("adept.searchQi")}
        aria-label={ui("adept.searchQi")}
        value={qiSearch}
        onChange={(e) => setQiSearch(e.target.value)}
      />
      <div className="quality-list">
        <PickerList
          items={(catalog.powers || []).filter((item) => {
            const q = qiSearch.trim().toLowerCase();
            return (
              !q || item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q)
            );
          })}
        >
          {(item) => (
            <div className="quality-item" key={`qi-${item.id}`}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / {ui("common.force")}{" "}
                  {Math.max(1, Math.ceil((item.points || 0) / 0.25))}〜 / {sourceBit(item, ui)}
                </div>
              </div>
              <button
                className="btn primary"
                onClick={() =>
                  patch({
                    qi_foci: [
                      ...(ch.qi_foci || []),
                      {
                        power_id: item.id,
                        rating: Math.max(1, Math.ceil((item.points || 0) / 0.25)),
                        power_rating: 1,
                      },
                    ],
                  })
                }
              >
                {ui("adept.bind")}
              </button>
            </div>
          )}
        </PickerList>
      </div>
    </>
  );
}
