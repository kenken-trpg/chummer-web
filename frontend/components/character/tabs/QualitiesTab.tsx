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
  trGroup,
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
  const filteredQualities = matchedQualities.slice(0, 200);

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
  const catalogById = useMemo(() => {
    const map = new Map((catalog.qualities || []).map((item) => [item.id, item]));
    return map;
  }, [catalog.qualities]);
  const ownedFromDerived = d.qualities || [];
  // SR5 p.107: after chargen a positive quality costs twice, and buying a
  // negative one off costs twice what it gave (`double_career: false` opts out)
  const careerPricing = Boolean(d.quality_career_pricing);
  const careerMult = (id: string) => (catalogById.get(id)?.double_career === false ? 1 : 2);
  const careerChanged =
    careerPricing &&
    (ownedFromDerived.some((q) => q.career_cost != null) || (d.qualities_removed || []).length > 0);
  // a chargen slip fixed in play is not a purchase: take today's list as the
  // chargen one, which drops every career charge and buy-off
  const rebaseline = () => {
    if (!ch.career_baseline || !window.confirm(ui("qual.rebaselineConfirm"))) return;
    patch({ career_baseline: { ...ch.career_baseline, quality_ids: [...ch.quality_ids] } });
  };

  return (
    <div className="card">
      {d.needs_mentor || d.needs_paragon ? (
        <MentorPicker
          catalog={catalog}
          mentor={d.mentor}
          ch={ch}
          tr={tr}
          onPatch={patch}
          paragon={Boolean(d.needs_paragon)}
        />
      ) : null}
      <SkillPickSelects
        slots={(d.skill_pick_slots || []).filter((slot) => slot.source_kind === "quality")}
        tr={tr}
        onPick={(key, skill) => patch({ skill_picks: { ...(ch.skill_picks || {}), [key]: skill } })}
      />
      {/* a career buy-off can take the pool below zero; say so where it happened */}
      <p className={`muted${d.karma.remaining < 0 ? " errors" : ""}`}>
        {ui("common.karmaPool", { remaining: d.karma.remaining, pool: d.karma.pool })}
        {d.karma.remaining < 0
          ? ` ・ ${ui("engine.karma.negative", { karma: d.karma.remaining })}`
          : ""}
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
                  {q.karma_base != null && q.karma_base !== q.karma
                    ? ui("qual.karmaBase", { base: q.karma_base })
                    : ""}
                  {q.side
                    ? ` / ${
                        q.side === "Left"
                          ? ui("common.left")
                          : q.side === "Right"
                            ? ui("common.right")
                            : q.side
                      }`
                    : ""}
                  {q.free ? ui("qual.freeAttached") : ""}
                  {q.career_cost == null
                    ? careerPricing && !q.free && q.category === "Negative"
                      ? ui("qual.buyoffHint", { cost: -q.karma * careerMult(q.id) })
                      : ""
                    : q.career_cost > 0
                      ? ui("qual.careerTaken", { cost: q.career_cost })
                      : ui("qual.careerTakenNegative")}
                </div>
                <QualityExtraEditor
                  q={q}
                  ch={ch}
                  d={d}
                  tr={tr}
                  trGroup={trGroup}
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
      {d.qualities_removed?.length ? (
        <>
          <h3>{ui("qual.removed")}</h3>
          {d.qualities_removed.map((q, idx) => (
            <div className="quality-item" key={`removed-${q.id}-${idx}`}>
              <div>
                <b>{tr(q.name)}</b>
                <div className="muted">
                  {q.name} /{" "}
                  {q.category === "Negative"
                    ? ui("qual.removedBuyoff", { cost: q.karma })
                    : ui("qual.removedPositive")}
                </div>
              </div>
              <button
                className="btn"
                title={ui("qual.restoreHint", { name: tr(q.name) })}
                // back to the chargen count: the buy-off charge goes with it
                onClick={() => patch({ quality_ids: [...ch.quality_ids, q.id] })}
              >
                {ui("qual.restore")}
              </button>
            </div>
          ))}
        </>
      ) : null}
      {careerChanged ? (
        <p className="muted">
          <button className="btn" onClick={rebaseline} title={ui("qual.rebaselineHint")}>
            {ui("qual.rebaseline")}
          </button>
        </p>
      ) : null}
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
          // `include_in_limit`: siblings share the limit (Indomitable: 3 across all three)
          const siblings = new Set(q.include_in_limit || []);
          const sharedCap = siblings.size ? q.limit_with_inclusions || maxTakes : null;
          const sharedCount = siblings.size
            ? ch.quality_ids.filter(
                (id) =>
                  id === q.id ||
                  siblings.has(
                    (catalog.qualities || []).find((item) => item.id === id)?.name || "",
                  ),
              ).length
            : ownedCount;
          const canAddMore =
            (maxTakes == null || ownedCount < maxTakes) &&
            (sharedCap == null || sharedCount < sharedCap);
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
          const blocked = canAddMore ? qualityBlockReason(q, qualityCtx, ui) : "";
          return (
            <div className="quality-item" key={q.id}>
              <div>
                <b>{tr(q.name)}</b>
                <div className="muted">
                  {q.name} / {q.category === "Negative" ? ui("qual.negative") : ui("qual.positive")}{" "}
                  / {ui("qual.karmaLabel")} {q.karma} / {q.source}
                  {careerPricing
                    ? q.karma > 0
                      ? ui("qual.careerPrice", {
                          cost: q.karma * (q.double_career === false ? 1 : 2),
                        })
                      : ui("qual.careerPriceNegative")
                    : ""}
                  {maxTakes == null
                    ? ui("common.repeatable")
                    : maxTakes > 1
                      ? ui("common.maxTakes", { max: maxTakes })
                      : ""}
                  {ownedCount > 0 && (maxTakes == null || maxTakes > 1)
                    ? ui("qual.taken", { count: ownedCount })
                    : ""}
                  {sharedCap != null
                    ? ui("qual.sharedLimit", {
                        names: [...siblings].map(tr).join(ui("common.listSep")),
                        max: sharedCap,
                      })
                    : ""}
                  {q.needs_extra ? ui("qual.needsTarget") : ""}
                  {q.is_way ? ui("qual.wayExclusive") : ""}
                  {replaces ? ui("qual.replacesNote") : ""}
                  {blocked ? ` / ${blocked}` : ""}
                </div>
              </div>
              <button
                className={`btn ${added && !canAddMore ? "danger" : "primary"}`}
                // full and not taken: a sibling holds the shared limit, nothing to do
                disabled={canAddMore ? !!blocked : !added}
                // the same button reads 追加 / 差替 / 削除 depending on what is
                // already taken; say which quality it is about to act on
                title={ui("picker.buyLabel", {
                  name: tr(q.name),
                  action:
                    added && !canAddMore
                      ? ui("common.delete")
                      : replaces
                        ? ui("qual.replace")
                        : ui("common.add"),
                })}
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
