"use client";

import { useMemo, useState } from "react";
import { CORE_ONLY, PickerFootnote } from "@/components/character/CatalogPicker";
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
  ui,
  t,
  patch,
  setCharacter,
}: TabPanelProps) {
  const [qSearch, setQSearch] = useState("");
  const [qCat, setQCat] = useState<"all" | "Positive" | "Negative" | "Metagenic">("all");
  const matchedQualities = useMemo(() => {
    const q = qSearch.trim().toLowerCase();
    const metaOnly = qCat === "Metagenic";
    return catalog.qualities
      .filter((item) => (metaOnly ? item.metagenic : qCat === "all" || item.category === qCat))
      .filter((item) => {
        if (!q) return metaOnly || !item.source || item.source === "SR5";
        return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
      });
  }, [catalog, qSearch, qCat, tr]);
  const filteredQualities = matchedQualities.slice(0, 80);

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
        {ui("qual.karma", { remaining: d.karma.remaining, pool: d.karma.pool })}
        {" ・ "}
        {ui("qual.negativeKarma", { used: d.karma.negative?.used || 0 })}
        {d.karma.negative?.max == null ? "" : `/${d.karma.negative.max}`}
        {d.career ? ` ・ ${ui("qual.career")}` : ""}
      </p>
      {d.metagenic &&
      (d.metagenic.limit > 0 || d.metagenic.positive > 0 || d.metagenic.negative > 0) ? (
        <p className={`muted${d.metagenic.balanced ? "" : " errors"}`}>
          {ui("qual.metagenic", {
            positive: d.metagenic.positive,
            negative: d.metagenic.negative,
          })}
          {d.metagenic.limit > 0
            ? ui("qual.metagenicLimit", { limit: d.metagenic.limit })
            : ui("qual.metagenicNoChangeling")}
          {d.metagenic.balanced ? "" : ui("qual.metagenicUnbalanced")}
        </p>
      ) : null}
      {ownedFromDerived.length ? (
        <>
          <h3>{ui("qual.owned")}</h3>
          {ownedFromDerived.map((q, idx) => (
            <div className="quality-item" key={`owned-${q.id}-${idx}`}>
              <div>
                <b>{tr(q.name)}</b>
                <div className="muted">
                  {q.name} / {q.category === "Negative" ? ui("qual.negative") : ui("qual.positive")}{" "}
                  / {ui("qual.karmaLabel")} {q.karma}
                  {q.side
                    ? ` / ${
                        q.side === "Left"
                          ? ui("qual.sideLeft")
                          : q.side === "Right"
                            ? ui("qual.sideRight")
                            : q.side
                      }`
                    : ""}
                  {q.free ? ui("qual.freeAttached") : ""}
                </div>
                <QualityExtraEditor
                  q={q}
                  ch={ch}
                  d={d}
                  tr={tr}
                  t={t}
                  ui={ui}
                  patch={patch}
                  setCharacter={setCharacter}
                  catalog={catalog}
                  catalogById={catalogById}
                />
              </div>
              {q.free ? (
                <span className="muted">{ui("qual.attached")}</span>
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
                  {ui("common.delete")}
                </button>
              )}
            </div>
          ))}
        </>
      ) : (
        <p className="muted">{ui("qual.empty")}</p>
      )}
      <div className="option-row">
        <button className={`tab ${qCat === "all" ? "active" : ""}`} onClick={() => setQCat("all")}>
          {ui("common.all")}
        </button>
        <button
          className={`tab ${qCat === "Positive" ? "active" : ""}`}
          onClick={() => setQCat("Positive")}
        >
          {ui("qual.filter.positive")}
        </button>
        <button
          className={`tab ${qCat === "Negative" ? "active" : ""}`}
          onClick={() => setQCat("Negative")}
        >
          {ui("qual.filter.negative")}
        </button>
        <button
          className={`tab ${qCat === "Metagenic" ? "active" : ""}`}
          onClick={() => setQCat("Metagenic")}
        >
          {ui("qual.filter.metagenic")}
        </button>
      </div>
      <input
        type="search"
        placeholder={ui("qual.search")}
        aria-label={ui("qual.search")}
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
                  {q.name} / {q.category === "Negative" ? ui("qual.negative") : ui("qual.positive")}{" "}
                  / {ui("qual.karmaLabel")} {q.karma} / {q.source}
                  {maxTakes == null
                    ? ui("common.repeatable")
                    : maxTakes > 1
                      ? ui("common.maxTakes", { max: maxTakes })
                      : ""}
                  {ownedCount > 0 && (maxTakes == null || maxTakes > 1)
                    ? ui("qual.taken", { count: ownedCount })
                    : ""}
                  {q.needs_extra ? ui("qual.needsTarget") : ""}
                  {q.is_way ? ui("qual.wayExclusive") : ""}
                  {replaces ? ui("qual.replacesNote") : ""}
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
                {added && !canAddMore
                  ? ui("common.delete")
                  : replaces
                    ? ui("qual.replace")
                    : ui("common.add")}
              </button>
            </div>
          );
        })}
        <PickerFootnote
          matched={matchedQualities.length}
          shown={filteredQualities.length}
          note={qSearch.trim() ? undefined : CORE_ONLY}
        />
      </div>
    </div>
  );
}
