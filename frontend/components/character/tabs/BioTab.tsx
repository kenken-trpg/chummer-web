"use client";
import type { TabPanelProps } from "@/components/character/types";
import { useMemo, useState } from "react";
import { WareRow } from "@/components/character/WareRow";
import { dropRemovedWarePicks } from "@/lib/character/quality";
import {
  hideFromWareCatalog,
  nextFreeSide,
  removeWareTree,
  wareBounds,
} from "@/lib/character/ware";

export function BioTab({ catalog, character: ch, d, tr, patch }: TabPanelProps) {
  const [bioSearch, setBioSearch] = useState("");
  const [bioCat, setBioCat] = useState("all");
  const [bioGrade, setBioGrade] = useState("Standard");
  const [slotPick, setSlotPick] = useState<Record<string, string>>({});
  const bioCats = useMemo(
    () =>
      [
        ...new Set(
          (catalog.bioware?.items || [])
            .filter((w) => !hideFromWareCatalog(w, "bioware"))
            .map((w) => w.category),
        ),
      ].sort(),
    [catalog],
  );
  const bioGrades = useMemo(() => {
    const banned = new Set(d.disabled_bioware_grades || []);
    return (catalog.bioware?.grades || []).filter((g) => !banned.has(g.name));
  }, [catalog, d.disabled_bioware_grades]);
  const effectiveBioGrade = bioGrades.some((g) => g.name === bioGrade)
    ? bioGrade
    : bioGrades[0]?.name || "Betaware";
  const filteredBio = useMemo(() => {
    const q = bioSearch.trim().toLowerCase();
    return (catalog.bioware?.items || [])
      .filter((w) => !hideFromWareCatalog(w, "bioware"))
      .filter((w) => bioCat === "all" || w.category === bioCat)
      .filter((w) => !q || w.name.toLowerCase().includes(q) || tr(w.name).includes(bioSearch))
      .slice(0, 80);
  }, [catalog, bioSearch, bioCat, tr]);
  const disabledCoreGrades = (d.disabled_bioware_grades || []).filter((g) =>
    (catalog.bioware?.grades || []).some((row) => row.name === g),
  );

  return (
    <div className="card">
      <p className="muted">
        装着中 {d.bioware?.length || 0} ・ Essence {d.essence}（バイオ −{d.essence_lost_bio ?? 0}）
        ・ 消費 {(d.nuyen_spent ?? 0).toLocaleString()}¥
      </p>
      {disabledCoreGrades.length > 0 ? (
        <p className="muted">使用不可グレード: {disabledCoreGrades.join("、")}</p>
      ) : null}
      {(d.bioware || [])
        .filter((item) => !item.parent_id)
        .map((item) => (
          <WareRow
            key={item.id}
            item={item}
            childrenItems={(d.bioware || []).filter((child) => child.parent_id === item.id)}
            catalogItems={catalog.bioware.items}
            grades={bioGrades}
            kind="bioware"
            tr={tr}
            slotValue={slotPick[item.id] || ""}
            wareRanges={d.ware_ranges}
            pickSlots={(d.skill_pick_slots || []).filter((slot) => slot.source_kind === "bioware")}
            onSkillPick={(key, skill) =>
              patch({ skill_picks: { ...(ch.skill_picks || {}), [key]: skill } })
            }
            onSlotChange={(wareId) => setSlotPick((cur) => ({ ...cur, [item.id]: wareId }))}
            onPatchRow={(id, next) =>
              patch({
                bioware: (ch.bioware || []).map((row) => {
                  if (row.id === id) return { ...row, ...next };
                  if (next.side && row.parent_id === id) return { ...row, side: next.side };
                  return row;
                }),
              })
            }
            onRemove={(id) => {
              const bioware = removeWareTree(ch.bioware || [], id);
              patch({
                bioware,
                skill_picks: dropRemovedWarePicks(ch.skill_picks, [
                  ...(ch.cyberware || []),
                  ...bioware,
                ]),
              });
            }}
            onAddChild={(wareId) => {
              const spec = catalog.bioware.items.find((w) => w.id === wareId);
              if (!spec) return;
              const range = wareBounds(spec, d.ware_ranges);
              patch({
                bioware: [
                  ...(ch.bioware || []),
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
          placeholder="バイオウェアを検索"
          aria-label="バイオウェアを検索"
          value={bioSearch}
          onChange={(e) => setBioSearch(e.target.value)}
        />
        <select value={bioCat} onChange={(e) => setBioCat(e.target.value)}>
          <option value="all">すべての分類</option>
          {bioCats.map((c) => (
            <option key={c} value={c}>
              {tr(c)}
            </option>
          ))}
        </select>
        <select value={effectiveBioGrade} onChange={(e) => setBioGrade(e.target.value)}>
          {bioGrades.map((g) => (
            <option key={g.name} value={g.name}>
              追加時 {g.name}
            </option>
          ))}
        </select>
      </div>
      <div className="quality-list">
        {filteredBio.map((w) => (
          <div className="quality-item" key={w.id}>
            <div>
              <b>{tr(w.name)}</b>
              <div className="muted">
                {w.name} / {w.category} / ESS {w.ess} / {w.cost}¥ / {w.source}
                {w.maxrating > 1 ? ` / 最大R${w.maxrating}` : ""}
                {w.allow_subsystems?.length ? " / スロット可" : ""}
              </div>
            </div>
            <button
              className="btn primary"
              onClick={() => {
                const range = wareBounds(w, d.ware_ranges);
                patch({
                  bioware: [
                    ...(ch.bioware || []),
                    {
                      ware_id: w.id,
                      rating: range.min,
                      grade: w.forcegrade || effectiveBioGrade,
                      wireless: true,
                      side: nextFreeSide(ch.bioware || [], catalog.bioware.items, w),
                    },
                  ],
                });
              }}
            >
              追加
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
