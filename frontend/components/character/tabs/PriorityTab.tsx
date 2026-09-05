"use client";
import type { TabPanelProps } from "@/components/character/types";
import { CATS, DEFAULT_PRIORITIES, LETTERS, SUM_TO_TEN_COST } from "@/lib/character/constants";
import { buildMethodLabel, priorityCellLabel } from "@/lib/character/priority-labels";
import { RangeInput } from "@/components/character/RangeInput";

export function PriorityTab({ catalog, character: ch, d, ui, patch, setCharacter }: TabPanelProps) {
  const table = catalog.priority_table;

  return (
    <div className="card">
      <div
        style={{
          display: "flex",
          gap: 8,
          marginBottom: 12,
          flexWrap: "wrap",
          alignItems: "center",
        }}
      >
        <button
          className={`choice ${(ch.build_method || "Priority") === "Priority" ? "selected" : ""}`}
          title={ui("prio.methodPriorityHint")}
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
          {buildMethodLabel("Priority", ui)}
        </button>
        <button
          className={`choice ${(ch.build_method || "Priority") === "SumToTen" ? "selected" : ""}`}
          title={ui("prio.methodSumHint")}
          onClick={() => patch({ build_method: "SumToTen" })}
        >
          {buildMethodLabel("SumToTen", ui)}
        </button>
        <button
          className={`choice ${(ch.build_method || "Priority") === "Karma" ? "selected" : ""}`}
          title={ui("prio.methodKarmaHint")}
          onClick={() => patch({ build_method: "Karma", talent: ch.talent || "Mundane" })}
        >
          {buildMethodLabel("Karma", ui)}
        </button>
        {(ch.build_method || "Priority") === "SumToTen" ? (
          <span className="muted">
            {ui("prio.sumTotal", {
              used: d.sum_to_ten?.used ?? 0,
              max: d.sum_to_ten?.max ?? 10,
            })}
            {" ・ "}A4 / B3 / C2 / D1 / E0
          </span>
        ) : null}
        {(ch.build_method || "Priority") === "Karma" ? (
          <span className="muted">
            {ui("common.karmaPool", { remaining: d.karma.remaining, pool: d.karma.pool })}
            {ui("prio.karmaNuyenRate", {
              rate: d.karma_chargen?.nuyen_per_karma ?? 2000,
              max: d.karma_chargen?.nuyen_karma_max ?? 235,
            })}
          </span>
        ) : (
          <span className="muted">
            {ui("prio.leftoverToNuyen", {
              max: d.karma_chargen?.nuyen_karma_max ?? d.nuyen_karma_max ?? 10,
            })}
          </span>
        )}
      </div>
      {(ch.build_method || "Priority") !== "Karma" ? (
        <label style={{ display: "block", marginBottom: 12 }}>
          {ui("prio.leftoverSlider", {
            k: ch.karma_nuyen || 0,
            nuyen: (
              (ch.karma_nuyen || 0) * (d.karma_chargen?.nuyen_per_karma || 2000)
            ).toLocaleString(),
          })}
          <RangeInput
            min={0}
            max={d.karma_chargen?.nuyen_karma_max ?? d.nuyen_karma_max ?? 10}
            value={ch.karma_nuyen || 0}
            label={ui("prio.leftoverSliderLabel")}
            title={ui("prio.nuyenSliderHint", {
              rate: (d.karma_chargen?.nuyen_per_karma || 2000).toLocaleString(),
            })}
            onDraft={(value) => setCharacter({ ...ch, karma_nuyen: value })}
            onCommit={(value) => patch({ karma_nuyen: value })}
          />
        </label>
      ) : null}
      {(ch.build_method || "Priority") === "Karma" ? (
        <div style={{ display: "grid", gap: 12 }}>
          <p className="muted">{ui("prio.karmaNote", { pool: d.karma.pool })}</p>
          <label>
            {ui("prio.talent")}
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
            {ui("prio.karmaSlider", {
              k: ch.karma_nuyen || 0,
              nuyen: (
                (ch.karma_nuyen || 0) * (d.karma_chargen?.nuyen_per_karma || 2000)
              ).toLocaleString(),
            })}
            <RangeInput
              min={0}
              max={d.karma_chargen?.nuyen_karma_max ?? 235}
              value={ch.karma_nuyen || 0}
              label={ui("prio.karmaSliderLabel")}
              title={ui("prio.nuyenSliderHint", {
                rate: (d.karma_chargen?.nuyen_per_karma || 2000).toLocaleString(),
              })}
              onDraft={(value) => setCharacter({ ...ch, karma_nuyen: value })}
              onCommit={(value) => patch({ karma_nuyen: value })}
            />
          </label>
          {d.karma_chargen ? (
            <div className="muted" style={{ display: "grid", gap: 4 }}>
              <div>
                {ui("prio.breakdownA", {
                  meta: d.karma_chargen.metatype,
                  attrs: d.karma_chargen.attributes,
                  skills: d.karma_chargen.skills,
                  knowledge: d.karma_chargen.knowledge,
                  specs: d.karma_chargen.specializations,
                })}
              </div>
              <div>
                {ui("prio.breakdownB", {
                  qualities: d.karma_chargen.qualities,
                  nuyenKarma: d.karma_chargen.nuyen_karma,
                  other: d.karma_chargen.other,
                })}
              </div>
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
                    {(ch.build_method || "Priority") === "SumToTen"
                      ? ` (${d.sum_to_ten?.costs?.[l] ?? SUM_TO_TEN_COST[l]})`
                      : ""}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {CATS.map((cat) => (
                <tr key={cat.key}>
                  <td className="rowhead">{ui(cat.label)}</td>
                  {LETTERS.map((letter) => {
                    const cell = table[cat.key][letter];
                    const sumMode = (ch.build_method || "Priority") === "SumToTen";
                    const takenBy = sumMode
                      ? undefined
                      : CATS.find((c) => ch.priorities[c.key] === letter && c.key !== cat.key);
                    return (
                      <td key={letter}>
                        <button
                          className={`choice ${ch.priorities[cat.key] === letter ? "selected" : ""}`}
                          // the cell shows only the tier's name ("24"、"Human")
                          // — say which row it belongs to and, in Priority
                          // mode, which category it would displace
                          title={
                            takenBy
                              ? ui("prio.cellSwapHint", {
                                  cat: ui(cat.label),
                                  letter,
                                  other: ui(takenBy.label),
                                })
                              : ui("prio.cellHint", { cat: ui(cat.label), letter })
                          }
                          onClick={() => {
                            const next = { ...ch.priorities };
                            if (!sumMode && takenBy) next[takenBy.key] = next[cat.key];
                            next[cat.key] = letter;
                            const extra: Record<string, unknown> = { priorities: next };
                            if (cat.key === "Talent") {
                              const options = table.Talent[letter].talents.filter(
                                (t) => t.name !== "Mundane",
                              );
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
                          {cell?.name
                            ? priorityCellLabel(cell.name.replace(/^[A-E]\s*-\s*/, ""), ui)
                            : letter}
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
              ? ui("prio.sumHint")
              : ui("prio.priorityHint")}
          </p>
        </>
      )}
    </div>
  );
}
