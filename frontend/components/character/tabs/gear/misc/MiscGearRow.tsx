"use client";
import { HelpTip } from "@/components/help/HelpTip";
import { DiscountToggle } from "@/components/character/DiscountToggle";
import { PriceField } from "@/components/character/tabs/gear/PriceField";
import type { TabPanelProps } from "@/components/character/types";
import { isBookEnabled, useAllowedBooks } from "@/lib/character/books";
import { dropTree, miscFits } from "@/lib/character/gear";
import type { InstalledGear } from "@/lib/types";
import { renderNotices } from "@/lib/engine-notices";

/** One top-level piece of gear (or one drug) the character owns, with what is
 *  slotted into it and the controls that change it.
 *
 *  `slotPick` / `extraPick` are the panel's own state, shared by every row, so
 *  they come down as props rather than being held here. */
export function MiscGearRow({
  item,
  catalog,
  character: ch,
  d,
  tr,
  ui,
  patch,
  slotPick,
  setSlotPick,
  extraPick,
  setExtraPick,
  mode,
  gearSearch,
}: Pick<TabPanelProps, "catalog" | "character" | "d" | "tr" | "ui" | "patch"> & {
  item: InstalledGear;
  mode: "misc" | "drugs";
  /** what is typed in the search box below: while it has text, the "slot
   *  something in" list widens past the core book, the way the catalog list
   *  does */
  gearSearch: string;
  slotPick: Record<string, string>;
  setSlotPick: (next: (cur: Record<string, string>) => Record<string, string>) => void;
  extraPick: Record<string, string>;
  setExtraPick: (next: (cur: Record<string, string>) => Record<string, string>) => void;
}) {
  const allowedBooks = useAllowedBooks();
  const childrenItems = (d.gear || []).filter((child) => child.parent_id === item.id);
  const addons = (catalog.gear || []).filter(
    (mod) => Boolean(mod.requireparent) && miscFits(item, mod),
  );
  const addonSpec = (catalog.gear || []).find((mod) => mod.id === (slotPick[item.id] || ""));
  return (
    <div className="cyber-item" key={item.id}>
      <div>
        <b>{tr(item.label || item.name)}</b>
        <div className="muted">
          <HelpTip
            label={ui("help.open", { label: tr(item.label || item.name) })}
            lines={[
              { label: ui("help.gear.rating") },
              { label: ui("help.gear.capacity") },
              { label: ui("help.gear.qty") },
            ]}
          >
            {ui("help.gear.statsLabel")}
          </HelpTip>{" "}
          {item.name} / {tr(item.category)}
          {item.qty > 1 ? ` ×${item.qty}` : ""}
          {item.granted_by ? ` / ${ui("gear.granted", { source: tr(item.granted_by) })}` : ""}
          {item.add_weapon ? ` / ${ui("gear.weaponized")}` : ""}
          {item.capacity_max
            ? ` / ${ui("common.capacity")} ${item.capacity_used}/${item.capacity_max}`
            : ""}
          {" / "}
          {item.nuyen.toLocaleString()}¥ / {item.source}
        </div>
        {/* a quality's gift was not bought: no price to discount */}
        <div className="cyber-controls" hidden={Boolean(item.granted_by)}>
          <DiscountToggle list="gear" id={item.id} ch={ch} d={d} ui={ui} patch={patch} />
        </div>
        <div className="cyber-controls" hidden={Boolean(item.granted_by)}>
          {item.category === "Custom" ? (
            <label>
              {ui("gear.customName")}
              <input
                value={item.custom_name || ""}
                placeholder={tr(item.name)}
                onChange={(e) =>
                  patch({
                    gear: (ch.gear || []).map((row) =>
                      row.id === item.id ? { ...row, name: e.target.value || null } : row,
                    ),
                  })
                }
              />
            </label>
          ) : null}
          <PriceField
            range={item.cost_range}
            value={
              (ch.gear || []).find((row) => row.id === item.id)?.cost ?? item.cost_range?.[0] ?? 0
            }
            label={tr(item.label || item.name)}
            ui={ui}
            onChange={(cost) =>
              patch({
                gear: (ch.gear || []).map((row) => (row.id === item.id ? { ...row, cost } : row)),
              })
            }
          />
          <label title={ui("common.qtyHint")}>
            {ui("common.qty")}
            <input
              type="number"
              min={1}
              max={999}
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
            <label title={ui("common.ratingHint")}>
              {ui("common.rating")}
              <input
                type="number"
                min={1}
                max={item.rating_max}
                value={item.rating}
                onChange={(e) =>
                  patch({
                    gear: (ch.gear || []).map((row) =>
                      row.id === item.id ? { ...row, rating: Number(e.target.value) } : row,
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
                    row.id === item.id ? { ...row, extra: e.target.value || undefined } : row,
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
                      row.id === item.id ? { ...row, extra: e.target.value || undefined } : row,
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
        {item.is_drug && item.drug_effect?.length ? (
          <>
            <div className="muted" style={{ marginTop: 4 }}>
              {ui("gear.effect")}: {renderNotices(item.drug_effect, ui, tr)}
              {item.drug_vectors?.length
                ? ` ／ ${ui("gear.vector")} ${item.drug_vectors.join("・")}`
                : ""}
              {item.drug_speed ? ` ／ ${ui("gear.onset")} ${item.drug_speed}` : ""}
            </div>
            <div className="cyber-controls" style={{ marginTop: 4 }}>
              <label title={ui("gear.drugToggleHint")}>
                <input
                  type="checkbox"
                  checked={Boolean((ch.gear || []).find((row) => row.id === item.id)?.active)}
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
            {child.included ? ` / ${ui("common.included")}` : ` / ${child.nuyen.toLocaleString()}¥`}
            {child.capacity_cost ? ` / ${ui("common.capacity")} ${child.capacity_cost}` : ""}
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
              <label title={ui("common.ratingHint")}>
                {ui("common.rating")}
                <input
                  type="number"
                  min={1}
                  max={child.rating_max}
                  value={child.rating}
                  onChange={(e) =>
                    patch({
                      gear: (ch.gear || []).map((row) =>
                        row.id === child.id ? { ...row, rating: Number(e.target.value) } : row,
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
              onChange={(e) => setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
            >
              <option value="">
                {mode === "drugs" ? ui("gear.gradeOrAddon") : ui("gear.addGear")}
              </option>
              {addons
                .filter((mod) => !childrenItems.some((child) => child.gear_id === mod.id))
                // Drug grades are not a book: they are how the one drug in
                // this row is cut, so they are always on offer.
                .filter(
                  (mod) =>
                    mod.category === "Drug Grades" || isBookEnabled(allowedBooks, mod.source),
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
                  onChange={(e) => setExtraPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
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
                    onChange={(e) => setExtraPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
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
      {item.granted_by ? null : (
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
      )}
    </div>
  );
}
