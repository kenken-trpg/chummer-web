"use client";

import type { Catalog, Character } from "@/lib/types";
import type { UiFn } from "@/lib/i18n";
import { SkillPickSelects } from "@/components/character/SkillPickSelects";
import { QualityExtraEditor } from "@/components/character/tabs/qualities/QualityExtraEditor";
import { CritterPowerRow } from "@/components/character/CritterPowerRow";
import { HelpTip } from "@/components/help/HelpTip";
import {
  dropSkillPicksForPrefix,
  grantedLevels,
  qualityBlockReason,
  qualityLevelMax,
  setQualityLevel,
  type QualityDisplayRow,
  type QualityReqCtx,
} from "@/lib/character/quality";

type CatalogQuality = Catalog["qualities"][number];

/**
 * One quality the character has, with everything it still leaves to decide.
 *
 * A row is rarely just a name: a leveled quality has its level here, an
 * addiction its substance, a quality that grants a skill its pick, a critter
 * quality its powers. The delete button is the other half — it has to take the
 * quality's extras and skill picks with it, and for a leveled quality
 * "deleting" means setting the level to zero rather than dropping one id.
 */
export function OwnedQualityRow({
  q,
  ch,
  d,
  tr,
  trGroup,
  t,
  ui,
  patch,
  setCharacter,
  catalog,
  catalogById,
  qualityCtx,
  careerPricing,
  careerMult,
}: {
  q: QualityDisplayRow;
  ch: Character;
  d: Character["derived"];
  tr: (name: string) => string;
  trGroup: (group: string) => string;
  t: (key: string, fallback?: string) => string;
  ui: UiFn;
  patch: (body: Record<string, unknown>) => void | Promise<void>;
  setCharacter: (next: Character) => void;
  catalog: Catalog;
  catalogById: Map<string, CatalogQuality>;
  qualityCtx: QualityReqCtx;
  /** Whether a positive quality costs career karma (SR5 p.107). */
  careerPricing: boolean;
  /** What a negative quality's buy-off is multiplied by. */
  careerMult: (id: string) => number;
}) {
  return (
    <div className="quality-item">
      <div>
        <b>
          {tr(q.name)}
          {q.level != null ? ` Lv${q.level}` : ""}
        </b>
        <div className="muted">
          {q.name} / {q.category === "Negative" ? ui("qual.negative") : ui("qual.positive")} /{" "}
          <HelpTip
            label={ui("help.open", { label: ui("help.qualityRow.of", { name: tr(q.name) }) })}
            lines={[
              { label: ui("help.qualityRow.karma") },
              ...(q.karma_base != null && q.karma_base !== q.karma
                ? [{ label: ui("help.qualityRow.base") }]
                : []),
              ...(q.free ? [{ label: ui("help.qualityRow.free") }] : []),
              ...(careerPricing && !q.free ? [{ label: ui("help.quality.career") }] : []),
            ]}
          >
            {ui("qual.karmaLabel")}
          </HelpTip>{" "}
          {q.karma}
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
          {q.origin === "Metatype"
            ? ` / ${ui("meta.innate", { name: tr(q.origin_name || ch.metatype) })}`
            : ""}
          {q.disabled_by ? ui("qual.disabledBy", { ware: tr(q.disabled_by) }) : ""}
          {q.career_cost == null
            ? careerPricing && !q.free && q.category === "Negative"
              ? ui("qual.buyoffHint", { cost: -q.karma * careerMult(q.id) })
              : ""
            : q.career_cost > 0
              ? ui("qual.careerTaken", { cost: q.career_cost })
              : ui("qual.careerTakenNegative")}
        </div>
        {/* Everything this quality still needs decided — a level, an
                addiction's substance, a skill pick, an optional power —
                plus the powers it brings. Indented as one block so a row
                like "依存症" and the select that says what it is for read
                as one item rather than two neighbours. Empty for most
                qualities, and `:empty` hides the rule then. */}
        <div className="quality-extras">
          {q.level != null && !q.free && catalogById.has(q.id) ? (
            <label>
              {ui("qual.level")}{" "}
              <select
                aria-label={ui("qual.ownedLevel", { name: tr(q.name) })}
                value={q.level}
                onChange={(e) =>
                  patch({
                    quality_ids: setQualityLevel(ch.quality_ids, q.id, Number(e.target.value)),
                  })
                }
              >
                {Array.from(
                  {
                    length: Math.max(
                      q.level,
                      qualityLevelMax(
                        catalogById.get(q.id)!,
                        ch.quality_ids,
                        catalog.qualities,
                        grantedLevels(d.qualities || [], catalogById.get(q.id)!),
                      ),
                    ),
                  },
                  (_, i) => i + 1,
                ).map((level) => (
                  <option
                    key={level}
                    value={level}
                    disabled={
                      level > q.level! &&
                      !!qualityBlockReason(catalogById.get(q.id)!, qualityCtx, ui)
                    }
                  >
                    Lv{level}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          <SkillPickSelects
            slots={(d.skill_pick_slots || []).filter(
              (slot) => slot.source_kind === "quality" && slot.source_id === q.id,
            )}
            tr={tr}
            onPick={(key, skill) =>
              patch({ skill_picks: { ...(ch.skill_picks || {}), [key]: skill } })
            }
          />
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
          {q.optional_powers?.length ? (
            <select
              aria-label={`${tr(q.name)}: ${ui("qual.optionalPower")}`}
              value={q.optional_power || ""}
              onChange={(e) =>
                patch({
                  quality_extras: {
                    ...(ch.quality_extras || {}),
                    [`${q.id}:optionalpower`]: e.target.value,
                  },
                })
              }
            >
              <option value="">{ui("qual.optionalPower")}</option>
              {q.optional_powers.map((name) => (
                <option key={name} value={name}>
                  {tr(name)}
                </option>
              ))}
            </select>
          ) : null}
          {q.critter_powers?.length ? (
            <div className="muted">
              {ui("common.powersHead")}
              <ul className="critter-powers">
                {q.critter_powers.map((power, i) => (
                  <li key={`${power.name}-${i}`}>
                    <CritterPowerRow power={power} tr={tr} ui={ui} />
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      </div>
      {q.origin === "Metatype" && q.removable && !ch.career ? (
        <RemoveInnateButton q={q} ch={ch} tr={tr} ui={ui} patch={patch} catalogById={catalogById} />
      ) : q.free ? (
        <span className="muted">
          {ui(q.origin === "Metatype" ? "meta.innateFixed" : "qual.attached")}
        </span>
      ) : (
        <button
          className="btn danger"
          onClick={() => {
            const extras = { ...(ch.quality_extras || {}) };
            const remaining =
              q.level != null ? 0 : ch.quality_ids.filter((id) => id === q.id).length - 1;
            if (remaining <= 0) {
              for (const key of Object.keys(extras)) {
                if (key === q.id || key.startsWith(`${q.id}:`)) delete extras[key];
              }
            }
            let removed = false;
            patch({
              quality_ids:
                q.level != null
                  ? setQualityLevel(ch.quality_ids, q.id, 0)
                  : ch.quality_ids.filter((id) => {
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
  );
}

/**
 * A metatype's `removable` quality (a Shapeshifter's Uneducated), which
 * Chummer lets go at creation for its value the other way round: a negative
 * one is bought off, a positive one gives its karma back. The row itself
 * shows 0 karma, being innate, so the price comes from the catalog.
 */
function RemoveInnateButton({
  q,
  ch,
  tr,
  ui,
  patch,
  catalogById,
}: {
  q: QualityDisplayRow;
  ch: Character;
  tr: (name: string) => string;
  ui: UiFn;
  patch: (body: Record<string, unknown>) => void | Promise<void>;
  catalogById: Map<string, CatalogQuality>;
}) {
  const cost = -(catalogById.get(q.id)?.karma ?? 0);
  return (
    <button
      className="btn"
      title={ui("qual.innateRemoveHint", { name: tr(q.name) })}
      onClick={() =>
        patch({ removed_innate_qualities: [...(ch.removed_innate_qualities || []), q.id] })
      }
    >
      {cost < 0
        ? ui("qual.innateRemoveRefund", { cost: -cost })
        : ui("qual.innateRemove", { cost })}
    </button>
  );
}
