"use client";
import { useState } from "react";
import { PickerList } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { HelpTip } from "@/components/help/HelpTip";
import { sourceBit } from "@/lib/character/format";
import type { MsgKey } from "@/lib/i18n";
import { editRow } from "@/lib/character/rows";

/** `programs.xml`'s five categories, in its own order. */
const CATEGORIES = [
  "Common Programs",
  "Hacking Programs",
  "Software",
  "Autosofts",
  "Advanced Programs",
] as const;

const CATEGORY_KEYS: Record<string, MsgKey> = {
  "Common Programs": "aiprog.cat.common",
  "Hacking Programs": "aiprog.cat.hacking",
  Software: "aiprog.cat.software",
  Autosofts: "aiprog.cat.autosofts",
  "Advanced Programs": "aiprog.cat.advanced",
};

/**
 * An A.I.'s own programs (DT p.158) — not the gear of the same names, which
 * runs on a deck. Each costs karma: 5, or 8 for an advanced one. The one
 * Inherent Program picks is listed too, free and not removable here (it goes
 * with the quality).
 */
export function AIProgramsTab({ catalog, character: ch, d, tr, ui, patch }: TabPanelProps) {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const owned = d.ai_programs || [];
  const ownedNames = new Set(owned.map((row) => row.name));
  const rules = ch.settings;
  const price = (advanced: boolean) =>
    advanced ? (rules?.karma_ai_advanced_program ?? 8) : (rules?.karma_ai_program ?? 5);
  const categoryLabel = (name: string) =>
    CATEGORY_KEYS[name] ? ui(CATEGORY_KEYS[name]) : tr(name);
  const spent = owned.reduce((sum, row) => sum + row.karma, 0);
  const statsTip = (
    name: string,
    row: { required: string[]; needs_extra: boolean; free?: boolean },
  ) => (
    <HelpTip
      label={ui("help.open", { label: tr(name) })}
      lines={[
        { label: ui("help.aiprog.category") },
        ...(row.required.length ? [{ label: ui("help.aiprog.required") }] : []),
        ...(row.needs_extra ? [{ label: ui("help.aiprog.extra") }] : []),
        ...(row.free ? [{ label: ui("help.aiprog.free") }] : []),
      ]}
    >
      {ui("help.aiprog.statsLabel")}
    </HelpTip>
  );
  const setExtra = (id: string, extra: string) =>
    patch({
      ai_programs: editRow(ch.ai_programs, id, { extra }),
    });

  return (
    <div className="card">
      <p className="muted">
        <HelpTip
          label={ui("help.open", { label: ui("aiprog.title") })}
          lines={[{ label: ui("help.aiprog.price") }, { label: ui("help.aiprog.inherent") }]}
        >
          {ui("aiprog.title")}
        </HelpTip>{" "}
        {ui("aiprog.summary", { count: owned.length, karma: spent })}
      </p>
      {owned.map((row) => (
        <div className="cyber-item" key={row.id}>
          <div>
            <b>{tr(row.name)}</b>
            <div className="muted">
              {statsTip(row.name, row)} {row.name} / {categoryLabel(row.category)}
              {row.free
                ? ui("aiprog.grantedBy", { name: tr(row.granted_by) })
                : ui("common.karmaCost", { karma: row.karma })}
              {row.required.length
                ? ` / ${ui("aiprog.required", {
                    list: row.required.map((name) => tr(name)).join(ui("common.termSep")),
                  })}`
                : ""}
              {" / "}
              {sourceBit(row, ui)}
            </div>
            {row.needs_extra && !row.free ? (
              <div className="cyber-controls">
                <label>
                  {ui("aiprog.extra")}
                  <input
                    type="text"
                    value={(ch.ai_programs || []).find((p) => p.id === row.id)?.extra ?? row.extra}
                    onChange={(e) => setExtra(row.id, e.target.value)}
                  />
                </label>
              </div>
            ) : null}
          </div>
          {row.free ? null : (
            <button
              className="btn danger"
              onClick={() =>
                patch({ ai_programs: (ch.ai_programs || []).filter((p) => p.id !== row.id) })
              }
            >
              {ui("common.delete")}
            </button>
          )}
        </div>
      ))}
      <div className="option-row" style={{ flexWrap: "wrap", gap: 8 }}>
        <input
          type="search"
          placeholder={ui("aiprog.search")}
          aria-label={ui("aiprog.search")}
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select
          aria-label={ui("aiprog.category")}
          value={category}
          onChange={(e) => setCategory(e.target.value)}
        >
          <option value="">{ui("common.all")}</option>
          {CATEGORIES.map((name) => (
            <option key={name} value={name}>
              {categoryLabel(name)}
            </option>
          ))}
        </select>
      </div>
      <div className="quality-list">
        <PickerList
          items={(catalog.ai_programs || []).filter((item) => {
            if (category && item.category !== category) return false;
            const q = search.trim().toLowerCase();
            return (
              !q || item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q)
            );
          })}
        >
          {(item) => {
            // SelectAIProgram refuses a program whose base program the A.I.
            // does not have yet; the server reports it, the list says it first
            const missing =
              item.required.length > 0 && !item.required.some((name) => ownedNames.has(name));
            return (
              <div className="quality-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {statsTip(item.name, item)} {item.name} / {categoryLabel(item.category)}
                    {ui("common.karmaCost", { karma: price(item.advanced) })}
                    {item.required.length
                      ? ` / ${ui("aiprog.required", {
                          list: item.required.map((name) => tr(name)).join(ui("common.termSep")),
                        })}`
                      : ""}
                    {" / "}
                    {sourceBit(item, ui)}
                  </div>
                  {missing ? <div className="muted">{ui("aiprog.missingBase")}</div> : null}
                </div>
                <button
                  className="btn primary"
                  disabled={missing}
                  onClick={() =>
                    patch({ ai_programs: [...(ch.ai_programs || []), { program_id: item.id }] })
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
