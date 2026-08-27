"use client";

import type { TabPanelProps } from "@/components/character/types";

export function SubmersionTab({ catalog, character: ch, d, tr, patch, setCharacter }: TabPanelProps) {

  return (
          <div className="card">
            <p className="muted">
              等級 {d.submersion?.grade || 0}
              {" ・ "}カルマ {d.submersion?.karma || 0}
              （各等級 10 + 等級×3。RES上限 = 種族上限 + 等級。等級 ≤ RES）
            </p>
            <label>
              サブマージョン等級
              <input
                type="range"
                min={0}
                max={Math.max(6, Number(d.totals.RES || 0))}
                value={ch.submersion_grade || 0}
                onChange={(e) => {
                  const grade = Number(e.target.value);
                  const existing = [...(ch.submersions || [])];
                  const byGrade = new Map(existing.map((row) => [row.grade, row]));
                  const next = [];
                  for (let g = 1; g <= grade; g += 1) {
                    next.push(byGrade.get(g) || { grade: g, echo_id: "" });
                  }
                  setCharacter({ ...ch, submersion_grade: grade, submersions: next });
                }}
                onMouseUp={(e) => {
                  const grade = Number((e.target as HTMLInputElement).value);
                  const existing = [...(ch.submersions || [])];
                  const byGrade = new Map(existing.map((row) => [row.grade, row]));
                  const next = [];
                  for (let g = 1; g <= grade; g += 1) {
                    next.push(byGrade.get(g) || { grade: g, echo_id: "" });
                  }
                  patch({ submersion_grade: grade, submersions: next });
                }}
                onTouchEnd={(e) => {
                  const grade = Number((e.target as HTMLInputElement).value);
                  const existing = [...(ch.submersions || [])];
                  const byGrade = new Map(existing.map((row) => [row.grade, row]));
                  const next = [];
                  for (let g = 1; g <= grade; g += 1) {
                    next.push(byGrade.get(g) || { grade: g, echo_id: "" });
                  }
                  patch({ submersion_grade: grade, submersions: next });
                }}
              />
              <b style={{ marginLeft: 8 }}>{ch.submersion_grade || 0}</b>
            </label>
            <div style={{ display: "grid", gap: 12, marginTop: 12 }}>
              {(d.submersion?.choices || []).map((choice) => {
                const local = (ch.submersions || []).find((row) => row.grade === choice.grade);
                const echoId = local?.echo_id || choice.echo_id || "";
                const extra = local?.extra ?? choice.extra ?? "";
                const selected = (catalog.echoes || []).find((item) => item.id === echoId);
                return (
                  <div className="cyber-item" key={choice.id || choice.grade}>
                    <div style={{ width: "100%" }}>
                      <b>等級 {choice.grade}</b>
                      <div className="muted">{choice.karma}カルマ{choice.name ? ` ・ ${tr(choice.name)}` : ""}</div>
                      <div className="grid" style={{ marginTop: 8 }}>
                        <label>
                          エコー
                          <select
                            value={echoId}
                            onChange={(e) => {
                              const nextId = e.target.value;
                              const nextSpec = (catalog.echoes || []).find((item) => item.id === nextId);
                              const submersions = (ch.submersions || []).map((row) => (
                                row.grade === choice.grade
                                  ? { ...row, echo_id: nextId, extra: nextSpec?.needs_extra ? (row.extra || "") : null }
                                  : row
                              ));
                              patch({ submersions });
                            }}
                          >
                            <option value="">選択してください</option>
                            {(catalog.echoes || []).map((item) => (
                              <option key={item.id} value={item.id}>
                                {tr(item.name)} ({item.name})
                                {item.max_takes == null ? " / 繰り返し可" : item.max_takes > 1 ? ` / 最大${item.max_takes}` : ""}
                              </option>
                            ))}
                          </select>
                        </label>
                        {selected?.needs_extra ? (
                          <label>
                            対象（プログラム名など）
                            <input
                              type="text"
                              value={extra || ""}
                              onChange={(e) => {
                                const submersions = (ch.submersions || []).map((row) => (
                                  row.grade === choice.grade ? { ...row, extra: e.target.value } : row
                                ));
                                setCharacter({ ...ch, submersions });
                              }}
                              onBlur={(e) => {
                                const submersions = (ch.submersions || []).map((row) => (
                                  row.grade === choice.grade ? { ...row, extra: e.target.value } : row
                                ));
                                patch({ submersions });
                              }}
                            />
                          </label>
                        ) : null}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

  );
}
