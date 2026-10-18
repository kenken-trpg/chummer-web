"use client";

import { PickerList } from "@/components/character/CatalogPicker";
import { RangeInput } from "@/components/character/RangeInput";
import type { TabPanelProps } from "@/components/character/types";

import { useMemo, useState } from "react";
import { MentorPicker } from "@/components/character/MentorPicker";
import { formatPoints, sourceBit } from "@/lib/character/format";
import { AdeptPowerRow } from "@/components/character/tabs/adept/AdeptPowerRow";
import { EnhancementsSection } from "@/components/character/tabs/adept/EnhancementsSection";
import { QiFociSection } from "@/components/character/tabs/adept/QiFociSection";
import { HelpTip } from "@/components/help/HelpTip";

export function AdeptTab({
  catalog,
  character: ch,
  d,
  tr,
  t,
  ui,
  patch,
  setCharacter,
}: TabPanelProps) {
  const [powerSearch, setPowerSearch] = useState("");

  // An empty search box lists every power the settings allow. It used to
  // narrow to SR5 underneath the book list, so switching a book on changed
  // nothing until you typed.
  const matchedPowers = useMemo(() => {
    const q = powerSearch.trim().toLowerCase();
    return (catalog.powers || []).filter(
      (item) =>
        !q || item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q),
    );
  }, [catalog, powerSearch, tr]);

  return (
    <div className="card">
      <p className="muted">
        <HelpTip
          label={ui("help.open", { label: ui("help.adept.statsLabel") })}
          lines={[
            { label: ui("help.adept.pp") },
            { label: ui("help.adept.mystic") },
            { label: ui("help.adept.way") },
          ]}
        >
          {ui("help.adept.statsLabel")}
        </HelpTip>{" "}
        {ui("adept.powerPoints", {
          used: formatPoints(d.power_points?.used || 0),
          max: formatPoints(d.power_points?.max || 0),
        })}
        {(d.way_discount?.max || 0) > 0
          ? ui("adept.wayDiscount", {
              used: formatPoints(d.way_discount?.used || 0),
              max: formatPoints(d.way_discount?.max || 0),
            })
          : ""}
      </p>
      {d.needs_mentor ? (
        <MentorPicker catalog={catalog} mentor={d.mentor} ch={ch} tr={tr} onPatch={patch} />
      ) : null}
      {ch.talent === "Mystic Adept" ? (
        <div className="skill-row">
          <span>{ui("adept.boughtPoints")}</span>
          <RangeInput
            min={0}
            max={d.totals.MAG || 0}
            value={ch.mystic_pp || 0}
            label={ui("adept.boughtPoints")}
            title={ui("adept.boughtPointsHint")}
            onDraft={(value) => setCharacter({ ...ch, mystic_pp: value })}
            onCommit={(value) => patch({ mystic_pp: value })}
          />
          <b>{ch.mystic_pp || 0}</b>
        </div>
      ) : null}
      {(d.adept_powers || []).map((item) => (
        <AdeptPowerRow
          key={item.id}
          item={item}
          character={ch}
          tr={tr}
          t={t}
          ui={ui}
          patch={patch}
        />
      ))}
      <div className="cyber-toolbar" style={{ gridTemplateColumns: "1fr" }}>
        <input
          type="search"
          placeholder={ui("adept.searchPowers")}
          aria-label={ui("adept.searchPowers")}
          value={powerSearch}
          onChange={(e) => setPowerSearch(e.target.value)}
        />
      </div>
      <div className="quality-list">
        <PickerList items={matchedPowers} limit={200}>
          {(item) => (
            <div className="quality-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / {formatPoints(item.points)} PP
                  {item.extrapointcost ? ` +${formatPoints(item.extrapointcost)}` : ""}
                  {item.adeptway
                    ? ui("adept.wayLabel", { points: formatPoints(item.adeptway) })
                    : ""}
                  {item.levels ? ui("adept.hasLevels") : ""}
                  {item.select === "spell" ? ui("adept.spellSelect") : ""}
                  {" / "}
                  {sourceBit(item, ui)}
                </div>
              </div>
              <button
                className="btn primary"
                onClick={() =>
                  patch({
                    adept_powers: [
                      ...(ch.adept_powers || []),
                      { power_id: item.id, rating: 1, discounted: !!item.adeptway },
                    ],
                  })
                }
              >
                {ui("common.add")}
              </button>
            </div>
          )}
        </PickerList>
      </div>
      <EnhancementsSection catalog={catalog} character={ch} d={d} tr={tr} ui={ui} patch={patch} />
      <QiFociSection catalog={catalog} character={ch} d={d} tr={tr} t={t} ui={ui} patch={patch} />
    </div>
  );
}
