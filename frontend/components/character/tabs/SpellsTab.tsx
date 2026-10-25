"use client";
import { PickerList } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { useState } from "react";
import { kindLabel, sourceBit } from "@/lib/character/format";
import { spellDescriptors, spellDuration, spellLabel, spellRange } from "@/lib/spell-terms";
import { attrLabel } from "@/lib/ui-strings";
import { HelpTip } from "@/components/help/HelpTip";
import { editRow } from "@/lib/character/rows";

export function SpellsTab({ catalog, character: ch, d, t, tr, ui, patch }: TabPanelProps) {
  const [spellSearch, setSpellSearch] = useState("");
  const [spellKind, setSpellKind] = useState<"all" | "spell" | "ritual" | "enchantment">("all");

  return (
    <div className="card">
      <p className="muted">
        <HelpTip
          label={ui("help.open", { label: ui("help.spell.pointsLabel") })}
          lines={[
            { label: ui("help.spell.pointsFree") },
            { label: ui("help.spell.pointsTouch") },
            { label: ui("help.spell.pointsPaid") },
          ]}
        >
          {ui("help.spell.pointsLabel")}
        </HelpTip>{" "}
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
          <option value="">{ui("common.choose")}</option>
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
            <b>{spellLabel(item, tr, t)}</b>
            <div className="muted">
              <HelpTip
                label={ui("help.open", { label: tr(item.name) })}
                lines={[
                  { label: ui("help.spell.drain") },
                  { label: ui("help.spell.force") },
                  { label: ui("help.spell.drainResist") },
                  ...(item.range || item.duration ? [{ label: ui("help.spell.range") }] : []),
                ]}
              >
                {ui("help.spell.statsLabel")}
              </HelpTip>{" "}
              {item.name} / {kindLabel(item.kind, ui)} / {item.useskill || "Spellcasting"} /{" "}
              {item.dv}
              {item.range || item.duration
                ? ` / ${[spellRange(item.range, ui), spellDuration(item.duration, ui)].filter(Boolean).join("・")}`
                : ""}
              {item.descriptor ? ` / ${spellDescriptors(item.descriptor, ui)}` : ""}
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
              {item.free ? ui("common.freeSlot") : ui("common.karmaCost", { karma: item.karma })}
              {item.required?.length
                ? ui("spell.required", {
                    list: item.required.map((name) => tr(name)).join(ui("common.termSep")),
                  })
                : ""}
              {" / "}
              {sourceBit(item, ui)}
            </div>
            {(item.has_force && item.spell) || item.extra_kind ? (
              <div className="cyber-controls">
                {item.extra_kind === "attribute" ? (
                  <label>
                    <HelpTip
                      label={ui("help.open", { label: ui("common.attribute") })}
                      lines={[
                        { label: ui("help.spell.pickAttr") },
                        { label: ui("help.spell.pickSame") },
                      ]}
                    >
                      {ui("common.attribute")}
                    </HelpTip>{" "}
                    <select
                      aria-label={ui("common.attribute")}
                      value={item.extra || ""}
                      onChange={(e) =>
                        patch({
                          spells: editRow(ch.spells, item.id, { extra: e.target.value || null }),
                        })
                      }
                    >
                      <option value="">{ui("common.choose")}</option>
                      {(item.extra_options || []).map((name) => (
                        <option key={name} value={name}>
                          {attrLabel(name, t)}
                        </option>
                      ))}
                    </select>
                  </label>
                ) : null}
                {item.extra_kind === "text" ? (
                  <label>
                    <HelpTip
                      label={ui("help.open", { label: ui("common.target") })}
                      lines={[
                        { label: ui("help.spell.pickText") },
                        { label: ui("help.spell.pickSame") },
                      ]}
                    >
                      {ui("common.target")}
                    </HelpTip>{" "}
                    {/* committed on leaving the field, as a quality's text
                        is: each keystroke would recompute the character */}
                    <input
                      type="text"
                      aria-label={ui("common.target")}
                      key={item.extra || ""}
                      defaultValue={item.extra || ""}
                      onBlur={(e) => {
                        const extra = e.target.value.trim();
                        if (extra !== (item.extra || ""))
                          patch({ spells: editRow(ch.spells, item.id, { extra: extra || null }) });
                      }}
                    />
                  </label>
                ) : null}
                {item.has_force && item.spell ? (
                  <label>
                    {ui("common.force")}
                    <input
                      type="number"
                      min={item.spell.force_min}
                      max={item.spell.force_max}
                      value={item.spell.force}
                      onChange={(e) =>
                        patch({
                          spells: editRow(ch.spells, item.id, { force: Number(e.target.value) }),
                        })
                      }
                    />
                  </label>
                ) : null}
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
            // a spell that picks is one spell per pick: Increase [Attribute]
            // stays offered after the first
            .filter(
              (item) =>
                item.needs_extra || !(ch.spells || []).some((row) => row.spell_id === item.id),
            )
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
              // `<PickerList>` applies the settings' book list; this used
              // to narrow to SR5 again underneath it
              return true;
            })}
        >
          {(item) => {
            const paid = (d.spell_points?.used || 0) >= (d.spell_points?.free || 0);
            return (
              <div className="quality-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name} / {kindLabel(item.kind, ui)} / {item.useskill || "Spellcasting"} /{" "}
                    {item.dv} / {sourceBit(item, ui)}
                    {item.required?.length
                      ? ui("spell.required", {
                          list: item.required.map((name) => tr(name)).join(ui("common.termSep")),
                        })
                      : ""}
                    {paid ? ui("common.karmaCost", { karma: 5 }) : ui("common.freeSlot")}
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
