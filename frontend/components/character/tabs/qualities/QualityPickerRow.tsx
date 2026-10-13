"use client";

import { useState } from "react";
import type { Catalog, Character } from "@/lib/types";
import type { UiFn } from "@/lib/i18n";
import { sourceText } from "@/lib/character/books";
import {
  dropSkillPicksForPrefix,
  qualityBlockReason,
  qualityPickState,
  setQualityLevel,
  type QualityReqCtx,
} from "@/lib/character/quality";

type CatalogQuality = Catalog["qualities"][number];

/**
 * One catalog quality, offered.
 *
 * The same button adds, replaces, changes a level or deletes, depending on
 * what is already taken — a Way replaces the Way it forbids, a quality at its
 * cap offers removal instead, a leveled one buys the level the select shows.
 * `qualityPickState` works out which of those applies; this renders it and
 * says so in the button's title, since "追加" on its own does not.
 *
 * The chosen level is local state: it is a proposal until the button is
 * pressed, and it lives per row so one row's select cannot move another's.
 */
export function QualityPickerRow({
  q,
  ch,
  ui,
  tr,
  patch,
  catalog,
  qualityCtx,
  careerPricing,
}: {
  q: CatalogQuality;
  ch: Character;
  ui: UiFn;
  tr: (name: string) => string;
  patch: (body: Record<string, unknown>) => void | Promise<void>;
  catalog: Catalog;
  qualityCtx: QualityReqCtx;
  /** Whether a positive quality costs career karma (SR5 p.107). */
  careerPricing: boolean;
}) {
  const [level, setLevel] = useState<number | null>(null);
  const {
    ownedCount,
    maxTakes,
    siblings,
    sharedCap,
    canAddMore,
    added,
    hasLevels,
    levelMax,
    replaces,
  } = qualityPickState(q, ch.quality_ids, catalog.qualities);
  const selectedLevel = Math.max(1, Math.min(level ?? (ownedCount || 1), levelMax || 1));
  const increasing = hasLevels ? selectedLevel > ownedCount : canAddMore;
  const shownKarma = q.karma * (hasLevels ? selectedLevel : 1);
  const blocked = increasing ? qualityBlockReason(q, qualityCtx, ui) : "";
  return (
    <div className="quality-item">
      <div>
        <b>{tr(q.name)}</b>
        <div className="muted">
          {q.name} / {q.category === "Negative" ? ui("qual.negative") : ui("qual.positive")} /{" "}
          {ui("qual.karmaLabel")} {shownKarma} / {sourceText(q)}
          {careerPricing
            ? q.karma > 0
              ? ui("qual.careerPrice", {
                  cost:
                    q.karma *
                    (hasLevels ? Math.max(0, selectedLevel - ownedCount) : 1) *
                    (q.double_career === false ? 1 : 2),
                })
              : ui("qual.careerPriceNegative")
            : ""}
          {hasLevels
            ? ui("qual.maxLevel", { max: maxTakes ?? 1 })
            : maxTakes == null
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
      {hasLevels ? (
        <label>
          {ui("qual.level")}{" "}
          <select
            aria-label={ui("qual.pickLevel", { name: tr(q.name) })}
            value={selectedLevel}
            disabled={levelMax < 1}
            onChange={(e) => setLevel(Number(e.target.value))}
          >
            {Array.from({ length: Math.max(1, levelMax) }, (_, i) => i + 1).map((level) => (
              <option key={level} value={level}>
                Lv{level}
              </option>
            ))}
          </select>
        </label>
      ) : null}
      <button
        className={`btn ${!hasLevels && added && !canAddMore ? "danger" : "primary"}`}
        // full and not taken: a sibling holds the shared limit, nothing to do
        disabled={
          hasLevels
            ? levelMax < 1 || selectedLevel === ownedCount || !!blocked
            : canAddMore
              ? !!blocked
              : !added
        }
        // the same button reads 追加 / 差替 / 削除 depending on what is
        // already taken; say which quality it is about to act on
        title={ui("picker.buyLabel", {
          name: tr(q.name),
          action: hasLevels
            ? added
              ? ui("qual.changeLevel")
              : ui("common.add")
            : added && !canAddMore
              ? ui("common.delete")
              : replaces
                ? ui("qual.replace")
                : ui("common.add"),
        })}
        onClick={() => {
          if (hasLevels) {
            if (levelMax < 1 || blocked || selectedLevel === ownedCount) return;
            patch({
              quality_ids: setQualityLevel(ch.quality_ids, q.id, selectedLevel),
              skill_picks: ch.skill_picks || {},
            });
            return;
          }
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
        {hasLevels
          ? added
            ? ui("qual.changeLevel")
            : ui("common.add")
          : added && !canAddMore
            ? ui("common.delete")
            : replaces
              ? ui("qual.replace")
              : ui("common.add")}
      </button>
    </div>
  );
}
