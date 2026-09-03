"use client";
import type { TabPanelProps } from "@/components/character/types";
import { useMemo, useState } from "react";
import { WareRow } from "@/components/character/WareRow";
import { limbQualityLine } from "@/lib/character/format";
import { dropRemovedWarePicks } from "@/lib/character/quality";
import {
  hideFromWareCatalog,
  nextFreeSide,
  removeWareTree,
  wareBounds,
} from "@/lib/character/ware";

export function CyberTab({ catalog, character: ch, d, tr, patch }: TabPanelProps) {
  const [cySearch, setCySearch] = useState("");
  const [cyCat, setCyCat] = useState("all");
  const [addGrade, setAddGrade] = useState("Standard");
  const [slotPick, setSlotPick] = useState<Record<string, string>>({});
  const cyberCats = useMemo(
    () =>
      [
        ...new Set(
          catalog.cyberware.items
            .filter((w) => !hideFromWareCatalog(w, "cyberware"))
            .map((w) => w.category),
        ),
      ].sort(),
    [catalog],
  );
  const cyberGrades = useMemo(() => {
    const banned = new Set(d.disabled_cyberware_grades || []);
    return catalog.cyberware.grades.filter((g) => !banned.has(g.name));
  }, [catalog, d.disabled_cyberware_grades]);
  const effectiveAddGrade = cyberGrades.some((g) => g.name === addGrade)
    ? addGrade
    : cyberGrades[0]?.name || "Betaware";
  const filteredCyber = useMemo(() => {
    const q = cySearch.trim().toLowerCase();
    return catalog.cyberware.items
      .filter((w) => !hideFromWareCatalog(w, "cyberware"))
      .filter((w) => cyCat === "all" || w.category === cyCat)
      .filter((w) => !q || w.name.toLowerCase().includes(q) || tr(w.name).includes(cySearch))
      .slice(0, 80);
  }, [catalog, cySearch, cyCat, tr]);
  const disabledCoreGrades = (d.disabled_cyberware_grades || []).filter((g) =>
    catalog.cyberware.grades.some((row) => row.name === g),
  );

  return (
    <div className="card">
      <p className="muted">
        装着中 {d.cyberware?.length || 0} ・ Essence {d.essence}（サイバー −
        {d.essence_lost_cyber ?? 0}） ・ 消費 {(d.nuyen_spent ?? 0).toLocaleString()}¥
      </p>
      {disabledCoreGrades.length > 0 ? (
        <p className="muted">使用不可グレード: {disabledCoreGrades.join("、")}</p>
      ) : null}
      {d.limb_replace ? (
        <p className="muted">
          本体 STR {d.limb_replace.str} / AGI {d.limb_replace.agi}
          （リム平均 {d.limb_replace.count}/{d.limb_replace.parts} ・ 肉 STR{" "}
          {d.limb_replace.meat_str} / AGI {d.limb_replace.meat_agi}）
        </p>
      ) : null}
      {d.limb_quality ? <p className="muted">{limbQualityLine(d.limb_quality)}</p> : null}
      <div className="option-row">
        <span>Redliner に含める</span>
        <label>
          <input
            type="checkbox"
            checked={Boolean(ch.options?.redliner_torso)}
            onChange={(e) =>
              patch({
                options: {
                  redliner_torso: e.target.checked,
                  redliner_skull: Boolean(ch.options?.redliner_skull),
                },
              })
            }
          />
          胴
        </label>
        <label>
          <input
            type="checkbox"
            checked={Boolean(ch.options?.redliner_skull)}
            onChange={(e) =>
              patch({
                options: {
                  redliner_torso: Boolean(ch.options?.redliner_torso),
                  redliner_skull: e.target.checked,
                },
              })
            }
          />
          頭蓋
        </label>
      </div>
      {(d.cyberware || [])
        .filter((item) => !item.parent_id)
        .map((item) => (
          <WareRow
            key={item.id}
            item={item}
            childrenItems={(d.cyberware || []).filter((child) => child.parent_id === item.id)}
            catalogItems={catalog.cyberware.items}
            grades={cyberGrades}
            kind="cyberware"
            tr={tr}
            slotValue={slotPick[item.id] || ""}
            wareRanges={d.ware_ranges}
            pickSlots={(d.skill_pick_slots || []).filter(
              (slot) => slot.source_kind === "cyberware",
            )}
            onSkillPick={(key, skill) =>
              patch({ skill_picks: { ...(ch.skill_picks || {}), [key]: skill } })
            }
            onSlotChange={(wareId) => setSlotPick((cur) => ({ ...cur, [item.id]: wareId }))}
            onPatchRow={(id, next) =>
              patch({
                cyberware: (ch.cyberware || []).map((row) => {
                  if (row.id === id) return { ...row, ...next };
                  if (next.side && row.parent_id === id) return { ...row, side: next.side };
                  return row;
                }),
              })
            }
            onRemove={(id) => {
              const keptIds = new Set(removeWareTree(ch.cyberware || [], id).map((row) => row.id));
              const cyberware = removeWareTree(ch.cyberware || [], id);
              patch({
                cyberware,
                weapon_accessories: (ch.weapon_accessories || []).filter(
                  (row) => !row.parent_id || keptIds.has(row.parent_id),
                ),
                gear: (ch.gear || []).filter((row) => !row.parent_id || keptIds.has(row.parent_id)),
                skill_picks: dropRemovedWarePicks(ch.skill_picks, [
                  ...cyberware,
                  ...(ch.bioware || []),
                ]),
              });
            }}
            onAddChild={(wareId) => {
              const spec = catalog.cyberware.items.find((w) => w.id === wareId);
              if (!spec) return;
              const range = wareBounds(spec, d.ware_ranges);
              patch({
                cyberware: [
                  ...(ch.cyberware || []),
                  {
                    ware_id: spec.id,
                    rating: range.min,
                    grade: item.grade,
                    wireless: true,
                    parent_id: item.id,
                  },
                ],
              });
            }}
          />
        ))}
      <div className="cyber-toolbar">
        <input
          type="search"
          placeholder="サイバーウェアを検索"
          aria-label="サイバーウェアを検索"
          value={cySearch}
          onChange={(e) => setCySearch(e.target.value)}
        />
        <select value={cyCat} onChange={(e) => setCyCat(e.target.value)}>
          <option value="all">すべての分類</option>
          {cyberCats.map((c) => (
            <option key={c} value={c}>
              {tr(c)}
            </option>
          ))}
        </select>
        <select value={effectiveAddGrade} onChange={(e) => setAddGrade(e.target.value)}>
          {cyberGrades.map((g) => (
            <option key={g.name} value={g.name}>
              追加時 {g.name}
            </option>
          ))}
        </select>
      </div>
      <div className="quality-list">
        {filteredCyber.map((w) => (
          <div className="quality-item" key={w.id}>
            <div>
              <b>{tr(w.name)}</b>
              <div className="muted">
                {w.name} / {w.category} / ESS {w.ess}
                {w.plugin ? "（単独時）" : ""} / {w.cost}¥ / {w.source}
                {w.maxrating > 1 ? ` / 最大R${w.maxrating}` : ""}
                {w.plugin ? " / スロット可" : ""}
              </div>
            </div>
            <button
              className="btn primary"
              onClick={() =>
                patch({
                  cyberware: [
                    ...(ch.cyberware || []),
                    {
                      ware_id: w.id,
                      rating: w.minrating || 1,
                      grade: effectiveAddGrade,
                      wireless: true,
                      side: nextFreeSide(ch.cyberware || [], catalog.cyberware.items, w),
                    },
                  ],
                })
              }
            >
              追加
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
