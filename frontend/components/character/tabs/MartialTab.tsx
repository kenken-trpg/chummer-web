"use client";

import type { TabPanelProps } from "@/components/character/types";

import { useState } from "react";

export function MartialTab({ catalog, character: ch, d, tr, patch, setCharacter }: TabPanelProps) {
  const [martialSearch, setMartialSearch] = useState("");

  return (
    <div className="card">
      <p className="muted">
        流派 {d.martial_art_points?.styles || 0}/{d.martial_art_points?.style_max || 1}
        {" ・ "}技 {d.martial_art_points?.techniques || 0}/
        {d.martial_art_points?.technique_max || 5}
        {" ・ "}カルマ {d.martial_art_points?.karma || 0}
        （流派7カルマに技1つ込み、追加技は各5カルマ。作成時は流派1・技合計5まで。品質武道は流派枠外）
        {(d.unarmed_reach || 0) > 0 ? ` ・ 素手Reach +${d.unarmed_reach}` : ""}
      </p>
      {(d.martial_arts || []).map((item) => {
        const local = (ch.martial_arts || []).find((row) => row.id === item.id);
        const selected = new Set(local?.techniques || item.techniques.map((tech) => tech.name));
        const techMax = item.technique_max ?? null;
        return (
          <div className="cyber-item" key={item.id}>
            <div>
              <b>{tr(item.name)}</b>
              <div className="muted">
                {item.name}
                {item.free
                  ? " / 無料（品質）"
                  : ` / ${item.karma}カルマ（流派 ${item.style_karma} + 追加技）`}
                {" / "}
                {item.source}
                {item.page ? ` p.${item.page}` : ""}
                {techMax === 1 ? " / 技1つのみ" : ""}
              </div>
              <div className="martial-techs" style={{ display: "grid", gap: 4, marginTop: 8 }}>
                {item.technique_options.map((name) => {
                  const owned = selected.has(name);
                  const techMeta = item.techniques.find((tech) => tech.name === name);
                  const atCap = techMax != null && !owned && selected.size >= techMax;
                  return (
                    <label key={name} style={{ display: "flex", gap: 8, alignItems: "center" }}>
                      <input
                        type="checkbox"
                        checked={owned}
                        disabled={atCap}
                        onChange={(e) => {
                          const next = new Set(selected);
                          if (e.target.checked) {
                            if (techMax === 1) next.clear();
                            next.add(name);
                          } else {
                            next.delete(name);
                          }
                          const techniques = item.technique_options.filter((opt) => next.has(opt));
                          patch({
                            martial_arts: (ch.martial_arts || []).map((row) =>
                              row.id === item.id ? { ...row, techniques } : row,
                            ),
                          });
                        }}
                      />
                      <span>
                        {tr(name)}
                        {owned && techMeta?.free
                          ? " / 込み"
                          : owned
                            ? ` / ${techMeta?.karma || 5}カルマ`
                            : ""}
                      </span>
                    </label>
                  );
                })}
              </div>
            </div>
            {item.locked ? (
              <span className="muted">品質連動</span>
            ) : (
              <button
                className="btn"
                onClick={() =>
                  patch({
                    martial_arts: (ch.martial_arts || []).filter((row) => row.id !== item.id),
                  })
                }
              >
                削除
              </button>
            )}
          </div>
        );
      })}
      <input
        type="search"
        placeholder="武道を検索"
        value={martialSearch}
        onChange={(e) => setMartialSearch(e.target.value)}
      />
      <div className="list">
        {(catalog.martial_arts || [])
          .filter((item) => {
            const q = martialSearch.trim().toLowerCase();
            if (!q) return true;
            return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
          })
          .slice(0, 40)
          .map((item) => {
            const owned = (d.martial_arts || []).some((row) => row.art_id === item.id);
            const blocked =
              !owned &&
              (d.martial_art_points?.styles || 0) >= (d.martial_art_points?.style_max || 1);
            return (
              <div className="list-row" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name} / {item.cost}カルマ（技1込み） / 技 {item.techniques.length}種 /{" "}
                    {item.source}
                    {item.spec_options?.length
                      ? ` / 専門化候補 ${item.spec_options.map((opt) => `${opt.skill}:${opt.spec}`).join(", ")}`
                      : ""}
                  </div>
                </div>
                <button
                  className="btn"
                  disabled={owned || blocked}
                  onClick={() => {
                    const first = item.techniques[0];
                    if (!first) return;
                    patch({
                      martial_arts: [
                        ...(ch.martial_arts || []),
                        { art_id: item.id, techniques: [first] },
                      ],
                    });
                  }}
                >
                  {owned ? "取得済" : blocked ? "上限" : "取得"}
                </button>
              </div>
            );
          })}
      </div>
    </div>
  );
}
