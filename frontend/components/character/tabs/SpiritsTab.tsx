"use client";

import type { TabPanelProps } from "@/components/character/types";

import { SPIRIT_ROLE_JA } from "@/lib/character/constants";
import { optionalNumber, testLine } from "@/lib/character/format";

export function SpiritsTab({ catalog, character: ch, d, tr, patch, setCharacter }: TabPanelProps) {

  return (
          <div className="card">
            <p className="muted">
              一時召喚は召喚+MAG[Force] vs Force。結合は結合+MAG[Force] vs Force×2と試薬 Force×20¥。ドレインは相手ヒット×2（最低2）。Forceが魔力超なら物理。
              {d.drain_resist ? ` ・ ドレイン抵抗 ${d.drain_resist.attrs} ${d.drain_resist.pool}` : ""}
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
            {(d.spirits || []).map((item) => (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name} / {item.role_label || item.role} / {item.bound ? "結合" : "一時召喚"} / F{item.force} / サービス {item.services}
                    {item.bound ? ` / 試薬 ${item.nuyen.toLocaleString()}¥` : " / 日の出または日の入りまで"}
                    {" / "}{item.source}
                  </div>
                  {item.test ? <div className="muted">{testLine(item.test)}</div> : null}
                  {item.attributes ? (
                    <div className="muted">
                      {["BOD", "AGI", "REA", "STR", "WIL", "LOG", "INT", "CHA"].map((key) => `${key} ${item.attributes?.[key] ?? "-"}`).join(" ・ ")}
                      {item.attributes.INI != null ? ` ・ INI ${item.attributes.INI}` : ""}
                    </div>
                  ) : null}
                  {item.powers?.length ? <div className="muted">能力 {item.powers.map((name) => tr(name)).join("・")}</div> : null}
                  <div className="cyber-controls">
                    <label>
                      Force
                      <input
                        type="number"
                        min={1}
                        max={item.force_max}
                        value={item.force}
                        onChange={(e) => patch({
                          spirits: (ch.spirits || []).map((row) => (
                            row.id === item.id ? { ...row, force: Number(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      サービス
                      <input
                        type="number"
                        min={0}
                        max={item.force_max}
                        value={item.services}
                        onChange={(e) => patch({
                          spirits: (ch.spirits || []).map((row) => (
                            row.id === item.id ? { ...row, services: Number(e.target.value), hits: null, opposed_hits: null } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      {item.bound ? "結合" : "召喚"}ヒット
                      <input
                        type="number"
                        min={0}
                        value={item.hits ?? ""}
                        onChange={(e) => patch({
                          spirits: (ch.spirits || []).map((row) => (
                            row.id === item.id ? { ...row, hits: optionalNumber(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      精霊ヒット
                      <input
                        type="number"
                        min={0}
                        value={item.opposed_hits ?? ""}
                        onChange={(e) => patch({
                          spirits: (ch.spirits || []).map((row) => (
                            row.id === item.id ? { ...row, opposed_hits: optionalNumber(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      種類
                      <select
                        value={item.bound ? "bound" : "summoned"}
                        onChange={(e) => patch({
                          spirits: (ch.spirits || []).map((row) => (
                            row.id === item.id ? { ...row, bound: e.target.value === "bound" } : row
                          )),
                        })}
                      >
                        <option value="summoned">一時召喚</option>
                        <option value="bound">結合</option>
                      </select>
                    </label>
                  </div>
                </div>
                <button className="btn danger" onClick={() => patch({
                  spirits: (ch.spirits || []).filter((row) => row.id !== item.id),
                })}>削除</button>
              </div>
            ))}
            <div className="quality-list">
              {Object.entries(d.tradition?.spirits || {}).map(([role, name]) => {
                const spec = (catalog.spirits || []).find((row) => row.name === name);
                if (!spec) return null;
                return (
                  <div className="quality-item" key={role}>
                    <div>
                      <b>{tr(spec.name)}</b>
                      <div className="muted">
                        {spec.name} / {SPIRIT_ROLE_JA[role] || role} / 召喚 vs Force ・ 結合 vs Force×2 / {spec.source}
                      </div>
                      <div className="muted">
                        {["BOD", "AGI", "REA", "STR"].map((key) => `${key} ${spec.attributes?.[key] || "F"}`).join(" ・ ")}
                      </div>
                    </div>
                    <div>
                      <button className="btn" onClick={() => patch({
                        spirits: [...(ch.spirits || []), { spirit_id: spec.id, force: 1, services: 1, bound: false }],
                      })}>召喚</button>
                      {" "}
                      <button className="btn primary" onClick={() => patch({
                        spirits: [...(ch.spirits || []), { spirit_id: spec.id, force: 1, services: 1, bound: true }],
                      })}>結合</button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

  );
}
