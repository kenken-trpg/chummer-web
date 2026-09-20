"use client";
import { PickerList } from "@/components/character/CatalogPicker";
import { filterByBooks, useAllowedBooks } from "@/lib/character/books";
import type { TabPanelProps } from "@/components/character/types";
import { DRUG_CATS, isDrugCategory } from "@/lib/character/constants";
import { renderNotices } from "@/lib/engine-notices";

/** The catalog half of the misc / drugs panel: the category tabs, the search
 *  box, and the list you buy from.
 *
 *  Two lists rather than one because the two modes browse differently — misc
 *  gear lists whatever the settings' books allow, drugs narrow to the Drugs
 *  and BTL chips you actually browse and leave the toxin-and-chemical tail to
 *  the search box. */
export function MiscGearPicker({
  catalog,
  character: ch,
  tr,
  ui,
  patch,
  mode,
  gearSearch,
  setGearSearch,
  gearCat,
  setGearCat,
  extraPick,
  setExtraPick,
}: Pick<TabPanelProps, "catalog" | "character" | "tr" | "ui" | "patch"> & {
  mode: "misc" | "drugs";
  gearSearch: string;
  setGearSearch: (next: string) => void;
  gearCat: string;
  setGearCat: (next: string) => void;
  extraPick: Record<string, string>;
  setExtraPick: (next: (cur: Record<string, string>) => Record<string, string>) => void;
}) {
  // The chips are built from the same set the list draws from, so a chip can
  // never select an empty list.
  const allowedGear = filterByBooks(useAllowedBooks(), catalog.gear || []);
  return (
    <>
      <div className="option-row">
        <button
          className={`tab ${gearCat === "all" ? "active" : ""}`}
          onClick={() => setGearCat("all")}
        >
          {ui("common.all")}
        </button>
        {(mode === "drugs"
          ? [...DRUG_CATS]
          : [
              ...new Set(
                allowedGear
                  .filter((item) => !item.requireparent && !isDrugCategory(item))
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
            items={(catalog.gear || [])
              .filter((item) => !item.requireparent)
              .filter((item) => !isDrugCategory(item))
              .filter((item) => gearCat === "all" || item.category === gearCat)
              .filter((item) => {
                const q = gearSearch.trim().toLowerCase();
                if (q)
                  return (
                    item.name.toLowerCase().includes(q) ||
                    tr(item.name).toLowerCase().includes(q) ||
                    item.category.toLowerCase().includes(q)
                  );
                // no second book test: `<PickerList>` applies the settings'
                // own, and this one hid the books they enabled
                return true;
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
              .filter((item) => isDrugCategory(item) && !item.requireparent)
              .filter((item) => gearCat === "all" || item.category === gearCat)
              .filter((item) => {
                const q = gearSearch.trim().toLowerCase();
                if (q)
                  return (
                    item.name.toLowerCase().includes(q) ||
                    tr(item.name).toLowerCase().includes(q) ||
                    item.category.toLowerCase().includes(q)
                  );
                // Toxins and chemicals are a long tail you search for; the
                // twelve drugs-proper and the twelve chips are the list you
                // browse, so they show without a search even though CF is not
                // the core book.
                return (
                  item.source === "SR5" || item.category === "Drugs" || item.category === "BTLs"
                );
              })}
          >
            {(item) => (
              <div className="quality-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name} / {tr(item.category)} / {item.cost}¥ / {item.avail || "-"} /{" "}
                    {item.source}
                    {item.effect?.length ? (
                      <>
                        <br />
                        {ui("gear.effect")}: {renderNotices(item.effect, ui, tr)}
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
