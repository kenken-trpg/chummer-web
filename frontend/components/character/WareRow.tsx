"use client";

import type { InstalledWare, SkillPickSlot, WareCatalogItem, WareInstall } from "@/lib/types";
import { SIDE_JA } from "@/lib/character/constants";
import { availBit } from "@/lib/character/format";
import { wareBounds } from "@/lib/character/ware";
import { SkillPickSelects } from "@/components/character/SkillPickSelects";

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
}) {
  const { item, childrenItems, catalogItems, grades, kind, tr, slotValue, wareRanges, onSlotChange, onPatchRow, onRemove, onAddChild, pickSlots, onSkillPick, nested } = props;
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
  const ratingMin = item.rating_min ?? spec?.minrating ?? 1;
  const ratingMax = item.rating_max ?? spec?.maxrating ?? 1;
  return (
    <div className={`cyber-item${nested ? " nested" : ""}`}>
      <div>
        <b>{tr(item.name)}{item.side ? `（${SIDE_JA[item.side] || item.side}）` : ""}{item.included ? "（同梱）" : ""}</b>
        <div className="muted">
          {item.name} / {item.category} / ESS −{item.essence} / {item.nuyen.toLocaleString()}¥{availBit(item)} / {item.source}
          {capMax > 0 ? <span className="cap"> ・ 容量 {item.capacity_used ?? 0}/{capMax}</span> : null}
          {item.limb_str != null ? <span className="cap"> ・ 肢 STR {item.limb_str} / AGI {item.limb_agi}</span> : null}
        </div>
        <div className="cyber-controls">
          {spec?.selectside && !item.parent_id && !item.included ? (
            <label>
              左右
              <select value={item.side || "Left"} onChange={(e) => onPatchRow(item.id, { side: e.target.value })}>
                <option value="Left">左</option>
                <option value="Right">右</option>
              </select>
            </label>
          ) : null}
          {spec && ratingMax > ratingMin && !item.included ? (
            <label>
              レーティング
              <input
                type="number"
                min={ratingMin}
                max={ratingMax}
                value={item.rating}
                onChange={(e) => onPatchRow(item.id, { rating: Number(e.target.value) })}
              />
            </label>
          ) : null}
          {!item.included && !spec?.forcegrade ? (
            <label>
              グレード
              <select value={item.grade} onChange={(e) => onPatchRow(item.id, { grade: e.target.value })}>
                {rowGrades.map((g) => (
                  <option key={g.name} value={g.name}>{g.name} (ESS×{g.ess} / ¥×{g.cost})</option>
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
              ワイヤレス
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
                    {tr(w.name)} / {w.capacity ? `[${w.capacity}]` : w.category}{showRange ? ` R${range.min}-${range.max}` : ""}
                  </option>
                );
              })}
            </select>
            <button className="btn primary" disabled={!chosen} onClick={() => chosen && onAddChild(chosen)}>スロットに追加</button>
          </div>
        ) : null}
      </div>
      {item.included ? <span className="muted">同梱</span> : <button className="btn danger" onClick={() => onRemove(item.id)}>削除</button>}
    </div>
  );
}
