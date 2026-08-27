"use client";

import { useMemo, useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import { MentorPicker } from "@/components/character/MentorPicker";
import { SkillPickSelects } from "@/components/character/SkillPickSelects";
import { ATTRS, ATTR_JA } from "@/lib/character/constants";
import { mergeRatings } from "@/lib/character/format";
import { dropSkillPicksForPrefix, qualityBlockReason, type QualityReqCtx } from "@/lib/character/quality";

export function QualitiesTab({ catalog, character: ch, d, tr, patch, setCharacter }: TabPanelProps) {
  const [qSearch, setQSearch] = useState("");
  const [qCat, setQCat] = useState<"all" | "Positive" | "Negative">("all");
  const filteredQualities = useMemo(() => {
    const q = qSearch.trim().toLowerCase();
    return catalog.qualities
      .filter((item) => qCat === "all" || item.category === qCat)
      .filter((item) => {
        if (!q) return !item.source || item.source === "SR5";
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
  const ownedQualitySpecs = (catalog.qualities || []).filter((item) => ch.quality_ids.includes(item.id));

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
            {ownedQualitySpecs.length ? (
              <>
                <h3>取得済み</h3>
                {ownedQualitySpecs.map((q) => (
                  <div className="quality-item" key={`owned-${q.id}`}>
                    <div>
                      <b>{tr(q.name)}</b>
                      <div className="muted">{q.name} / {q.category === "Negative" ? "不利" : "有利"} / カルマ {q.karma}</div>
                      {q.name === "Black Market Pipeline" ? (
                        <select
                          value={ch.quality_extras?.[q.id] || ""}
                          onChange={(e) => patch({
                            quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
                          })}
                        >
                          <option value="">商品カテゴリを選択</option>
                          {["Weapons", "Armor", "Electronics", "Vehicles", "Cyberware", "Bioware", "Drugs"].map((cat) => (
                            <option key={cat} value={cat}>{cat}</option>
                          ))}
                        </select>
                      ) : q.needs_extra ? (
                        q.name === "Exceptional Attribute" ? (
                          <select
                            value={ch.quality_extras?.[q.id] || ""}
                            onChange={(e) => patch({
                              quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
                            })}
                          >
                            <option value="">属性を選択</option>
                            {ATTRS.filter((key) => key !== "EDG" && key !== "MAG" && key !== "RES").map((key) => (
                              <option key={key} value={key}>{ATTR_JA[key] || key}</option>
                            ))}
                          </select>
                        ) : (
                        <input
                          type="text"
                          placeholder="対象（花粉、日光など）"
                          value={ch.quality_extras?.[q.id] || ""}
                          onChange={(e) => setCharacter({
                            ...ch,
                            quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
                          })}
                          onBlur={(e) => patch({
                            quality_extras: { ...(ch.quality_extras || {}), [q.id]: e.target.value },
                          })}
                        />
                        )
                      ) : null}
                    </div>
                    <button
                      className="btn danger"
                      onClick={() => {
                        const extras = { ...(ch.quality_extras || {}) };
                        delete extras[q.id];
                        patch({
                          quality_ids: ch.quality_ids.filter((id) => id !== q.id),
                          quality_extras: extras,
                          skill_picks: dropSkillPicksForPrefix(ch.skill_picks, [`quality:${q.id}:`]),
                        });
                      }}
                    >
                      削除
                    </button>
                  </div>
                ))}
              </>
            ) : (
              <p className="muted">まだありません。有利／不利で絞り込んで追加できます。</p>
            )}
            <div className="option-row">
              <button className={`tab ${qCat === "all" ? "active" : ""}`} onClick={() => setQCat("all")}>すべて</button>
              <button className={`tab ${qCat === "Positive" ? "active" : ""}`} onClick={() => setQCat("Positive")}>有利</button>
              <button className={`tab ${qCat === "Negative" ? "active" : ""}`} onClick={() => setQCat("Negative")}>不利</button>
            </div>
            <input type="search" placeholder="クオリティを検索" value={qSearch} onChange={(e) => setQSearch(e.target.value)} />
            <div className="quality-list">
              {filteredQualities.map((q) => {
                const added = ch.quality_ids.includes(q.id);
                const ownedWays = new Set(
                  (catalog.qualities || [])
                    .filter((item) => item.is_way && ch.quality_ids.includes(item.id))
                    .map((item) => item.name),
                );
                const replaces = !added && !!q.is_way && (q.forbidden_qualities || []).some((name) => ownedWays.has(name));
                const blocked = added ? "" : qualityBlockReason(q, qualityCtx);
                return (
                  <div className="quality-item" key={q.id}>
                    <div>
                      <b>{tr(q.name)}</b>
                      <div className="muted">
                        {q.name} / {q.category === "Negative" ? "不利" : "有利"} / カルマ {q.karma} / {q.source}
                        {q.needs_extra ? " / 対象が必要" : ""}
                        {q.is_way ? " / 他の Way と排他" : ""}
                        {replaces ? " / 追加すると両立しないクオリティを外します" : ""}
                        {blocked ? ` / ${blocked}` : ""}
                      </div>
                    </div>
                    <button
                      className={`btn ${added ? "danger" : "primary"}`}
                      disabled={!added && !!blocked}
                      onClick={() => {
                        if (added) {
                          const extras = { ...(ch.quality_extras || {}) };
                          delete extras[q.id];
                          patch({
                            quality_ids: ch.quality_ids.filter((id) => id !== q.id),
                            quality_extras: extras,
                            skill_picks: dropSkillPicksForPrefix(ch.skill_picks, [`quality:${q.id}:`]),
                          });
                          return;
                        }
                        patch({
                          quality_ids: [...ch.quality_ids, q.id],
                          skill_picks: ch.skill_picks || {},
                        });
                      }}
                    >
                      {added ? "削除" : replaces ? "入れ替え" : "追加"}
                    </button>
                  </div>
                );
              })}
            </div>
          </div>

  );
}
