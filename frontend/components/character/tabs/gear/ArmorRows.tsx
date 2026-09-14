"use client";
import type { TabPanelProps } from "@/components/character/types";
import { availBit, limitModifierLine, specialArmorLine } from "@/lib/character/format";
import type { InstalledArmorMod, InstalledGear } from "@/lib/types";

type RowProps = Pick<TabPanelProps, "character" | "tr" | "ui" | "patch">;

/** One mod on a piece of armor: price, capacity, what it adds, and its own
 * controls (remove, rating, the piece a Custom Fit (Stack) is tailored to,
 * wireless). A mod that came with the piece is only listed. */
export function ArmorModRow({
  mod,
  stackOptions,
  character: ch,
  tr,
  ui,
  patch,
}: RowProps & { mod: InstalledArmorMod; /** pieces it may stack with */ stackOptions: string[] }) {
  return (
    <div className="muted" style={{ marginTop: 6 }}>
      {tr(mod.name)}
      {mod.rating_max > 1 ? ` R${mod.rating}` : ""}
      {mod.included ? ` / ${ui("common.included")}` : ` / ${mod.nuyen.toLocaleString()}¥`}
      {mod.capacity_cost
        ? ui("gear.capacityCost", {
            cost: mod.capacity_cost < 0 ? `+${-mod.capacity_cost}` : mod.capacity_cost,
          })
        : ""}
      {specialArmorLine(mod.special_armor, ui)
        ? ` / ${specialArmorLine(mod.special_armor, ui)}`
        : ""}
      {limitModifierLine(mod.limit_modifiers, ui)
        ? ` / ${limitModifierLine(mod.limit_modifiers, ui)}`
        : ""}
      {availBit(mod, ui)}
      {mod.included ? null : (
        <>
          {" "}
          <button
            className="btn danger"
            onClick={() =>
              patch({
                armor_mods: (ch.armor_mods || []).filter((row) => row.id !== mod.id),
              })
            }
          >
            {ui("common.remove")}
          </button>
        </>
      )}
      {mod.rating_max > 1 && !mod.included ? (
        <label>
          Rating
          <input
            type="number"
            min={1}
            max={mod.rating_max}
            value={mod.rating}
            onChange={(e) =>
              patch({
                armor_mods: (ch.armor_mods || []).map((row) =>
                  row.id === mod.id ? { ...row, rating: Number(e.target.value) } : row,
                ),
              })
            }
          />
        </label>
      ) : null}
      {mod.select_armor ? (
        <label title={ui("gear.stackWithHint")}>
          {" "}
          {ui("gear.stackWith")}{" "}
          <select
            aria-label={ui("gear.stackWith")}
            value={mod.stack_with || ""}
            onChange={(e) =>
              patch({
                armor_mods: (ch.armor_mods || []).map((row) =>
                  row.id === mod.id ? { ...row, stack_with: e.target.value } : row,
                ),
              })
            }
          >
            <option value="">—</option>
            {stackOptions.map((name) => (
              <option key={name} value={name}>
                {tr(name)}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      {mod.has_wireless ? (
        <label title={ui("common.wirelessHint")}>
          {" "}
          <input
            type="checkbox"
            checked={mod.wireless ?? true}
            onChange={(e) =>
              patch({
                armor_mods: (ch.armor_mods || []).map((row) =>
                  row.id === mod.id ? { ...row, wireless: e.target.checked } : row,
                ),
              })
            }
          />
          WL
        </label>
      ) : null}
    </div>
  );
}

/** One piece of gear carried in armor (a Holster, a Medkit): what it takes
 * of the armor's capacity, and remove / rating. */
export function CarriedGearRow({
  gear,
  character: ch,
  tr,
  ui,
  patch,
}: RowProps & { gear: InstalledGear }) {
  return (
    <div className="muted" style={{ marginTop: 6 }}>
      {tr(gear.name)}
      {gear.rating_max > 1 ? ` R${gear.rating}` : ""}
      {gear.qty > 1 ? ` ×${gear.qty}` : ""}
      {gear.included ? ` / ${ui("common.included")}` : ` / ${gear.nuyen.toLocaleString()}¥`}
      {gear.armor_capacity ? ui("gear.capacityCost", { cost: gear.armor_capacity }) : ""}
      {availBit(gear, ui)}
      {gear.included ? null : (
        <>
          {" "}
          <button
            className="btn danger"
            onClick={() =>
              patch({
                gear: (ch.gear || []).filter(
                  (row) => row.id !== gear.id && row.parent_id !== gear.id,
                ),
              })
            }
          >
            {ui("common.remove")}
          </button>
        </>
      )}
      {gear.rating_max > 1 && !gear.included ? (
        <label>
          Rating
          <input
            type="number"
            min={1}
            max={gear.rating_max}
            value={gear.rating}
            onChange={(e) =>
              patch({
                gear: (ch.gear || []).map((row) =>
                  row.id === gear.id ? { ...row, rating: Number(e.target.value) } : row,
                ),
              })
            }
          />
        </label>
      ) : null}
    </div>
  );
}
