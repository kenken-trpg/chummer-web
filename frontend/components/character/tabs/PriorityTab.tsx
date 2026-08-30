"use client";

import type { TabPanelProps } from "@/components/character/types";

import { CATS, DEFAULT_PRIORITIES, LETTERS, SUM_TO_TEN_COST } from "@/lib/character/constants";

export function PriorityTab({ catalog, character: ch, d, tr, patch, setCharacter }: TabPanelProps) {
  const table = catalog.priority_table;

  return (
          <div className="card">
            <div style={{ display: "flex", gap: 8, marginBottom: 12, flexWrap: "wrap", alignItems: "center" }}>
              <button
                className={`choice ${(ch.build_method || "Priority") === "Priority" ? "selected" : ""}`}
                onClick={() => {
                  const letters = CATS.map((c) => ch.priorities[c.key]);
                  const unique = [...letters].sort().join("") === "ABCDE";
                  patch({
                    build_method: "Priority",
                    ...(unique
                      ? {}
                      : {
                          priorities: { ...DEFAULT_PRIORITIES },
                          talent: "Mundane",
                        }),
                  });
                }}
              >
                Priority
              </button>
              <button
                className={`choice ${(ch.build_method || "Priority") === "SumToTen" ? "selected" : ""}`}
                onClick={() => patch({ build_method: "SumToTen" })}
              >
                Sum to Ten
              </button>
              <button
                className={`choice ${(ch.build_method || "Priority") === "Karma" ? "selected" : ""}`}
                onClick={() => patch({ build_method: "Karma", talent: ch.talent || "Mundane" })}
              >
                Karma
              </button>
              {(ch.build_method || "Priority") === "SumToTen" ? (
                <span className="muted">
                  合計 {d.sum_to_ten?.used ?? 0}/{d.sum_to_ten?.max ?? 10}
                  {" ・ "}A4 / B3 / C2 / D1 / E0
                </span>
              ) : null}
              {(ch.build_method || "Priority") === "Karma" ? (
                <span className="muted">
                  カルマ {d.karma.remaining} / {d.karma.pool}
                  {" ・ "}1K={d.karma_chargen?.nuyen_per_karma ?? 2000}¥（最大 {d.karma_chargen?.nuyen_karma_max ?? 235}K）
                </span>
              ) : (
                <span className="muted">
                  残カルマ→¥ 最大 {d.karma_chargen?.nuyen_karma_max ?? d.nuyen_karma_max ?? 10}K
                </span>
              )}
            </div>
            {(ch.build_method || "Priority") !== "Karma" ? (
              <label style={{ display: "block", marginBottom: 12 }}>
                残カルマ→ニューエン（{ch.karma_nuyen || 0}K = {((ch.karma_nuyen || 0) * (d.karma_chargen?.nuyen_per_karma || 2000)).toLocaleString()}¥）
                <input
                  type="range"
                  min={0}
                  max={d.karma_chargen?.nuyen_karma_max ?? d.nuyen_karma_max ?? 10}
                  value={ch.karma_nuyen || 0}
                  onChange={(e) => setCharacter({ ...ch, karma_nuyen: Number(e.target.value) })}
                  onMouseUp={(e) => patch({ karma_nuyen: Number((e.target as HTMLInputElement).value) })}
                  onTouchEnd={(e) => patch({ karma_nuyen: Number((e.target as HTMLInputElement).value) })}
                  onBlur={(e) => patch({ karma_nuyen: Number(e.target.value) })}
                />
              </label>
            ) : null}
            {(ch.build_method || "Priority") === "Karma" ? (
              <div style={{ display: "grid", gap: 12 }}>
                <p className="muted">
                  優先度表は使いません。メタタイプ／能力値／技能／術式などをカルマで購入します（開始 {d.karma.pool}）。
                  MAG／RES はタレント選択で解禁され、最低1から買い上げます。無料の術式枠はありません。
                </p>
                <label>
                  タレント
                  <select value={ch.talent} onChange={(e) => patch({ talent: e.target.value })}>
                    {(catalog.karma_talents || []).map((t) => (
                      <option key={t.name} value={t.name}>
                        {t.label || t.name}
                        {t.magic ? ` / MAG` : ""}
                        {t.resonance ? ` / RES` : ""}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  カルマ→ニューエン（{ch.karma_nuyen || 0}K = {((ch.karma_nuyen || 0) * (d.karma_chargen?.nuyen_per_karma || 2000)).toLocaleString()}¥）
                  <input
                    type="range"
                    min={0}
                    max={d.karma_chargen?.nuyen_karma_max ?? 235}
                    value={ch.karma_nuyen || 0}
                    onChange={(e) => setCharacter({ ...ch, karma_nuyen: Number(e.target.value) })}
                    onMouseUp={(e) => patch({ karma_nuyen: Number((e.target as HTMLInputElement).value) })}
                    onTouchEnd={(e) => patch({ karma_nuyen: Number((e.target as HTMLInputElement).value) })}
                    onBlur={(e) => patch({ karma_nuyen: Number(e.target.value) })}
                  />
                </label>
                {d.karma_chargen ? (
                  <div className="muted" style={{ display: "grid", gap: 4 }}>
                    <div>内訳: メタタイプ {d.karma_chargen.metatype} / 能力値 {d.karma_chargen.attributes} / 技能 {d.karma_chargen.skills} / 知識 {d.karma_chargen.knowledge} / 専門化 {d.karma_chargen.specializations}</div>
                    <div>資質 {d.karma_chargen.qualities} / ニューエン交換 {d.karma_chargen.nuyen_karma} / その他 {d.karma_chargen.other}</div>
                  </div>
                ) : null}
              </div>
            ) : (
              <>
            <table>
              <thead>
                <tr>
                  <th></th>
                  {LETTERS.map((l) => (
                    <th key={l}>
                      {l}
                      {(ch.build_method || "Priority") === "SumToTen" ? ` (${d.sum_to_ten?.costs?.[l] ?? SUM_TO_TEN_COST[l]})` : ""}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {CATS.map((cat) => (
                  <tr key={cat.key}>
                    <td className="rowhead">{cat.label}</td>
                    {LETTERS.map((letter) => {
                      const cell = table[cat.key][letter];
                      const sumMode = (ch.build_method || "Priority") === "SumToTen";
                      const takenBy = sumMode ? undefined : CATS.find((c) => ch.priorities[c.key] === letter && c.key !== cat.key);
                      return (
                        <td key={letter}>
                          <button
                            className={`choice ${ch.priorities[cat.key] === letter ? "selected" : ""}`}
                            onClick={() => {
                              const next = { ...ch.priorities };
                              if (!sumMode && takenBy) next[takenBy.key] = next[cat.key];
                              next[cat.key] = letter;
                              const extra: Record<string, unknown> = { priorities: next };
                              if (cat.key === "Talent") {
                                const options = table.Talent[letter].talents.filter((t) => t.name !== "Mundane");
                                extra.talent =
                                  letter === "E"
                                    ? "Mundane"
                                    : options.some((t) => t.name === ch.talent)
                                      ? ch.talent
                                      : options[0]?.name || "Magician";
                              }
                              patch(extra);
                            }}
                          >
                            {cell?.name?.replace(/^[A-E]\s*-\s*/, "") || letter}
                          </button>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="muted">
              {(ch.build_method || "Priority") === "SumToTen"
                ? "同じ優先度を複数カテゴリに割り当てできます。合計がちょうど 10 になるようにしてください。"
                : "A〜E は各1回。クリックで入れ替えます。"}
            </p>
              </>
            )}
          </div>

  );
}
