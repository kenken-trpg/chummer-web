"use client";

import { useMemo, useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import { MentorPicker } from "@/components/character/MentorPicker";
import { SkillPickSelects } from "@/components/character/SkillPickSelects";
import { QualityExtraEditor } from "@/components/character/tabs/qualities/QualityExtraEditor";
import { mergeRatings } from "@/lib/character/format";
import {
  dropSkillPicksForPrefix,
  qualityBlockReason,
  type QualityReqCtx,
} from "@/lib/character/quality";

export function QualitiesTab({
  catalog,
  character: ch,
  d,
  tr,
  t,
  patch,
  setCharacter,
}: TabPanelProps) {
  const [qSearch, setQSearch] = useState("");
  const [qCat, setQCat] = useState<"all" | "Positive" | "Negative" | "Metagenic">("all");
  const filteredQualities = useMemo(() => {
    const q = qSearch.trim().toLowerCase();
    const metaOnly = qCat === "Metagenic";
    return catalog.qualities
      .filter((item) => (metaOnly ? item.metagenic : qCat === "all" || item.category === qCat))
      .filter((item) => {
        if (!q) return metaOnly || !item.source || item.source === "SR5";
        return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
      })
      .slice(0, 80);
  }, [catalog, qSearch, qCat, tr]);

  const qualityCtx: QualityReqCtx = {
    qualities: new Set((d.qualities || []).map((item) => item.name)),
    metatypes: new Set([ch.metatype, ch.metavariant || ""].filter(Boolean)),
    magenabled: d.enabled_tabs.includes("MAG"),
    resenabled: d.enabled_tabs.includes("RES"),
    skills: mergeRatings(d.skill_totals, d.skillsoft),
    knowledge: mergeRatings(ch.knowledge_skills, d.skillsoft),
    powers: new Set((d.adept_powers || []).map((item) => item.name)),
    spells: new Set((d.spells || []).map((item) => item.name)),
    cyberware: new Set((d.cyberware || []).map((item) => item.name)),
    bioware: new Set((d.bioware || []).map((item) => item.name)),
    tradition: d.tradition?.name || "",
    essence: d.essence,
    essLost: (d.essence_lost_cyber || 0) + (d.essence_lost_bio || 0),
  };
  const ownedFromDerived = d.qualities || [];
  const catalogById = useMemo(() => {
    const map = new Map((catalog.qualities || []).map((item) => [item.id, item]));
    return map;
  }, [catalog.qualities]);

  return (
    <div className="card">
      {d.needs_mentor ? (
        <MentorPicker catalog={catalog} mentor={d.mentor} ch={ch} tr={tr} onPatch={patch} />
      ) : null}
      <SkillPickSelects
        slots={(d.skill_pick_slots || []).filter((slot) => slot.source_kind === "quality")}
        tr={tr}
        onPick={(key, skill) => patch({ skill_picks: { ...(ch.skill_picks || {}), [key]: skill } })}
      />
      <p className="muted">
        カルマ {d.karma.remaining} / {d.karma.pool}
        {" ・ "}不利から得られるカルマ {d.karma.negative?.used || 0}
        {d.karma.negative?.max == null ? "" : `/${d.karma.negative.max}`}
        {d.career ? " ・ キャリア" : ""}
      </p>
      {d.metagenic &&
      (d.metagenic.limit > 0 || d.metagenic.positive > 0 || d.metagenic.negative > 0) ? (
        <p className={`muted${d.metagenic.balanced ? "" : " errors"}`}>
          メタジェネティック資質: 有利 {d.metagenic.positive} ／ 不利 {d.metagenic.negative}
          {d.metagenic.limit > 0 ? ` ／ 上限 ${d.metagenic.limit}` : "（Changeling 未取得）"}
          {d.metagenic.balanced ? "" : " ・ 収支が不均衡（不利＝有利 か 有利−1）"}
        </p>
      ) : null}
      {ownedFromDerived.length ? (
        <>
          <h3>取得済み</h3>
          {ownedFromDerived.map((q, idx) => (
            <div className="quality-item" key={`owned-${q.id}-${idx}`}>
              <div>
                <b>{tr(q.name)}</b>
                <div className="muted">
                  {q.name} / {q.category === "Negative" ? "不利な資質" : "有利な資質"} / カルマ{" "}
                  {q.karma}
                  {q.side
                    ? ` / ${q.side === "Left" ? "左" : q.side === "Right" ? "右" : q.side}`
                    : ""}
                  {q.free ? " / 付帯（無料）" : ""}
                </div>
                <QualityExtraEditor
                  q={q}
                  ch={ch}
                  d={d}
                  tr={tr}
                  t={t}
                  patch={patch}
                  setCharacter={setCharacter}
                  catalog={catalog}
                  catalogById={catalogById}
                />
              </div>
              {q.free ? (
                <span className="muted">付帯</span>
              ) : (
                <button
                  className="btn danger"
                  onClick={() => {
                    const extras = { ...(ch.quality_extras || {}) };
                    const remaining = ch.quality_ids.filter((id) => id === q.id).length - 1;
                    if (remaining <= 0) {
                      delete extras[q.id];
                      delete extras[`${q.id}:contact`];
                    }
                    let removed = false;
                    patch({
                      quality_ids: ch.quality_ids.filter((id) => {
                        if (!removed && id === q.id) {
                          removed = true;
                          return false;
                        }
                        return true;
                      }),
                      quality_extras: extras,
                      skill_picks:
                        remaining <= 0
                          ? dropSkillPicksForPrefix(ch.skill_picks, [`quality:${q.id}:`])
                          : ch.skill_picks,
                    });
                  }}
                >
                  削除
                </button>
              )}
            </div>
          ))}
        </>
      ) : (
        <p className="muted">まだありません。有利／不利で絞り込んで追加できます。</p>
      )}
      <div className="option-row">
        <button className={`tab ${qCat === "all" ? "active" : ""}`} onClick={() => setQCat("all")}>
          すべて
        </button>
        <button
          className={`tab ${qCat === "Positive" ? "active" : ""}`}
          onClick={() => setQCat("Positive")}
        >
          有利
        </button>
        <button
          className={`tab ${qCat === "Negative" ? "active" : ""}`}
          onClick={() => setQCat("Negative")}
        >
          不利
        </button>
        <button
          className={`tab ${qCat === "Metagenic" ? "active" : ""}`}
          onClick={() => setQCat("Metagenic")}
        >
          メタジェネ
        </button>
      </div>
      <input
        type="search"
        placeholder="資質を検索"
        aria-label="資質を検索"
        value={qSearch}
        onChange={(e) => setQSearch(e.target.value)}
      />
      <div className="quality-list">
        {filteredQualities.map((q) => {
          const ownedCount = ch.quality_ids.filter((id) => id === q.id).length;
          const maxTakes = q.max_takes == null ? null : Number(q.max_takes ?? 1);
          const canAddMore = maxTakes == null || ownedCount < maxTakes;
          const added = ownedCount > 0;
          const ownedWays = new Set(
            (catalog.qualities || [])
              .filter((item) => item.is_way && ch.quality_ids.includes(item.id))
              .map((item) => item.name),
          );
          const replaces =
            !added &&
            !!q.is_way &&
            (q.forbidden_qualities || []).some((name) => ownedWays.has(name));
          const blocked = canAddMore ? qualityBlockReason(q, qualityCtx) : "";
          return (
            <div className="quality-item" key={q.id}>
              <div>
                <b>{tr(q.name)}</b>
                <div className="muted">
                  {q.name} / {q.category === "Negative" ? "不利な資質" : "有利な資質"} / カルマ{" "}
                  {q.karma} / {q.source}
                  {maxTakes == null ? " / 繰り返し可" : maxTakes > 1 ? ` / 最大${maxTakes}` : ""}
                  {ownedCount > 0 && (maxTakes == null || maxTakes > 1)
                    ? ` / 取得${ownedCount}`
                    : ""}
                  {q.needs_extra ? " / 対象が必要" : ""}
                  {q.is_way ? " / 他の Way と排他" : ""}
                  {replaces ? " / 追加すると両立しない資質を外します" : ""}
                  {blocked ? ` / ${blocked}` : ""}
                </div>
              </div>
              <button
                className={`btn ${added && !canAddMore ? "danger" : "primary"}`}
                disabled={canAddMore ? !!blocked : false}
                onClick={() => {
                  if (added && !canAddMore) {
                    const extras = { ...(ch.quality_extras || {}) };
                    delete extras[q.id];
                    delete extras[`${q.id}:contact`];
                    patch({
                      quality_ids: ch.quality_ids.filter((id) => id !== q.id),
                      quality_extras: extras,
                      skill_picks: dropSkillPicksForPrefix(ch.skill_picks, [`quality:${q.id}:`]),
                    });
                    return;
                  }
                  if (!canAddMore || blocked) return;
                  patch({
                    quality_ids: [...ch.quality_ids, q.id],
                    skill_picks: ch.skill_picks || {},
                  });
                }}
              >
                {added && !canAddMore ? "削除" : replaces ? "入れ替え" : "追加"}
              </button>
            </div>
          );
        })}
      </div>
    </div>
  );
}
