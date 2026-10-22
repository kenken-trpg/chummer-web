"use client";
import { useState } from "react";
import { PickerList } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { HelpTip } from "@/components/help/HelpTip";
import { sourceBit } from "@/lib/character/format";
import { editRow } from "@/lib/character/rows";

/**
 * The Critter Powers tab (Chummer's): an Infected or a Dracoform quality opens
 * it and names the category it sells (Infected, Drake). Each power costs its
 * own karma. What the tab offers is the engine's `critter_power_offer` — the
 * powers in an open category whose requirements are met — since those read
 * the qualities and the other powers the character has.
 *
 * The powers a quality grants outright are not here; they are on the quality.
 */
export function CritterPowersTab({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  const [search, setSearch] = useState("");
  const owned = d.critter_powers || [];
  const offer = new Set(d.critter_power_offer || []);
  const spent = owned.reduce((sum, row) => sum + row.karma, 0);
  const update = (id: string, change: { rating?: number | null; extra?: string }) =>
    patch({
      critter_powers: editRow(ch.critter_powers, id, change),
    });
  const stats = (row: { type: string; action: string; range: string; duration: string }) =>
    ui("cpower.stats", {
      type: row.type,
      action: tr(row.action),
      range: tr(row.range),
      duration: tr(row.duration),
    });
  // the stats line is the data's own terms, some of them blank
  const statsTip = (name: string) => (
    <HelpTip
      label={ui("help.open", { label: tr(name) })}
      lines={[{ label: ui("help.cpower.stats") }, { label: ui("help.cpower.blank") }]}
    >
      {ui("help.cpower.statsLabel")}
    </HelpTip>
  );
  const q = search.trim().toLowerCase();
  const items = (catalog.buyable_critter_powers || []).filter(
    (item) =>
      offer.has(item.id) &&
      (!q || item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q)),
  );

  return (
    <div className="card">
      <p className="muted">
        <HelpTip
          label={ui("help.open", { label: ui("cpower.title") })}
          lines={[
            { label: ui("help.cpower.what") },
            { label: ui("help.cpower.offer") },
            { label: ui("help.cpower.granted") },
          ]}
        >
          {ui("cpower.title")}
        </HelpTip>{" "}
        {ui("cpower.summary", { count: owned.length, karma: spent })}
        {" / "}
        {ui("cpower.categories", {
          list: (d.critter_power_categories || []).join(ui("common.termSep")),
        })}
      </p>
      {owned.map((row) => {
        const mine = (ch.critter_powers || []).find((p) => p.id === row.id);
        return (
          <div className="cyber-item" key={row.id}>
            <div>
              <b>{tr(row.name)}</b>
              <div className="muted">
                {statsTip(row.name)} {row.name} / {row.category} / {stats(row)}
                {ui("common.karmaCost", { karma: row.karma })}
                {" / "}
                {sourceBit(row, ui)}
              </div>
              {row.has_rating || row.needs_extra ? (
                <div className="cyber-controls">
                  {row.has_rating ? (
                    <label>
                      {ui("cpower.rating")}
                      <input
                        type="number"
                        min={1}
                        value={mine?.rating ?? row.rating ?? ""}
                        onChange={(e) =>
                          update(row.id, { rating: e.target.value ? Number(e.target.value) : null })
                        }
                      />
                    </label>
                  ) : null}
                  {row.needs_extra ? (
                    <label>
                      {ui("cpower.extra")}
                      <input
                        type="text"
                        value={mine?.extra ?? row.extra}
                        onChange={(e) => update(row.id, { extra: e.target.value })}
                      />
                    </label>
                  ) : null}
                </div>
              ) : null}
            </div>
            <button
              className="btn danger"
              onClick={() =>
                patch({ critter_powers: (ch.critter_powers || []).filter((p) => p.id !== row.id) })
              }
            >
              {ui("common.delete")}
            </button>
          </div>
        );
      })}
      <div className="option-row" style={{ flexWrap: "wrap", gap: 8 }}>
        <input
          type="search"
          placeholder={ui("cpower.search")}
          aria-label={ui("cpower.search")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>
      {items.length ? (
        <div className="quality-list">
          <PickerList items={items}>
            {(item) => (
              <div className="quality-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {statsTip(item.name)} {item.name} / {item.category} / {stats(item)}
                    {ui("common.karmaCost", { karma: item.karma })}
                    {" / "}
                    {sourceBit(item, ui)}
                  </div>
                </div>
                <button
                  className="btn primary"
                  onClick={() =>
                    patch({
                      critter_powers: [
                        ...(ch.critter_powers || []),
                        { power_id: item.id, ...(item.has_rating ? { rating: 1 } : {}) },
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
      ) : (
        <p className="muted">{ui("cpower.none")}</p>
      )}
    </div>
  );
}
