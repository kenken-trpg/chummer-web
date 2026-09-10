"use client";

import type { InstalledWare, SkillPickSlot, WareCatalogItem, WareInstall } from "@/lib/types";
import { sideLabel } from "@/lib/character/constants";
import { availBit } from "@/lib/character/format";
import { wareBounds } from "@/lib/character/ware";
import { SkillPickSelects } from "@/components/character/SkillPickSelects";
import { useUiText } from "@/lib/i18n";

export function WareRow(props: {
  item: InstalledWare;
  childrenItems: InstalledWare[];
  catalogItems: WareCatalogItem[];
  grades: { name: string; ess: number; cost: number }[];
  kind: "cyberware" | "bioware";
  tr: (name: string) => string;
  slotValue: string;
  wareRanges?: Record<string, { min: number; max: number }>;
  onSlotChange: (wareId: string) => void;
  onPatchRow: (id: string, next: Partial<WareInstall>) => void;
  onRemove: (id: string) => void;
  onAddChild: (wareId: string) => void;
  pickSlots?: SkillPickSlot[];
  onSkillPick?: (key: string, skill: string) => void;
  nested?: boolean;
  /** Name only: no stat line, no controls, no slot picker — the row keeps
   *  its plug-ins (as names) and its delete button. */
  compact?: boolean;
}) {
  const {
    item,
    childrenItems,
    catalogItems,
    grades,
    kind,
    tr,
    slotValue,
    wareRanges,
    onSlotChange,
    onPatchRow,
    onRemove,
    onAddChild,
    pickSlots,
    onSkillPick,
    nested,
    compact,
  } = props;
  const { ui } = useUiText();
  const spec = catalogItems.find((w) => w.id === item.ware_id);
  const slots = (spec?.allow_subsystems || []).filter(Boolean);
  const slotOptions = catalogItems.filter((w) => {
    if (w.id === item.ware_id) return false;
    if ((w.required?.[kind] || []).includes(item.name)) return true;
    return slots.includes(w.category) && Boolean(w.plugin || w.requireparent);
  });
  const rowGrades = grades.filter((g) => !(spec?.bannedgrades || []).includes(g.name));
  const chosen = slotValue || slotOptions[0]?.id || "";
  const capMax = item.capacity_max || 0;
  // Bundled with a parent, or handed over by a quality (`<addware>`): either
  // way there is nothing here for the player to change or remove.
  const locked = Boolean(item.included || item.granted_by);
  const ratingMin = item.rating_min ?? spec?.minrating ?? 1;
  const ratingMax = item.rating_max ?? spec?.maxrating ?? 1;
  const title = (
    <b>
      {tr(item.name)}
      {compact && item.rating > 1 ? ` R${item.rating}` : ""}
      {item.side ? `（${sideLabel(item.side, ui)}）` : ""}
      {item.included ? ui("ware.bundledSuffix") : ""}
      {item.granted_by ? ui("ware.grantedSuffix", { source: tr(item.granted_by) }) : ""}
    </b>
  );
  const removeControl = locked ? (
    <span className="muted">{ui("common.bundled")}</span>
  ) : (
    <button className="btn danger" onClick={() => onRemove(item.id)}>
      {ui("common.delete")}
    </button>
  );
  if (compact) {
    // The folded row hides the selects, so say when one still wants an answer
    // — an unpicked skill is a bonus the engine is silently not applying.
    const pending =
      (pickSlots || []).some((slot) => slot.source_id === item.id && !slot.picked) ||
      Boolean(item.select_ware && !locked && !item.extra);
    return (
      <div className={`cyber-item compact${nested ? " nested" : ""}`}>
        <div>
          {title}
          {pending ? <span className="warn"> {ui("ware.pending")}</span> : null}
          {childrenItems.map((child) => (
            <WareRow
              key={child.id}
              {...props}
              item={child}
              childrenItems={[]}
              slotValue=""
              onSlotChange={() => undefined}
              onAddChild={() => undefined}
              nested
            />
          ))}
        </div>
        {/* the name already says （同梱）／（…付与） on a locked row */}
        {locked ? null : removeControl}
      </div>
    );
  }
  return (
    <div className={`cyber-item${nested ? " nested" : ""}`}>
      <div>
        {title}
        <div className="muted">
          {item.name} / {tr(item.category)} / ESS −{item.essence} / {item.nuyen.toLocaleString()}¥
          {availBit(item, ui)} / {item.source}
          {capMax > 0 ? (
            <span className="cap">
              {ui("ware.capacityInline", { used: item.capacity_used ?? 0, max: capMax })}
            </span>
          ) : null}
          {item.limb_str != null ? (
            <span className="cap">
              {ui("ware.limb", { str: item.limb_str, agi: item.limb_agi ?? 0 })}
              {(item.limb_armor ?? 0) > 0
                ? ui("ware.limbArmor", { armor: item.limb_armor ?? 0 })
                : ""}
            </span>
          ) : null}
        </div>
        <div className="cyber-controls">
          {spec?.selectside && !item.parent_id && !locked ? (
            <label>
              {ui("ware.side")}
              <select
                value={item.side || "Left"}
                onChange={(e) => onPatchRow(item.id, { side: e.target.value })}
              >
                <option value="Left">{ui("common.left")}</option>
                <option value="Right">{ui("common.right")}</option>
              </select>
            </label>
          ) : null}
          {item.select_ware && !locked ? (
            <label>
              {ui("ware.target")}
              <select
                value={item.extra || ""}
                onChange={(e) => onPatchRow(item.id, { extra: e.target.value })}
              >
                <option value="">{ui("common.choose")}</option>
                {catalogItems
                  .filter(
                    (w) => !item.select_ware_category || w.category === item.select_ware_category,
                  )
                  .map((w) => (
                    <option key={w.id} value={w.name}>
                      {tr(w.name)}
                    </option>
                  ))}
              </select>
            </label>
          ) : null}
          {spec && ratingMax > ratingMin && !locked ? (
            <label>
              {ui("common.rating")}
              <input
                type="number"
                min={ratingMin}
                max={ratingMax}
                value={item.rating}
                onChange={(e) => onPatchRow(item.id, { rating: Number(e.target.value) })}
              />
            </label>
          ) : null}
          {!locked && !spec?.forcegrade ? (
            <label>
              {ui("common.grade")}
              <select
                value={item.grade}
                onChange={(e) => onPatchRow(item.id, { grade: e.target.value })}
              >
                {rowGrades.map((g) => (
                  <option key={g.name} value={g.name}>
                    {g.name} (ESS×{g.ess} / ¥×{g.cost})
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          {spec?.has_wireless ? (
            <label>
              <input
                type="checkbox"
                checked={item.wireless}
                onChange={(e) => onPatchRow(item.id, { wireless: e.target.checked })}
              />
              {ui("common.wireless")}
            </label>
          ) : null}
        </div>
        {onSkillPick ? (
          <SkillPickSelects
            slots={(pickSlots || []).filter((slot) => slot.source_id === item.id)}
            tr={tr}
            onPick={onSkillPick}
          />
        ) : null}
        {childrenItems.map((child) => (
          <WareRow
            key={child.id}
            item={child}
            childrenItems={[]}
            catalogItems={catalogItems}
            grades={grades}
            kind={kind}
            tr={tr}
            slotValue=""
            wareRanges={wareRanges}
            onSlotChange={() => undefined}
            onPatchRow={onPatchRow}
            onRemove={onRemove}
            onAddChild={() => undefined}
            pickSlots={pickSlots}
            onSkillPick={onSkillPick}
            nested
          />
        ))}
        {slotOptions.length > 0 ? (
          <div className="slot-picker">
            <select value={chosen} onChange={(e) => onSlotChange(e.target.value)}>
              {slotOptions.map((w) => {
                const range = wareBounds(w, wareRanges);
                const showRange = range.max > range.min || range.max > 1;
                return (
                  <option key={w.id} value={w.id}>
                    {tr(w.name)} / {w.capacity ? `[${w.capacity}]` : tr(w.category)}
                    {showRange ? ` R${range.min}-${range.max}` : ""}
                  </option>
                );
              })}
            </select>
            <button
              className="btn primary"
              disabled={!chosen}
              onClick={() => chosen && onAddChild(chosen)}
            >
              {ui("gear.addToSlot")}
            </button>
          </div>
        ) : null}
      </div>
      {removeControl}
    </div>
  );
}
