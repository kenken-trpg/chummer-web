"use client";
import { ExtraSelect, optionLabel } from "@/components/character/ExtraSelect";
import type { TabPanelProps } from "@/components/character/types";
import { formatPoints, sourceBit } from "@/lib/character/format";
import { editRow } from "@/lib/character/rows";
import { renderNotice } from "@/lib/engine-notices";
import type { InstalledAdeptPower } from "@/lib/types";

/** One adept power the character has, with its rating, choice, Force and
 *  Way discount, and the button that drops it. */
export function AdeptPowerRow({
  item,
  character: ch,
  tr,
  t,
  ui,
  patch,
}: Pick<TabPanelProps, "character" | "tr" | "t" | "ui" | "patch"> & { item: InstalledAdeptPower }) {
  return (
    <div className="cyber-item">
      <div>
        <b>{tr(item.name)}</b>
        <div className="muted">
          {item.name}
          {item.extra ? `（${optionLabel(item.extra, item.select, tr, t, ui)}）` : ""}
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
          {sourceBit(item, ui)}
          {item.notes?.length
            ? ` / ${item.notes.map((n) => renderNotice(n, ui, tr)).join(" ・ ")}`
            : ""}
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
                    adept_powers: editRow(ch.adept_powers, item.id, {
                      rating: Number(e.target.value),
                    }),
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
                patch({ adept_powers: editRow(ch.adept_powers, item.id, { extra }) })
              }
            />
          ) : null}
          {item.spell ? (
            <label title={ui("common.forceHint")}>
              {ui("common.force")}
              <input
                type="number"
                min={item.spell.force_min}
                max={item.spell.force_max}
                value={item.spell.force}
                onChange={(e) =>
                  patch({
                    adept_powers: editRow(ch.adept_powers, item.id, {
                      force: Number(e.target.value),
                    }),
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
                    adept_powers: editRow(ch.adept_powers, item.id, {
                      discounted: e.target.checked,
                    }),
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
  );
}
