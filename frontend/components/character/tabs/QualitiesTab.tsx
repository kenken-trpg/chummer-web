"use client";

import { useMemo, useState } from "react";
import { PickerFootnote } from "@/components/character/CatalogPicker";
import { filterByBooks, useAllowedBooks } from "@/lib/character/books";
import type { TabPanelProps } from "@/components/character/types";
import { MentorPicker } from "@/components/character/MentorPicker";
import { OwnedQualityRow } from "@/components/character/tabs/qualities/OwnedQualityRow";
import { QualityKarmaSummary } from "@/components/character/tabs/qualities/QualityKarmaSummary";
import { QualityPickerRow } from "@/components/character/tabs/qualities/QualityPickerRow";
import { mergeRatings } from "@/lib/character/format";
import { qualityDisplayRows, type QualityReqCtx } from "@/lib/character/quality";
import { qualityRestriction } from "@/lib/character/metatype-limits";

/** The four chips above the search box. "Metagenic" cuts across the other
 *  two rather than being a third category of its own. */
const FILTERS = [
  ["all", "common.all"],
  ["Positive", "qual.filter.positive"],
  ["Negative", "qual.filter.negative"],
  ["Metagenic", "qual.filter.metagenic"],
] as const;

type Filter = (typeof FILTERS)[number][0];

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
  const [qCat, setQCat] = useState<Filter>("all");
  // This tab writes its own list rather than using `<CatalogPicker>`, and so
  // had never applied the settings' book list: with Chrome Flesh switched off,
  // 「プロトタイプ・トランスヒューマン」 still turned up in the search and could
  // still be bought. Qualities already taken are not narrowed away — they are
  // listed, and removed, in the 所持 section above.
  const allowedBooks = useAllowedBooks();
  const matchedQualities = useMemo(() => {
    const q = qSearch.trim().toLowerCase();
    const metaOnly = qCat === "Metagenic";
    // An A.I. may take only the qualities its metatype lists — the same
    // `<qualityrestriction>` the server checks (Chummer's SelectQuality).
    const restriction = qualityRestriction(catalog, ch.metatype, ch.metavariant);
    return filterByBooks(allowedBooks, catalog.qualities)
      .filter(
        (item) =>
          !restriction ||
          (restriction[item.category as keyof typeof restriction] ?? []).includes(item.name),
      )
      .filter((item) => (metaOnly ? item.metagenic : qCat === "all" || item.category === qCat))
      .filter(
        (item) =>
          !q || item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q),
      );
  }, [catalog, qSearch, qCat, tr, allowedBooks, ch.metatype, ch.metavariant]);
  const filteredQualities = matchedQualities.slice(0, 200);

  const qualityCtx: QualityReqCtx = {
    qualities: new Set((d.qualities || []).map((item) => item.name)),
    metatypes: new Set([ch.metatype, ch.metavariant || ""].filter(Boolean)),
    magenabled: d.enabled_tabs.includes("MAG"),
    resenabled: d.enabled_tabs.includes("RES"),
    skills: mergeRatings(d.skill_totals, d.skillsoft),
    knowledge: mergeRatings(ch.knowledge_skills, d.skillsoft),
    powers: new Set([
      ...(d.adept_powers || []).map((item) => item.name),
      ...(d.metatype_info.powers || []).filter((item) => item.id).map((item) => item.name),
    ]),
    spells: new Set((d.spells || []).map((item) => item.name)),
    cyberware: new Set((d.cyberware || []).map((item) => item.name)),
    bioware: new Set((d.bioware || []).map((item) => item.name)),
    tradition: d.tradition?.name || "",
    essence: d.essence,
    essLost: (d.essence_lost_cyber || 0) + (d.essence_lost_bio || 0),
  };
  const catalogById = useMemo(
    () => new Map((catalog.qualities || []).map((item) => [item.id, item])),
    [catalog.qualities],
  );
  const ownedFromDerived = qualityDisplayRows(d.qualities || [], catalog.qualities);
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
      <QualityKarmaSummary d={d} ui={ui} />
      {ownedFromDerived.length ? (
        <>
          <h3>{ui("qual.owned")}</h3>
          {ownedFromDerived.map((q, idx) => (
            <OwnedQualityRow
              key={`owned-${q.id}-${idx}`}
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
              qualityCtx={qualityCtx}
              careerPricing={careerPricing}
              careerMult={careerMult}
            />
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
        {FILTERS.map(([value, label]) => (
          <button
            key={value}
            className={`tab ${qCat === value ? "active" : ""}`}
            onClick={() => setQCat(value)}
          >
            {ui(label)}
          </button>
        ))}
      </div>
      <input
        type="search"
        placeholder={ui("qual.search")}
        aria-label={ui("qual.search")}
        value={qSearch}
        onChange={(e) => setQSearch(e.target.value)}
      />
      <div className="quality-list">
        {filteredQualities.map((q) => (
          <QualityPickerRow
            key={q.id}
            q={q}
            ch={ch}
            ui={ui}
            tr={tr}
            patch={patch}
            catalog={catalog}
            qualityCtx={qualityCtx}
            careerPricing={careerPricing}
          />
        ))}
        <PickerFootnote matched={matchedQualities.length} shown={filteredQualities.length} />
      </div>
    </div>
  );
}
