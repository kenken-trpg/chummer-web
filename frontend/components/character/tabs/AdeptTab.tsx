"use client";

import { CORE_ONLY, PickerList } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";

import { useMemo, useState } from "react";
import { ExtraSelect, selectLabel } from "@/components/character/ExtraSelect";
import { MentorPicker } from "@/components/character/MentorPicker";
import { attrLabel } from "@/lib/ui-strings";
import { formatPoints } from "@/lib/character/format";

export function AdeptTab({
  catalog,
  character: ch,
  d,
  tr,
  t,
  ui,
  patch,
  setCharacter,
}: TabPanelProps) {
  const [powerSearch, setPowerSearch] = useState("");
  const [enhSearch, setEnhSearch] = useState("");
  const [qiSearch, setQiSearch] = useState("");

  const matchedPowers = useMemo(() => {
    const q = powerSearch.trim().toLowerCase();
    return (catalog.powers || []).filter((item) =>
      !q
        ? item.source === "SR5"
        : item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q),
    );
  }, [catalog, powerSearch, tr]);

  return (
    <div className="card">
      <p className="muted">
        {ui("adept.powerPoints", {
          used: formatPoints(d.power_points?.used || 0),
          max: formatPoints(d.power_points?.max || 0),
        })}
        {(d.way_discount?.max || 0) > 0
          ? ui("adept.wayDiscount", {
              used: formatPoints(d.way_discount?.used || 0),
              max: formatPoints(d.way_discount?.max || 0),
            })
          : ""}
      </p>
      {d.needs_mentor ? (
        <MentorPicker catalog={catalog} mentor={d.mentor} ch={ch} tr={tr} onPatch={patch} />
      ) : null}
      {ch.talent === "Mystic Adept" ? (
        <div className="skill-row">
          <span>{ui("adept.boughtPoints")}</span>
          <input
            type="range"
            min={0}
            max={d.totals.MAG || 0}
            value={ch.mystic_pp || 0}
            onChange={(e) => setCharacter({ ...ch, mystic_pp: Number(e.target.value) })}
            onMouseUp={(e) => patch({ mystic_pp: Number((e.target as HTMLInputElement).value) })}
            onBlur={(e) => patch({ mystic_pp: Number(e.target.value) })}
          />
          <b>{ch.mystic_pp || 0}</b>
        </div>
      ) : null}
      {(d.adept_powers || []).map((item) => (
        <div className="cyber-item" key={item.id}>
          <div>
            <b>{tr(item.name)}</b>
            <div className="muted">
              {item.name}
              {item.extra
                ? `（${item.select === "attribute" ? attrLabel(item.extra, t) : tr(item.extra)}）`
                : ""}
              {" / "}
              {formatPoints(item.cost)} PP
              {item.discounted && item.full_cost != null
                ? ui("adept.beforeDiscount", { cost: formatPoints(item.full_cost) })
                : ""}
              {item.free_levels ? ui("adept.freeLevels", { levels: item.free_levels }) : ""}
              {item.total_rating && item.total_rating !== item.rating
                ? ui("adept.totalRating", { rating: item.total_rating })
                : ""}
              {" / "}
              {item.source}
              {item.notes?.length ? ` / ${item.notes.join(" ・ ")}` : ""}
              {item.spell
                ? ui("adept.spellLine", {
                    dv: item.spell.dv,
                    force: item.spell.force,
                    drain:
                      item.spell.drain == null
                        ? ui("adept.drainSpecial")
                        : `${item.spell.drain}${item.spell.drain_code || ""}`,
                    resistAttrs: item.spell.resist_attrs,
                    resist: item.spell.resist,
                  })
                : ""}
            </div>
            <div className="cyber-controls">
              {!item.free_only && item.rating_max > item.rating_min ? (
                <label>
                  {ui("adept.rating")}
                  <input
                    type="number"
                    min={item.rating_min}
                    max={item.rating_max}
                    value={item.rating}
                    onChange={(e) =>
                      patch({
                        adept_powers: (ch.adept_powers || []).map((row) =>
                          row.id === item.id ? { ...row, rating: Number(e.target.value) } : row,
                        ),
                      })
                    }
                  />
                </label>
              ) : null}
              {!item.free_only ? (
                <ExtraSelect
                  item={item}
                  tr={tr}
                  t={t}
                  onChange={(extra) =>
                    patch({
                      adept_powers: (ch.adept_powers || []).map((row) =>
                        row.id === item.id ? { ...row, extra } : row,
                      ),
                    })
                  }
                />
              ) : null}
              {item.spell ? (
                <label>
                  Force
                  <input
                    type="number"
                    min={item.spell.force_min}
                    max={item.spell.force_max}
                    value={item.spell.force}
                    onChange={(e) =>
                      patch({
                        adept_powers: (ch.adept_powers || []).map((row) =>
                          row.id === item.id ? { ...row, force: Number(e.target.value) } : row,
                        ),
                      })
                    }
                  />
                </label>
              ) : null}
              {item.can_discount ? (
                <label>
                  <input
                    type="checkbox"
                    checked={!!item.discounted}
                    onChange={(e) =>
                      patch({
                        adept_powers: (ch.adept_powers || []).map((row) =>
                          row.id === item.id ? { ...row, discounted: e.target.checked } : row,
                        ),
                      })
                    }
                  />
                  {ui("adept.wayDiscountToggle")}
                </label>
              ) : null}
            </div>
          </div>
          {item.free_only ? (
            <span className="muted">{ui("adept.free")}</span>
          ) : (
            <button
              className="btn danger"
              onClick={() =>
                patch({
                  adept_powers: (ch.adept_powers || []).filter((row) => row.id !== item.id),
                })
              }
            >
              {ui("common.delete")}
            </button>
          )}
        </div>
      ))}
      <div className="cyber-toolbar" style={{ gridTemplateColumns: "1fr" }}>
        <input
          type="search"
          placeholder={ui("adept.searchPowers")}
          aria-label={ui("adept.searchPowers")}
          value={powerSearch}
          onChange={(e) => setPowerSearch(e.target.value)}
        />
      </div>
      <div className="quality-list">
        <PickerList
          items={matchedPowers}
          limit={80}
          note={powerSearch.trim() ? undefined : CORE_ONLY}
        >
          {(item) => (
            <div className="quality-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / {formatPoints(item.points)} PP
                  {item.extrapointcost ? ` +${formatPoints(item.extrapointcost)}` : ""}
                  {item.adeptway
                    ? ui("adept.wayLabel", { points: formatPoints(item.adeptway) })
                    : ""}
                  {item.levels ? ui("adept.hasLevels") : ""}
                  {item.select === "spell" ? ui("adept.spellSelect") : ""}
                  {" / "}
                  {item.source}
                </div>
              </div>
              <button
                className="btn primary"
                onClick={() =>
                  patch({
                    adept_powers: [
                      ...(ch.adept_powers || []),
                      { power_id: item.id, rating: 1, discounted: !!item.adeptway },
                    ],
                  })
                }
              >
                {ui("common.add")}
              </button>
            </div>
          )}
        </PickerList>
      </div>
      <h3>Enhancement</h3>
      <p className="muted">{ui("adept.enhancementNote")}</p>
      {(d.enhancements || []).map((item) => (
        <div className="cyber-item" key={item.id}>
          <div>
            <b>{tr(item.name)}</b>
            <div className="muted">
              {item.name}
              {item.power ? ` / ${item.power}` : ""}
              {ui("adept.enhancementCost")}
              {item.source}
            </div>
          </div>
          <button
            className="btn danger"
            onClick={() =>
              patch({
                adept_enhancements: (ch.adept_enhancements || []).filter((id) => id !== item.id),
              })
            }
          >
            {ui("common.delete")}
          </button>
        </div>
      ))}
      <input
        type="search"
        placeholder={ui("adept.searchEnhancements")}
        aria-label={ui("adept.searchEnhancements")}
        value={enhSearch}
        onChange={(e) => setEnhSearch(e.target.value)}
      />
      <div className="quality-list">
        {(catalog.enhancements || [])
          .filter((item) => {
            const q = enhSearch.trim().toLowerCase();
            return (
              !q || item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q)
            );
          })
          .filter((item) => !(ch.adept_enhancements || []).includes(item.id))
          .map((item) => (
            <div className="quality-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name}
                  {item.power ? ` / ${item.power}` : ""}
                  {item.required?.quality?.length ? ` / ${item.required.quality.join(" ・ ")}` : ""}
                  {ui("adept.enhancementCost")}
                  {item.source}
                </div>
              </div>
              <button
                className="btn primary"
                onClick={() =>
                  patch({
                    adept_enhancements: [...(ch.adept_enhancements || []), item.id],
                  })
                }
              >
                {ui("common.add")}
              </button>
            </div>
          ))}
      </div>
      <h3>{ui("adept.qiTitle")}</h3>
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
                Force
                <input
                  type="number"
                  min={item.rating_min}
                  max={item.rating_max}
                  value={item.rating}
                  onChange={(e) =>
                    patch({
                      qi_foci: (ch.qi_foci || []).map((row) =>
                        row.id === item.id ? { ...row, rating: Number(e.target.value) } : row,
                      ),
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
                        qi_foci: (ch.qi_foci || []).map((row) =>
                          row.id === item.id
                            ? { ...row, power_rating: Number(e.target.value) }
                            : row,
                        ),
                      })
                    }
                  />
                </label>
              ) : null}
              {item.select ? (
                <label>
                  {selectLabel(item.select)}
                  <select
                    value={item.extra || ""}
                    onChange={(e) =>
                      patch({
                        qi_foci: (ch.qi_foci || []).map((row) =>
                          row.id === item.id ? { ...row, extra: e.target.value } : row,
                        ),
                      })
                    }
                  >
                    <option value="">{ui("common.choose")}</option>
                    {item.options.map((name) => (
                      <option key={name} value={name}>
                        {item.select === "attribute" ? attrLabel(name, t) : tr(name)}
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
            return q
              ? item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q)
              : item.source === "SR5";
          })}
          note={qiSearch.trim() ? undefined : CORE_ONLY}
        >
          {(item) => (
            <div className="quality-item" key={`qi-${item.id}`}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / Force {Math.max(1, Math.ceil((item.points || 0) / 0.25))}〜 /{" "}
                  {item.source}
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
    </div>
  );
}
