"use client";
import { HelpTip } from "@/components/help/HelpTip";
import { DiscountToggle } from "@/components/character/DiscountToggle";
import { PriceField } from "@/components/character/tabs/gear/PriceField";
import type { TabPanelProps } from "@/components/character/types";
import { trAs } from "@/lib/ui-strings";
import { dropTree, catalogExtraOptions } from "@/lib/character/gear";
import { editRow } from "@/lib/character/rows";
import { GearAddonPicker } from "@/components/character/tabs/gear/misc/GearAddonPicker";
import { GearChild } from "@/components/character/tabs/gear/misc/GearChild";
import type { InstalledGear } from "@/lib/types";
import { renderNotices } from "@/lib/engine-notices";
import { sourceBit } from "@/lib/character/format";

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
}: Pick<TabPanelProps, "catalog" | "character" | "d" | "tr" | "ui" | "patch"> & {
  item: InstalledGear;
  mode: "misc" | "drugs";
  slotPick: Record<string, string>;
  setSlotPick: (next: (cur: Record<string, string>) => Record<string, string>) => void;
  extraPick: Record<string, string>;
  setExtraPick: (next: (cur: Record<string, string>) => Record<string, string>) => void;
}) {
  const protectedPurchase = (item.parts_used_units || 0) > 0;
  const gearOptions = (id: string) => catalogExtraOptions(catalog.gear, id);
  const childrenItems = (d.gear || []).filter((child) => child.parent_id === item.id);
  // Anything else the character carries can hold this one — a Spare Clip, a
  // Medkit, a briefcase. Only the rows that are top level themselves are
  // offered, so the arrangement stays a tree.
  const containers = (d.gear || []).filter(
    (row) => !row.parent_id && row.id !== item.id && !row.granted_by,
  );
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
          {item.nuyen.toLocaleString()}¥ / {sourceBit(item, ui)}
        </div>
        {item.parts_remaining_units != null ? (
          <p>
            {ui("gear.partsRemaining", {
              remaining: item.parts_remaining_units / 4,
              purchased: (item.parts_purchased_units || 0) / 4,
              used: (item.parts_used_units || 0) / 4,
              reserved: (item.parts_reserved_units || 0) / 4,
            })}
          </p>
        ) : null}
        {protectedPurchase ? <p>{ui("gear.partsProtected")}</p> : null}
        {/* a quality's gift was not bought: no price to discount */}
        <div className="cyber-controls" hidden={Boolean(item.granted_by) || protectedPurchase}>
          <DiscountToggle list="gear" id={item.id} ch={ch} d={d} ui={ui} patch={patch} />
        </div>
        <div className="cyber-controls" hidden={Boolean(item.granted_by) || protectedPurchase}>
          {item.category === "Custom" ? (
            <label>
              {ui("gear.customName")}
              <input
                value={item.custom_name || ""}
                placeholder={tr(item.name)}
                onChange={(e) =>
                  patch({ gear: editRow(ch.gear, item.id, { name: e.target.value || null }) })
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
            onChange={(cost) => patch({ gear: editRow(ch.gear, item.id, { cost }) })}
          />
          <label title={ui("common.qtyHint")}>
            {ui("common.qty")}
            <input
              type="number"
              min={1}
              max={999}
              value={item.purchased_qty ?? item.qty}
              onChange={(e) =>
                patch({ gear: editRow(ch.gear, item.id, { qty: Number(e.target.value) }) })
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
                  patch({ gear: editRow(ch.gear, item.id, { rating: Number(e.target.value) }) })
                }
              />
            </label>
          ) : null}
          {item.needs_extra && item.extra_kind === "skill" ? (
            <select
              aria-label={`${tr(item.name)}: ${ui("common.skill")}`}
              value={item.extra || ""}
              onChange={(e) =>
                patch({ gear: editRow(ch.gear, item.id, { extra: e.target.value || undefined }) })
              }
            >
              <option value="">{ui("common.skill")}</option>
              {gearOptions(item.gear_id).map((name) => (
                <option key={name} value={name}>
                  {trAs(tr, item.extra_skill_kind, name)}
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
                  patch({ gear: editRow(ch.gear, item.id, { extra: e.target.value || undefined }) })
                }
              />
              <datalist id={`gear-extra-${item.id}`}>
                {gearOptions(item.gear_id)
                  .slice(0, 80)
                  .map((name) => (
                    <option key={name} value={name} />
                  ))}
              </datalist>
            </>
          ) : null}
        </div>
        {item.is_drug && item.drug_effect?.length ? (
          <>
            <div className="muted" style={{ marginTop: 4 }}>
              <HelpTip
                label={ui("help.open", { label: ui("gear.effect") })}
                lines={[
                  { label: ui("help.drug.effect") },
                  { label: ui("help.drug.vector") },
                  { label: ui("help.drug.onset") },
                ]}
              >
                {ui("help.drug.statsLabel")}
              </HelpTip>{" "}
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
                    patch({ gear: editRow(ch.gear, item.id, { active: e.target.checked }) })
                  }
                />
                {ui("gear.inUse")}
              </label>
            </div>
          </>
        ) : null}
        {childrenItems.map((child) => (
          <GearChild
            key={child.id}
            child={child}
            all={d.gear || []}
            ch={ch}
            tr={tr}
            ui={ui}
            patch={patch}
          />
        ))}
        {containers.length && !item.granted_by ? (
          <div className="cyber-controls">
            <label title={ui("gear.putIntoHint")}>
              {ui("gear.putInto")}
              <select
                aria-label={`${tr(item.label || item.name)}: ${ui("gear.putInto")}`}
                value=""
                onChange={(e) => {
                  const into = e.target.value;
                  if (!into) return;
                  patch({ gear: editRow(ch.gear, item.id, { parent_id: into }) });
                }}
              >
                <option value="">{ui("gear.putInto")}</option>
                {containers.map((row) => (
                  <option key={row.id} value={row.id}>
                    {tr(row.label || row.name)}
                  </option>
                ))}
              </select>
            </label>
          </div>
        ) : null}
        <GearAddonPicker
          item={item}
          catalog={catalog}
          character={ch}
          tr={tr}
          ui={ui}
          patch={patch}
          childrenItems={childrenItems}
          slotPick={slotPick}
          setSlotPick={setSlotPick}
          extraPick={extraPick}
          setExtraPick={setExtraPick}
          mode={mode}
        />
      </div>
      {item.granted_by || protectedPurchase ? null : (
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
