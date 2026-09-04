"use client";
import { CORE_ONLY, PickerList } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { useState } from "react";
import { optionalNumber, testLine } from "@/lib/character/format";

export function FociTab({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  const [focusSearch, setFocusSearch] = useState("");

  return (
    <div className="card">
      <p className="muted">
        {ui("foci.note", {
          count: d.focus_limits?.count || 0,
          countMax: d.focus_limits?.count_max || 0,
          force: d.focus_limits?.force || 0,
          forceMax: d.focus_limits?.force_max || 0,
        })}
        {d.enabled_tabs.includes("adept") ? ui("foci.adeptNote") : ""}
      </p>
      {(d.foci || []).map((item) => (
        <div className="cyber-item" key={item.id}>
          <div>
            <b>{tr(item.name)}</b>
            <div className="muted">
              {item.name} / F{item.force} / {item.crafted ? ui("foci.crafted") : ui("common.buy")} /{" "}
              {item.nuyen.toLocaleString()}¥ / {ui("foci.bind", { karma: item.karma })}
              {item.crafted
                ? ui("foci.craftBreakdown", {
                    formula: item.formula_nuyen?.toLocaleString() || 0,
                    reagent: item.reagent_nuyen?.toLocaleString() || 0,
                    retail: item.retail_nuyen?.toLocaleString() || 0,
                  })
                : ""}
              {item.effect ? ` / ${item.effect.replace(/Rating/g, String(item.force))}` : ""}
              {item.needs_weapon
                ? item.weapon_name
                  ? ui("foci.target", {
                      name: tr(item.weapon_name),
                      dice: item.weapon_dice || item.force,
                    })
                  : ui("foci.needsWeapon")
                : ""}
              {" / "}
              {item.source}
            </div>
            {item.formula_test ? (
              <div className="muted">
                {ui("foci.formulaTest", { test: testLine(item.formula_test, ui) })}
              </div>
            ) : null}
            {item.test ? <div className="muted">{testLine(item.test, ui)}</div> : null}
            <div className="cyber-controls">
              <label>
                Force
                <input
                  type="number"
                  min={1}
                  max={item.force_max}
                  value={item.force}
                  onChange={(e) =>
                    patch({
                      foci: (ch.foci || []).map((row) =>
                        row.id === item.id ? { ...row, force: Number(e.target.value) } : row,
                      ),
                    })
                  }
                />
              </label>
              {item.needs_weapon ? (
                <label>
                  {ui("foci.weaponLabel")}
                  <select
                    value={item.weapon_id || ""}
                    onChange={(e) =>
                      patch({
                        foci: (ch.foci || []).map((row) =>
                          row.id === item.id ? { ...row, extra: e.target.value || null } : row,
                        ),
                      })
                    }
                  >
                    <option value="">
                      {item.weapon_type === "Melee" ? ui("foci.melee") : ui("foci.weapon")}
                    </option>
                    {(item.weapon_options || []).map((opt) => (
                      <option key={opt.id} value={opt.id}>
                        {tr(opt.name)}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}
              {item.crafted ? (
                <>
                  <label>
                    {ui("foci.craftHits")}
                    <input
                      type="number"
                      min={0}
                      value={item.hits ?? ""}
                      onChange={(e) =>
                        patch({
                          foci: (ch.foci || []).map((row) =>
                            row.id === item.id
                              ? { ...row, hits: optionalNumber(e.target.value) }
                              : row,
                          ),
                        })
                      }
                    />
                  </label>
                  <label>
                    {ui("foci.resistHits")}
                    <input
                      type="number"
                      min={0}
                      value={item.opposed_hits ?? ""}
                      onChange={(e) =>
                        patch({
                          foci: (ch.foci || []).map((row) =>
                            row.id === item.id
                              ? { ...row, opposed_hits: optionalNumber(e.target.value) }
                              : row,
                          ),
                        })
                      }
                    />
                  </label>
                  <label>
                    {ui("foci.formula")}
                    <select
                      value={item.formula_bought ? "buy" : "design"}
                      onChange={(e) =>
                        patch({
                          foci: (ch.foci || []).map((row) =>
                            row.id === item.id
                              ? { ...row, formula_bought: e.target.value === "buy" }
                              : row,
                          ),
                        })
                      }
                    >
                      <option value="buy">{ui("common.buy")}</option>
                      <option value="design">{ui("foci.formulaDesign")}</option>
                    </select>
                  </label>
                </>
              ) : null}
            </div>
          </div>
          <button
            className="btn danger"
            onClick={() =>
              patch({
                foci: (ch.foci || []).filter((row) => row.id !== item.id),
              })
            }
          >
            {ui("common.delete")}
          </button>
        </div>
      ))}
      <input
        type="search"
        placeholder={ui("foci.search")}
        aria-label={ui("foci.search")}
        value={focusSearch}
        onChange={(e) => setFocusSearch(e.target.value)}
      />
      <div className="quality-list">
        <PickerList
          items={(catalog.foci || []).filter((item) => {
            const q = focusSearch.trim().toLowerCase();
            if (q) {
              return (
                item.name.toLowerCase().includes(q) ||
                tr(item.name).toLowerCase().includes(q) ||
                (item.effect || "").toLowerCase().includes(q)
              );
            }
            return item.source === "SR5";
          })}
          note={focusSearch.trim() ? undefined : CORE_ONLY}
        >
          {(item) => (
            <div className="quality-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / {ui("foci.buyCost", { cost: item.cost ?? "" })}
                  {item.formula ? ui("foci.craftCost", { cost: item.formula.cost ?? "" }) : ""}
                  {" / "}
                  {item.effect || ui("foci.bindOnly")}
                  {item.needs_weapon
                    ? ui("foci.weaponRequired", { type: item.weapon_type || "Melee" })
                    : ""}
                  {" / "}
                  {item.source}
                </div>
              </div>
              <div>
                <button
                  className="btn"
                  onClick={() =>
                    patch({
                      foci: [...(ch.foci || []), { gear_id: item.id, force: 1, crafted: false }],
                    })
                  }
                >
                  {ui("common.buy")}
                </button>{" "}
                <button
                  className="btn primary"
                  onClick={() =>
                    patch({
                      foci: [
                        ...(ch.foci || []),
                        { gear_id: item.id, force: 1, crafted: true, formula_bought: true },
                      ],
                    })
                  }
                >
                  {ui("foci.crafted")}
                </button>
              </div>
            </div>
          )}
        </PickerList>
      </div>
    </div>
  );
}
