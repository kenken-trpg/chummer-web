"use client";

import type { TabPanelProps } from "@/components/character/types";

export function SubmersionTab({
  catalog,
  character: ch,
  d,
  tr,
  ui,
  patch,
  setCharacter,
}: TabPanelProps) {
  return (
    <div className="card">
      <p className="muted">
        {ui("grade.summary", {
          grade: d.submersion?.grade || 0,
          karma: d.submersion?.karma || 0,
        })}
        {ui("sub.note")}
      </p>
      <label>
        {ui("sub.grade")}
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
                <b>{ui("grade.label", { grade: choice.grade })}</b>
                <div className="muted">
                  {ui("grade.karma", { karma: choice.karma })}
                  {choice.name ? ui("grade.named", { name: tr(choice.name) }) : ""}
                  {choice.group || choice.ordeal || choice.schooling
                    ? ui("grade.discount", {
                        list: [
                          choice.group && ui("sub.net"),
                          choice.ordeal && ui("sub.task"),
                          choice.schooling && ui("init.schooling"),
                        ]
                          .filter(Boolean)
                          .join(ui("common.termSep")),
                      })
                    : ""}
                </div>
                <div className="cyber-controls" style={{ marginTop: 6 }}>
                  {(
                    [
                      ["group", "sub.network"],
                      ["ordeal", "sub.task"],
                      ["schooling", "init.schooling"],
                    ] as const
                  ).map(([key, label]) => (
                    <label key={key} title={ui("grade.discountHint")}>
                      <input
                        type="checkbox"
                        checked={Boolean(local?.[key] ?? choice[key])}
                        onChange={(e) => {
                          const submersions = (ch.submersions || []).map((row) =>
                            row.grade === choice.grade ? { ...row, [key]: e.target.checked } : row,
                          );
                          patch({ submersions });
                        }}
                      />
                      {ui(label)}
                    </label>
                  ))}
                </div>
                <div className="grid" style={{ marginTop: 8 }}>
                  <label>
                    {ui("sub.echo")}
                    <select
                      value={echoId}
                      onChange={(e) => {
                        const nextId = e.target.value;
                        const nextSpec = (catalog.echoes || []).find((item) => item.id === nextId);
                        const submersions = (ch.submersions || []).map((row) =>
                          row.grade === choice.grade
                            ? {
                                ...row,
                                echo_id: nextId,
                                extra: nextSpec?.needs_extra ? row.extra || "" : null,
                              }
                            : row,
                        );
                        patch({ submersions });
                      }}
                    >
                      <option value="">{ui("common.choose")}</option>
                      {(catalog.echoes || []).map((item) => (
                        <option key={item.id} value={item.id}>
                          {tr(item.name)} ({item.name})
                          {item.max_takes == null
                            ? ui("common.repeatable")
                            : item.max_takes > 1
                              ? ui("common.maxTakes", { max: item.max_takes })
                              : ""}
                        </option>
                      ))}
                    </select>
                  </label>
                  {selected?.needs_extra ? (
                    <label>
                      {ui("sub.target")}
                      <input
                        type="text"
                        value={extra || ""}
                        onChange={(e) => {
                          const submersions = (ch.submersions || []).map((row) =>
                            row.grade === choice.grade ? { ...row, extra: e.target.value } : row,
                          );
                          setCharacter({ ...ch, submersions });
                        }}
                        onBlur={(e) => {
                          const submersions = (ch.submersions || []).map((row) =>
                            row.grade === choice.grade ? { ...row, extra: e.target.value } : row,
                          );
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
