"use client";

import type { TabPanelProps } from "@/components/character/types";

import { useState } from "react";
import { kindLabel } from "@/lib/character/format";

export function SpellsTab({ catalog, character: ch, d, tr, patch, setCharacter }: TabPanelProps) {

  const [spellSearch, setSpellSearch] = useState("");
  const [spellKind, setSpellKind] = useState<"all" | "spell" | "ritual" | "enchantment">("all");

  return (
          <div className="card">
            <p className="muted">
              無料 {(d.spell_points?.used || 0) - (d.spell_points?.paid || 0)}/{d.spell_points?.free || 0}
              {(d.spell_points?.paid || 0) > 0 ? ` ・ 追加 ${d.spell_points?.paid}（各5カルマ）` : ""}
              {d.drain_resist ? ` ・ ドレイン抵抗 ${d.drain_resist.attrs} ${d.drain_resist.pool}` : ""}
              {" ・ 呪文・儀式・エンチャントは同じ無料枠"}
              {(d.limit_spell_categories || []).length || (d.allow_spell_categories || []).length
                ? ` ・ 許可カテゴリ ${[...(d.limit_spell_categories || []), ...(d.allow_spell_categories || [])].filter((v, i, a) => a.indexOf(v) === i).join("、")}`
                : ""}
            </p>
            <label>
              伝統
              <select
                value={ch.tradition_id || ""}
                onChange={(e) => patch({ tradition_id: e.target.value || null })}
              >
                <option value="">選択してください</option>
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
                    {item.damage_mod ? ` ・ ダメージ+${item.damage_mod}` : ""}
                    {item.spell ? ` @ F${item.spell.force} → ドレイン ${item.spell.drain == null ? "特殊" : `${item.spell.drain}${item.spell.drain_code || ""}`}${item.spell.drain_mod ? `（修正${item.spell.drain_mod > 0 ? "+" : ""}${item.spell.drain_mod}）` : ""}` : ""}
                    {item.focus_bonus ? ` / 焦点+${item.focus_bonus}` : ""}
                    {item.free ? " / 無料" : ` / ${item.karma}カルマ`}
                    {item.required?.length ? ` / 必要 ${item.required.map((name) => tr(name)).join("・")}` : ""}
                    {" / "}{item.source}
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
                          onChange={(e) => patch({
                            spells: (ch.spells || []).map((row) => (
                              row.id === item.id ? { ...row, force: Number(e.target.value) } : row
                            )),
                          })}
                        />
                      </label>
                    </div>
                  ) : null}
                </div>
                <button className="btn danger" onClick={() => patch({
                  spells: (ch.spells || []).filter((row) => row.id !== item.id),
                })}>削除</button>
              </div>
            ))}
            <div className="tabs" style={{ marginTop: 12 }}>
              {([
                ["all", "すべて"],
                ["spell", "呪文"],
                ["ritual", "儀式"],
                ["enchantment", "エンチャント"],
              ] as const).map(([key, label]) => (
                <button key={key} className={`tab ${spellKind === key ? "active" : ""}`} onClick={() => setSpellKind(key)}>{label}</button>
              ))}
            </div>
            <input type="search" placeholder="術式を検索" value={spellSearch} onChange={(e) => setSpellSearch(e.target.value)} />
            <div className="quality-list">
              {(catalog.spells || [])
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
                    if (text.toLowerCase() === "spell" && (item.kind || "spell") === "spell") return false;
                    if (text && (item.descriptor || "").includes(text)) return false;
                  }
                  return true;
                })
                .filter((item) => {
                  const q = spellSearch.trim().toLowerCase();
                  if (q) {
                    return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q) || (item.category || "").toLowerCase().includes(q);
                  }
                  if (spellKind === "enchantment") return true;
                  return item.source === "SR5";
                })
                .slice(0, 40)
                .map((item) => {
                  const paid = (d.spell_points?.used || 0) >= (d.spell_points?.free || 0);
                  return (
                    <div className="quality-item" key={item.id}>
                      <div>
                        <b>{tr(item.name)}</b>
                        <div className="muted">
                          {item.name} / {kindLabel(item.kind)} / {item.useskill || "Spellcasting"} / {item.dv} / {item.source}
                          {item.required?.length ? ` / 必要 ${item.required.map((name) => tr(name)).join("・")}` : ""}
                          {paid ? " / 5カルマ" : " / 無料"}
                        </div>
                      </div>
                      <button className="btn primary" onClick={() => patch({
                        spells: [...(ch.spells || []), { spell_id: item.id }],
                      })}>追加</button>
                    </div>
                  );
                })}
            </div>
          </div>

  );
}
