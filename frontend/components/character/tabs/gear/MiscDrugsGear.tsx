"use client";
import { useState } from "react";
import { CORE_ONLY, PickerList } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { dropTree, miscFits } from "@/lib/character/gear";

export function MiscDrugsGear({
  catalog,
  character: ch,
  d,
  tr,
  ui,
  patch,
  mode,
}: TabPanelProps & { mode: "misc" | "drugs" }) {
  const [gearSearch, setGearSearch] = useState("");
  const [gearCat, setGearCat] = useState("all");
  const [slotPick, setSlotPick] = useState<Record<string, string>>({});
  const [extraPick, setExtraPick] = useState<Record<string, string>>({});

  return (
    <>
      <>
        {(d.gear || [])
          .filter((item) => {
            if (item.parent_id) return false;
            const drugCat =
              item.category === "Drugs" ||
              item.category === "Toxins" ||
              item.category === "Chemicals";
            return mode === "drugs" ? drugCat : !drugCat;
          })
          .map((item) => {
            const childrenItems = (d.gear || []).filter((child) => child.parent_id === item.id);
            const addons = (catalog.gear || []).filter(
              (mod) => Boolean(mod.requireparent) && miscFits(item, mod),
            );
            const addonSpec = (catalog.gear || []).find(
              (mod) => mod.id === (slotPick[item.id] || ""),
            );
            return (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>{tr(item.label || item.name)}</b>
                  <div className="muted">
                    {item.name} / {tr(item.category)}
                    {item.qty > 1 ? ` ×${item.qty}` : ""}
                    {item.add_weapon ? ` / ${ui("gear.weaponized")}` : ""}
                    {item.capacity_max
                      ? ` / ${ui("common.capacity")} ${item.capacity_used}/${item.capacity_max}`
                      : ""}
                    {" / "}
                    {item.nuyen.toLocaleString()}¥ / {item.source}
                  </div>
                  <div className="cyber-controls">
                    <label>
                      {ui("common.qty")}
                      <input
                        type="number"
                        min={1}
                        max={99}
                        value={item.qty}
                        onChange={(e) =>
                          patch({
                            gear: (ch.gear || []).map((row) =>
                              row.id === item.id ? { ...row, qty: Number(e.target.value) } : row,
                            ),
                          })
                        }
                      />
                    </label>
                    {item.rating_max > 0 ? (
                      <label>
                        Rating
                        <input
                          type="number"
                          min={1}
                          max={item.rating_max}
                          value={item.rating}
                          onChange={(e) =>
                            patch({
                              gear: (ch.gear || []).map((row) =>
                                row.id === item.id
                                  ? { ...row, rating: Number(e.target.value) }
                                  : row,
                              ),
                            })
                          }
                        />
                      </label>
                    ) : null}
                    {item.needs_extra && item.extra_kind === "skill" ? (
                      <select
                        aria-label={`${tr(item.name)}: ${ui("common.skill")}`}
                        value={item.extra || ""}
                        onChange={(e) =>
                          patch({
                            gear: (ch.gear || []).map((row) =>
                              row.id === item.id
                                ? { ...row, extra: e.target.value || undefined }
                                : row,
                            ),
                          })
                        }
                      >
                        <option value="">{ui("common.skill")}</option>
                        {(item.extra_options || []).map((name) => (
                          <option key={name} value={name}>
                            {tr(name)}
                          </option>
                        ))}
                      </select>
                    ) : null}
                    {item.needs_extra && item.extra_kind === "text" ? (
                      <>
                        <input
                          list={`gear-extra-${item.id}`}
                          placeholder={ui("common.target")}
                          value={item.extra || ""}
                          onChange={(e) =>
                            patch({
                              gear: (ch.gear || []).map((row) =>
                                row.id === item.id
                                  ? { ...row, extra: e.target.value || undefined }
                                  : row,
                              ),
                            })
                          }
                        />
                        <datalist id={`gear-extra-${item.id}`}>
                          {(item.extra_options || []).slice(0, 80).map((name) => (
                            <option key={name} value={name} />
                          ))}
                        </datalist>
                      </>
                    ) : null}
                  </div>
                  {item.is_drug && item.drug_effect ? (
                    <>
                      <div className="muted" style={{ marginTop: 4 }}>
                        {ui("gear.effect")}: {item.drug_effect}
                        {item.drug_vectors?.length
                          ? ` ／ ${ui("gear.vector")} ${item.drug_vectors.join("・")}`
                          : ""}
                        {item.drug_speed ? ` ／ ${ui("gear.onset")} ${item.drug_speed}` : ""}
                      </div>
                      <div className="cyber-controls" style={{ marginTop: 4 }}>
                        <label title={ui("gear.drugToggleHint")}>
                          <input
                            type="checkbox"
                            checked={Boolean(
                              (ch.gear || []).find((row) => row.id === item.id)?.active,
                            )}
                            onChange={(e) =>
                              patch({
                                gear: (ch.gear || []).map((row) =>
                                  row.id === item.id ? { ...row, active: e.target.checked } : row,
                                ),
                              })
                            }
                          />
                          {ui("gear.inUse")}
                        </label>
                      </div>
                    </>
                  ) : null}
                  {childrenItems.map((child) => (
                    <div className="muted" key={child.id} style={{ marginTop: 6 }}>
                      {tr(child.label || child.name)}
                      {child.rating_max > 0 ? ` R${child.rating}` : ""}
                      {child.qty > 1 ? ` ×${child.qty}` : ""}
                      {child.included
                        ? ` / ${ui("common.included")}`
                        : ` / ${child.nuyen.toLocaleString()}¥`}
                      {child.capacity_cost
                        ? ` / ${ui("common.capacity")} ${child.capacity_cost}`
                        : ""}
                      {child.included ? null : (
                        <>
                          {" "}
                          <button
                            className="btn danger"
                            onClick={() =>
                              patch({
                                gear: dropTree(ch.gear || [], child.id),
                              })
                            }
                          >
                            {ui("common.remove")}
                          </button>
                        </>
                      )}
                      {child.rating_max > 0 && !child.included ? (
                        <label>
                          Rating
                          <input
                            type="number"
                            min={1}
                            max={child.rating_max}
                            value={child.rating}
                            onChange={(e) =>
                              patch({
                                gear: (ch.gear || []).map((row) =>
                                  row.id === child.id
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
                  {addons.length ? (
                    <div className="cyber-controls">
                      <select
                        aria-label={`${tr(item.name)}: ${mode === "drugs" ? ui("gear.gradeOrAddon") : ui("gear.addGear")}`}
                        value={slotPick[item.id] || ""}
                        onChange={(e) =>
                          setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))
                        }
                      >
                        <option value="">
                          {mode === "drugs" ? ui("gear.gradeOrAddon") : ui("gear.addGear")}
                        </option>
                        {addons
                          .filter((mod) => !childrenItems.some((child) => child.gear_id === mod.id))
                          .filter(
                            (mod) =>
                              gearSearch.trim() ||
                              mod.source === "SR5" ||
                              mod.category === "Drug Grades",
                          )
                          .map((mod) => (
                            <option key={mod.id} value={mod.id}>
                              {tr(mod.name)} ({mod.cost}¥)
                            </option>
                          ))}
                      </select>
                      {addonSpec?.extra_kind === "skill" || addonSpec?.extra_kind === "text" ? (
                        addonSpec.extra_kind === "skill" ? (
                          <select
                            aria-label={`${tr(item.name)}: ${ui("common.target")}`}
                            value={extraPick[item.id] || ""}
                            onChange={(e) =>
                              setExtraPick((cur) => ({ ...cur, [item.id]: e.target.value }))
                            }
                          >
                            <option value="">{ui("common.target")}</option>
                            {(addonSpec.extra_options || []).map((name) => (
                              <option key={name} value={name}>
                                {tr(name)}
                              </option>
                            ))}
                          </select>
                        ) : (
                          <>
                            <input
                              list={`gear-addon-extra-${item.id}`}
                              placeholder={ui("common.target")}
                              value={extraPick[item.id] || ""}
                              onChange={(e) =>
                                setExtraPick((cur) => ({ ...cur, [item.id]: e.target.value }))
                              }
                            />
                            <datalist id={`gear-addon-extra-${item.id}`}>
                              {(addonSpec.extra_options || []).slice(0, 80).map((name) => (
                                <option key={name} value={name} />
                              ))}
                            </datalist>
                          </>
                        )
                      ) : null}
                      <button
                        className="btn"
                        disabled={!slotPick[item.id]}
                        onClick={() => {
                          const wareId = slotPick[item.id];
                          const spec = addons.find((mod) => mod.id === wareId);
                          if (!spec) return;
                          patch({
                            gear: [
                              ...(ch.gear || []),
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
                        {ui("common.install")}
                      </button>
                    </div>
                  ) : null}
                </div>
                <button
                  className="btn danger"
                  onClick={() =>
                    patch({
                      gear: dropTree(ch.gear || [], item.id),
                    })
                  }
                >
                  {ui("common.delete")}
                </button>
              </div>
            );
          })}
      </>

      <div className="option-row">
        <button
          className={`tab ${gearCat === "all" ? "active" : ""}`}
          onClick={() => setGearCat("all")}
        >
          {ui("common.all")}
        </button>
        {(mode === "drugs"
          ? ["Drugs", "Toxins", "Chemicals"]
          : [
              ...new Set(
                (catalog.gear || [])
                  .filter((item) => {
                    if (item.requireparent) return false;
                    const drugCat =
                      item.category === "Drugs" ||
                      item.category === "Toxins" ||
                      item.category === "Chemicals";
                    if (drugCat) return false;
                    return gearSearch.trim() || item.source === "SR5";
                  })
                  .map((item) => item.category),
              ),
            ]
        )
          .sort()
          .map((cat) => (
            <button
              key={cat}
              className={`tab ${gearCat === cat ? "active" : ""}`}
              onClick={() => setGearCat(cat)}
            >
              {tr(cat)}
            </button>
          ))}
      </div>
      <input
        type="search"
        placeholder={mode === "drugs" ? ui("gear.searchDrugs") : ui("gear.searchMisc")}
        aria-label={mode === "drugs" ? ui("gear.searchDrugs") : ui("gear.searchMisc")}
        value={gearSearch}
        onChange={(e) => setGearSearch(e.target.value)}
      />
      <div className="quality-list">
        {mode === "misc" && (
          <PickerList
            note={gearSearch.trim() ? undefined : CORE_ONLY}
            items={(catalog.gear || [])
              .filter((item) => !item.requireparent)
              .filter((item) => {
                const drugCat =
                  item.category === "Drugs" ||
                  item.category === "Toxins" ||
                  item.category === "Chemicals";
                return !drugCat;
              })
              .filter((item) => gearCat === "all" || item.category === gearCat)
              .filter((item) => {
                const q = gearSearch.trim().toLowerCase();
                if (q)
                  return (
                    item.name.toLowerCase().includes(q) ||
                    tr(item.name).toLowerCase().includes(q) ||
                    item.category.toLowerCase().includes(q)
                  );
                return item.source === "SR5";
              })}
          >
            {(item) => (
              <div className="quality-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name} / {tr(item.category)}
                    {item.maxrating > 0
                      ? ` / R${item.minrating || 1}-${item.maxrating}`
                      : ""} / {item.cost}¥ / {item.avail || "-"} / {item.source}
                  </div>
                  {item.needs_extra ? (
                    <div className="cyber-controls">
                      {item.extra_kind === "skill" ? (
                        <select
                          aria-label={`${tr(item.name)}: ${ui("common.skill")}`}
                          value={extraPick[`buy-${item.id}`] || ""}
                          onChange={(e) =>
                            setExtraPick((cur) => ({ ...cur, [`buy-${item.id}`]: e.target.value }))
                          }
                        >
                          <option value="">{ui("common.skill")}</option>
                          {(item.extra_options || []).map((name) => (
                            <option key={name} value={name}>
                              {tr(name)}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <>
                          <input
                            list={`buy-extra-${item.id}`}
                            placeholder={ui("common.target")}
                            value={extraPick[`buy-${item.id}`] || ""}
                            onChange={(e) =>
                              setExtraPick((cur) => ({
                                ...cur,
                                [`buy-${item.id}`]: e.target.value,
                              }))
                            }
                          />
                          <datalist id={`buy-extra-${item.id}`}>
                            {(item.extra_options || []).slice(0, 80).map((name) => (
                              <option key={name} value={name} />
                            ))}
                          </datalist>
                        </>
                      )}
                    </div>
                  ) : null}
                </div>
                <button
                  className="btn primary"
                  onClick={() => {
                    patch({
                      gear: [
                        ...(ch.gear || []),
                        {
                          gear_id: item.id,
                          rating: Math.max(1, item.minrating || 1),
                          extra: extraPick[`buy-${item.id}`] || undefined,
                        },
                      ],
                    });
                    setExtraPick((cur) => ({ ...cur, [`buy-${item.id}`]: "" }));
                  }}
                >
                  {ui("common.buy")}
                </button>
              </div>
            )}
          </PickerList>
        )}
        {mode === "drugs" && (
          <PickerList
            limit={200}
            note={gearSearch.trim() ? undefined : "gear.idleDrugs"}
            items={(catalog.drugs || catalog.gear || [])
              .filter((item) => {
                const drugCat =
                  item.category === "Drugs" ||
                  item.category === "Toxins" ||
                  item.category === "Chemicals";
                return drugCat && !item.requireparent;
              })
              .filter((item) => gearCat === "all" || item.category === gearCat)
              .filter((item) => {
                const q = gearSearch.trim().toLowerCase();
                if (q)
                  return (
                    item.name.toLowerCase().includes(q) ||
                    tr(item.name).toLowerCase().includes(q) ||
                    item.category.toLowerCase().includes(q)
                  );
                return item.source === "SR5" || item.category === "Drugs";
              })}
          >
            {(item) => (
              <div className="quality-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name} / {tr(item.category)} / {item.cost}¥ / {item.avail || "-"} /{" "}
                    {item.source}
                    {item.effect ? (
                      <>
                        <br />
                        {ui("gear.effect")}: {item.effect}
                      </>
                    ) : null}
                    {item.vectors?.length
                      ? ` ／ ${ui("gear.vector")} ${item.vectors.join("・")}`
                      : ""}
                  </div>
                </div>
                <button
                  className="btn primary"
                  onClick={() =>
                    patch({
                      gear: [...(ch.gear || []), { gear_id: item.id, rating: 1 }],
                    })
                  }
                >
                  {ui("common.buy")}
                </button>
              </div>
            )}
          </PickerList>
        )}
      </div>
    </>
  );
}
