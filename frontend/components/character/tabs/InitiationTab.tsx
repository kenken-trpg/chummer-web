"use client";

import type { TabPanelProps } from "@/components/character/types";

export function InitiationTab({
  catalog,
  character: ch,
  d,
  tr,
  patch,
  setCharacter,
}: TabPanelProps) {
  return (
    <div className="card">
      <p className="muted">
        等級 {d.initiation?.grade || 0}
        {" ・ "}カルマ {d.initiation?.karma || 0}
        （各等級 10 + 等級×3。集団／試練／教習は各 −10%（累積で減算）。魔力上限 = 種族上限 +
        等級。等級 ≤ MAG）
        {(d.initiation?.metamagics || []).some((m) => m.free)
          ? ` ・ 品質付与 ${(d.initiation?.metamagics || [])
              .filter((m) => m.free)
              .map((m) => m.name)
              .join("、")}`
          : ""}
      </p>
      {(d.initiation?.metamagics || []).filter((m) => m.free).length ? (
        <div className="muted" style={{ marginBottom: 8 }}>
          無料メタマジック:{" "}
          {(d.initiation?.metamagics || [])
            .filter((m) => m.free)
            .map((m) => `${tr(m.name)}${m.source_quality ? `（${tr(m.source_quality)}）` : ""}`)
            .join(" ・ ")}
        </div>
      ) : null}
      <label>
        イニシエーション等級
        <input
          type="range"
          min={0}
          max={Math.max(6, Number(d.totals.MAG || 0))}
          value={ch.initiate_grade || 0}
          onChange={(e) => {
            const grade = Number(e.target.value);
            const existing = [...(ch.initiations || [])];
            const byGrade = new Map(existing.map((row) => [row.grade, row]));
            const next = [];
            for (let g = 1; g <= grade; g += 1) {
              next.push(byGrade.get(g) || { grade: g, kind: "metamagic", option_id: "" });
            }
            setCharacter({ ...ch, initiate_grade: grade, initiations: next });
          }}
          onMouseUp={(e) => {
            const grade = Number((e.target as HTMLInputElement).value);
            const existing = [...(ch.initiations || [])];
            const byGrade = new Map(existing.map((row) => [row.grade, row]));
            const next = [];
            for (let g = 1; g <= grade; g += 1) {
              next.push(byGrade.get(g) || { grade: g, kind: "metamagic", option_id: "" });
            }
            patch({ initiate_grade: grade, initiations: next });
          }}
          onTouchEnd={(e) => {
            const grade = Number((e.target as HTMLInputElement).value);
            const existing = [...(ch.initiations || [])];
            const byGrade = new Map(existing.map((row) => [row.grade, row]));
            const next = [];
            for (let g = 1; g <= grade; g += 1) {
              next.push(byGrade.get(g) || { grade: g, kind: "metamagic", option_id: "" });
            }
            patch({ initiate_grade: grade, initiations: next });
          }}
        />
        <b style={{ marginLeft: 8 }}>{ch.initiate_grade || 0}</b>
      </label>
      <div style={{ display: "grid", gap: 12, marginTop: 12 }}>
        {(d.initiation?.choices || []).map((choice) => {
          const local = (ch.initiations || []).find((row) => row.grade === choice.grade);
          const kind = (local?.kind || choice.kind || "metamagic") as string;
          const optionId = local?.option_id || choice.option_id || "";
          const talentName = ch.talent || "";
          const canAdept = talentName === "Adept" || talentName === "Mystic Adept";
          const canMagician = talentName !== "Adept";
          const metaOptions = (catalog.metamagics || []).filter((item) => {
            if (canAdept && !canMagician) return item.adept;
            if (canMagician && !canAdept) return item.magician;
            return item.adept || item.magician;
          });
          return (
            <div className="cyber-item" key={choice.id || choice.grade}>
              <div style={{ width: "100%" }}>
                <b>等級 {choice.grade}</b>
                <div className="muted">
                  {choice.karma}カルマ{choice.name ? ` ・ ${tr(choice.name)}` : ""}
                  {choice.group || choice.ordeal || choice.schooling
                    ? `（${[choice.group && "集団", choice.ordeal && "試練", choice.schooling && "教習"].filter(Boolean).join("・")} 割引）`
                    : ""}
                </div>
                <div className="cyber-controls" style={{ marginTop: 6 }}>
                  {(
                    [
                      ["group", "集団加入"],
                      ["ordeal", "試練"],
                      ["schooling", "教習"],
                    ] as const
                  ).map(([key, label]) => (
                    <label key={key} title="各 −10%（累積で減算）">
                      <input
                        type="checkbox"
                        checked={Boolean(local?.[key] ?? choice[key])}
                        onChange={(e) => {
                          const initiations = (ch.initiations || []).map((row) =>
                            row.grade === choice.grade ? { ...row, [key]: e.target.checked } : row,
                          );
                          patch({ initiations });
                        }}
                      />
                      {label}
                    </label>
                  ))}
                </div>
                <div className="grid" style={{ marginTop: 8 }}>
                  <label>
                    種類
                    <select
                      value={kind}
                      onChange={(e) => {
                        const nextKind = e.target.value;
                        const initiations = (ch.initiations || []).map((row) =>
                          row.grade === choice.grade
                            ? { ...row, kind: nextKind, option_id: "" }
                            : row,
                        );
                        patch({ initiations });
                      }}
                    >
                      <option value="metamagic">メタマジック</option>
                      <option value="art">Art</option>
                    </select>
                  </label>
                  <label>
                    {kind === "art" ? "Art" : "メタマジック"}
                    <select
                      value={optionId}
                      onChange={(e) => {
                        const initiations = (ch.initiations || []).map((row) =>
                          row.grade === choice.grade
                            ? { ...row, kind, option_id: e.target.value }
                            : row,
                        );
                        patch({ initiations });
                      }}
                    >
                      <option value="">選択してください</option>
                      {kind === "art"
                        ? (catalog.magic_arts || []).map((item) => (
                            <option key={item.id} value={item.id}>
                              {tr(item.name)} ({item.name})
                            </option>
                          ))
                        : metaOptions.map((item) => (
                            <option key={item.id} value={item.id}>
                              {tr(item.name)} ({item.name})
                              {item.required?.length ? ` / 要 ${item.required.join(", ")}` : ""}
                            </option>
                          ))}
                    </select>
                  </label>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
