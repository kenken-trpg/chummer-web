"use client";
import { CORE_ONLY, PickerList } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { useState } from "react";
import { kindLabel } from "@/lib/character/format";
import { spellDescriptors, spellDuration, spellRange } from "@/lib/spell-terms";

export function SpellsTab({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  const [spellSearch, setSpellSearch] = useState("");
  const [spellKind, setSpellKind] = useState<"all" | "spell" | "ritual" | "enchantment">("all");

  return (
    <div className="card">
      <p className="muted">
        {ui("spell.free", {
          used: (d.spell_points?.used || 0) - (d.spell_points?.paid || 0),
          free: d.spell_points?.free || 0,
        })}
        {(d.spell_points?.paid || 0) > 0
          ? ui("spell.paid", {
              paid: d.spell_points?.paid || 0,
              karma: d.spell_points?.spell_karma ?? 5,
            })
          : d.spell_points?.spell_karma != null && d.spell_points.spell_karma !== 5
            ? ui("spell.extraKarma", { karma: d.spell_points.spell_karma })
            : ""}
        {d.drain_resist
          ? ui("magic.drainResist", { attrs: d.drain_resist.attrs, pool: d.drain_resist.pool })
          : ""}
        {ui("spell.sharedPool")}
        {(d.limit_spell_categories || []).length || (d.allow_spell_categories || []).length
          ? ui("spell.allowedCategories", {
              list: [...(d.limit_spell_categories || []), ...(d.allow_spell_categories || [])]
                .filter((v, i, a) => a.indexOf(v) === i)
                .join(ui("common.listSep")),
            })
          : ""}
        {(d.allow_spell_ranges || []).length
          ? ui("spell.allowedRanges", {
              list: (d.allow_spell_ranges || []).join(ui("common.listSep")),
            })
          : ""}
      </p>
      <label>
        {ui("magic.tradition")}
        <select
          value={ch.tradition_id || ""}
          onChange={(e) => patch({ tradition_id: e.target.value || null })}
        >
          <option value="">{ui("magic.choose")}</option>
          {(catalog.traditions || []).map((item) => (
            <option key={item.id} value={item.id}>
              {tr(item.name)}（{item.drain_attrs.join("+")}）
            </option>
          ))}
        </select>
      </label>
      {(d.spells || []).map((item) => (
        <div className="cyber-item" key={item.id}>
          <div>
            <b>{tr(item.name)}</b>
            <div className="muted">
              {item.name} / {kindLabel(item.kind)} / {item.useskill || "Spellcasting"} / {item.dv}
              {item.range || item.duration
                ? ` / ${[spellRange(item.range), spellDuration(item.duration)].filter(Boolean).join("・")}`
                : ""}
              {item.descriptor ? ` / ${spellDescriptors(item.descriptor)}` : ""}
              {item.damage_mod ? ui("spell.damageMod", { mod: item.damage_mod }) : ""}
              {item.barehanded_adept ? ui("spell.barehanded") : ""}
              {item.spell
                ? ui("spell.drainAt", {
                    force: item.spell.force,
                    drain:
                      (item.spell.drain == null
                        ? ui("spell.drainSpecial")
                        : `${item.spell.drain}${item.spell.drain_code || ""}`) +
                      (item.spell.drain_mod
                        ? ui("spell.drainMod", {
                            mod: `${item.spell.drain_mod > 0 ? "+" : ""}${item.spell.drain_mod}`,
                          })
                        : ""),
                  })
                : ""}
              {item.focus_bonus ? ui("spell.focusBonus", { bonus: item.focus_bonus }) : ""}
              {item.free ? ui("spell.freeSlot") : ui("spell.karmaCost", { karma: item.karma })}
              {item.required?.length
                ? ui("spell.required", {
                    list: item.required.map((name) => tr(name)).join(ui("common.termSep")),
                  })
                : ""}
              {" / "}
              {item.source}
            </div>
            {item.has_force && item.spell ? (
              <div className="cyber-controls">
                <label>
                  Force
                  <input
                    type="number"
                    min={item.spell.force_min}
                    max={item.spell.force_max}
                    value={item.spell.force}
                    onChange={(e) =>
                      patch({
                        spells: (ch.spells || []).map((row) =>
                          row.id === item.id ? { ...row, force: Number(e.target.value) } : row,
                        ),
                      })
                    }
                  />
                </label>
              </div>
            ) : null}
          </div>
          <button
            className="btn danger"
            onClick={() =>
              patch({
                spells: (ch.spells || []).filter((row) => row.id !== item.id),
              })
            }
          >
            {ui("common.delete")}
          </button>
        </div>
      ))}
      <div className="tabs" style={{ marginTop: 12 }}>
        {(
          [
            ["all", "common.all"],
            ["spell", "spell.kind.spell"],
            ["ritual", "spell.kind.ritual"],
            ["enchantment", "spell.kind.enchantment"],
          ] as const
        ).map(([key, label]) => (
          <button
            key={key}
            className={`tab ${spellKind === key ? "active" : ""}`}
            onClick={() => setSpellKind(key)}
          >
            {ui(label)}
          </button>
        ))}
      </div>
      <input
        type="search"
        placeholder={ui("spell.search")}
        aria-label={ui("spell.search")}
        value={spellSearch}
        onChange={(e) => setSpellSearch(e.target.value)}
      />
      <div className="quality-list">
        <PickerList
          items={(catalog.spells || [])
            .filter((item) => item.learnable !== false)
            .filter((item) => !(ch.spells || []).some((row) => row.spell_id === item.id))
            .filter((item) => spellKind === "all" || (item.kind || "spell") === spellKind)
            .filter((item) => {
              const limits = d.limit_spell_categories || [];
              const allows = d.allow_spell_categories || [];
              if (limits.length || allows.length) {
                const allowed = new Set([...limits, ...allows]);
                if (!allowed.has(item.category || "")) return false;
              }
              const blocked = d.block_spell_descriptors || [];
              for (const text of blocked) {
                if (text.toLowerCase() === "spell" && (item.kind || "spell") === "spell")
                  return false;
                if (text && (item.descriptor || "").includes(text)) return false;
              }
              const ranges = d.allow_spell_ranges || [];
              if (d.spell_range_gated && ranges.length) {
                if (!ranges.includes(item.range || "")) return false;
              }
              return true;
            })
            .filter((item) => {
              const q = spellSearch.trim().toLowerCase();
              if (q) {
                return (
                  item.name.toLowerCase().includes(q) ||
                  tr(item.name).toLowerCase().includes(q) ||
                  (item.category || "").toLowerCase().includes(q)
                );
              }
              if (spellKind === "enchantment") return true;
              return item.source === "SR5";
            })}
          note={spellSearch.trim() ? undefined : CORE_ONLY}
        >
          {(item) => {
            const paid = (d.spell_points?.used || 0) >= (d.spell_points?.free || 0);
            return (
              <div className="quality-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name} / {kindLabel(item.kind)} / {item.useskill || "Spellcasting"} /{" "}
                    {item.dv} / {item.source}
                    {item.required?.length
                      ? ui("spell.required", {
                          list: item.required.map((name) => tr(name)).join(ui("common.termSep")),
                        })
                      : ""}
                    {paid ? ui("spell.karmaCost", { karma: 5 }) : ui("spell.freeSlot")}
                  </div>
                </div>
                <button
                  className="btn primary"
                  onClick={() =>
                    patch({
                      spells: [...(ch.spells || []), { spell_id: item.id }],
                    })
                  }
                >
                  {ui("common.add")}
                </button>
              </div>
            );
          }}
        </PickerList>
      </div>
    </div>
  );
}
