"use client";

import type { TabPanelProps } from "@/components/character/types";

import { useState } from "react";
import { optionalNumber, testLine } from "@/lib/character/format";

export function SpritesTab({ catalog, character: ch, d, tr, patch, setCharacter }: TabPanelProps) {

  const [spriteSearch, setSpriteSearch] = useState("");

  return (
          <div className="card">
            <p className="muted">
              コンパイルは Compiling+RES[Level] vs Level×2。登録は Registering+RES[Level] vs Level×2（Level時間）。フェードは相手ヒット×2（最低2）。Levelが共振力超なら物理。登録数は共振力まで。
              {d.fade_resist ? ` ・ フェード抵抗 ${d.fade_resist.attrs} ${d.fade_resist.pool}` : ""}
              {d.living_persona ? ` ・ リビングペルソナ DR${d.living_persona.device_rating} ATK${d.living_persona.attack} SLZ${d.living_persona.sleaze} DP${d.living_persona.dataprocessing} FW${d.living_persona.firewall}` : ""}
            </p>
            {(d.sprites || []).map((item) => (
              <div className="cyber-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name} / {item.registered ? "登録" : "コンパイル"} / L{item.level} / タスク {item.services}
                    {item.registered ? "" : " / 再起動またはリブートまで"}
                    {" / "}{item.source}
                  </div>
                  {item.test ? <div className="muted">{testLine(item.test, "フェード")}</div> : null}
                  {item.matrix ? (
                    <div className="muted">
                      ATK {item.matrix.attack} ・ SLZ {item.matrix.sleaze} ・ DP {item.matrix.dataprocessing} ・ FW {item.matrix.firewall} ・ INI {item.matrix.initiative}
                    </div>
                  ) : null}
                  {item.powers?.length ? <div className="muted">能力 {item.powers.map((name) => tr(name)).join("・")}</div> : null}
                  <div className="cyber-controls">
                    <label>
                      Level
                      <input
                        type="number"
                        min={1}
                        max={item.level_max}
                        value={item.level}
                        onChange={(e) => patch({
                          sprites: (ch.sprites || []).map((row) => (
                            row.id === item.id ? { ...row, level: Number(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      タスク
                      <input
                        type="number"
                        min={0}
                        max={item.level_max}
                        value={item.services}
                        onChange={(e) => patch({
                          sprites: (ch.sprites || []).map((row) => (
                            row.id === item.id ? { ...row, services: Number(e.target.value), hits: null, opposed_hits: null } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      {item.registered ? "登録" : "コンパイル"}ヒット
                      <input
                        type="number"
                        min={0}
                        value={item.hits ?? ""}
                        onChange={(e) => patch({
                          sprites: (ch.sprites || []).map((row) => (
                            row.id === item.id ? { ...row, hits: optionalNumber(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      スプライトヒット
                      <input
                        type="number"
                        min={0}
                        value={item.opposed_hits ?? ""}
                        onChange={(e) => patch({
                          sprites: (ch.sprites || []).map((row) => (
                            row.id === item.id ? { ...row, opposed_hits: optionalNumber(e.target.value) } : row
                          )),
                        })}
                      />
                    </label>
                    <label>
                      種類
                      <select
                        value={item.registered ? "registered" : "compiled"}
                        onChange={(e) => patch({
                          sprites: (ch.sprites || []).map((row) => (
                            row.id === item.id ? { ...row, registered: e.target.value === "registered" } : row
                          )),
                        })}
                      >
                        <option value="compiled">コンパイル</option>
                        <option value="registered">登録</option>
                      </select>
                    </label>
                  </div>
                </div>
                <button className="btn danger" onClick={() => patch({
                  sprites: (ch.sprites || []).filter((row) => row.id !== item.id),
                })}>削除</button>
              </div>
            ))}
            <input type="search" placeholder="スプライトを検索" value={spriteSearch} onChange={(e) => setSpriteSearch(e.target.value)} />
            <div className="quality-list">
              {(catalog.sprites || [])
                .filter((item) => {
                  const q = spriteSearch.trim().toLowerCase();
                  if (q) return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
                  return item.source === "SR5";
                })
                .map((item) => (
                  <div className="quality-item" key={item.id}>
                    <div>
                      <b>{tr(item.name)}</b>
                      <div className="muted">{item.name} / {item.source}</div>
                    </div>
                    <div>
                      <button className="btn" onClick={() => patch({
                        sprites: [...(ch.sprites || []), { sprite_id: item.id, level: 1, registered: false }],
                      })}>コンパイル</button>
                      {" "}
                      <button className="btn primary" onClick={() => patch({
                        sprites: [...(ch.sprites || []), { sprite_id: item.id, level: 1, registered: true }],
                      })}>登録</button>
                    </div>
                  </div>
                ))}
            </div>
          </div>

  );
}
