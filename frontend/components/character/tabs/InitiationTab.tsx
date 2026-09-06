"use client";

import { RangeInput } from "@/components/character/RangeInput";
import { withOriginal } from "@/lib/character/format";
import type { TabPanelProps } from "@/components/character/types";

export function InitiationTab({
  catalog,
  character: ch,
  d,
  tr,
  ui,
  patch,
  setCharacter,
}: TabPanelProps) {
  /** One row per grade, keeping whatever the user already chose for the
   *  grades that survive the change. */
  function gradeRows(grade: number) {
    const byGrade = new Map((ch.initiations || []).map((row) => [row.grade, row]));
    const next = [];
    for (let g = 1; g <= grade; g += 1) {
      next.push(byGrade.get(g) || { grade: g, kind: "metamagic", option_id: "" });
    }
    return next;
  }

  return (
    <div className="card">
      <p className="muted">
        {ui("grade.summary", {
          grade: d.initiation?.grade || 0,
          karma: d.initiation?.karma || 0,
        })}
        {ui("init.note")}
        {(d.initiation?.metamagics || []).some((m) => m.free)
          ? ui("init.granted", {
              list: (d.initiation?.metamagics || [])
                .filter((m) => m.free)
                .map((m) => m.name)
                .join(ui("common.listSep")),
            })
          : ""}
      </p>
      {(d.initiation?.metamagics || []).filter((m) => m.free).length ? (
        <div className="muted" style={{ marginBottom: 8 }}>
          {ui("init.freeMetamagics", {
            list: (d.initiation?.metamagics || [])
              .filter((m) => m.free)
              .map((m) => `${tr(m.name)}${m.source_quality ? `（${tr(m.source_quality)}）` : ""}`)
              .join(` ${ui("common.termSep")} `),
          })}
        </div>
      ) : null}
      <label>
        {ui("init.grade")}
        <RangeInput
          min={0}
          max={Math.max(6, Number(d.totals.MAG || 0))}
          value={ch.initiate_grade || 0}
          label={ui("init.grade")}
          title={ui("init.gradeHint")}
          onDraft={(grade) =>
            setCharacter({ ...ch, initiate_grade: grade, initiations: gradeRows(grade) })
          }
          onCommit={(grade) => patch({ initiate_grade: grade, initiations: gradeRows(grade) })}
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
                <b>{ui("grade.label", { grade: choice.grade })}</b>
                <div className="muted">
                  {ui("grade.karma", { karma: choice.karma })}
                  {choice.name ? ui("grade.named", { name: tr(choice.name) }) : ""}
                  {choice.group || choice.ordeal || choice.schooling
                    ? ui("grade.discount", {
                        list: [
                          choice.group && ui("init.group"),
                          choice.ordeal && ui("init.ordeal"),
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
                      ["group", "init.groupJoin"],
                      ["ordeal", "init.ordeal"],
                      ["schooling", "init.schooling"],
                    ] as const
                  ).map(([key, label]) => (
                    <label key={key} title={ui("grade.discountHint")}>
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
                      {ui(label)}
                    </label>
                  ))}
                </div>
                <div className="grid" style={{ marginTop: 8 }}>
                  <label>
                    {ui("common.kind")}
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
                      <option value="metamagic">{ui("init.metamagic")}</option>
                      <option value="art">Art</option>
                    </select>
                  </label>
                  <label>
                    {kind === "art" ? "Art" : ui("init.metamagic")}
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
                      <option value="">{ui("common.choose")}</option>
                      {kind === "art"
                        ? (catalog.magic_arts || []).map((item) => (
                            <option key={item.id} value={item.id}>
                              {withOriginal(item.name, tr)}
                            </option>
                          ))
                        : metaOptions.map((item) => (
                            <option key={item.id} value={item.id}>
                              {withOriginal(item.name, tr)}
                              {item.required?.length
                                ? ui("init.requires", { list: item.required.join(", ") })
                                : ""}
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
