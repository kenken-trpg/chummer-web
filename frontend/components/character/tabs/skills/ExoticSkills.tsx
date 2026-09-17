"use client";
import type { TabPanelProps } from "@/components/character/types";
import { HelpTip } from "@/components/help/HelpTip";
import { RangeInput } from "@/components/character/RangeInput";
import { SpecPicker } from "@/components/character/SpecPicker";
import { skillDice } from "@/lib/character/format";

type ExoticRow = { id?: string; skill_name: string; extra?: string; rating?: number };

export function ExoticSkills({
  catalog,
  character: ch,
  d,
  tr,
  ui,
  patch,
  setCharacter,
}: TabPanelProps) {
  function patchExotic(next: ExoticRow[]) {
    patch({ exotic_skills: next });
  }

  function draftExotic(id: string, next: { extra?: string; rating?: number }) {
    setCharacter({
      ...ch,
      exotic_skills: (ch.exotic_skills || []).map((row) =>
        row.id === id ? { ...row, ...next } : row,
      ),
    });
  }

  return (
    <>
      <h3>{ui("skills.exotic")}</h3>
      <p className="muted">{ui("skills.exoticNote")}</p>
      {(d.exotic_skills || []).length ? (
        (d.exotic_skills || []).map((row) => {
          const local = (ch.exotic_skills || []).find((item) => item.id === row.id);
          const extra = local?.extra ?? row.extra ?? "";
          const rating = local?.rating ?? row.rating;
          const bonus = d.skill_bonus?.[row.label] || d.skill_bonus?.[row.skill_name];
          return (
            <div className="skill-row has-spec can-delete" key={row.id}>
              <span>
                <HelpTip
                  label={ui("help.open", { label: tr(row.skill_name) })}
                  lines={[
                    { label: row.attribute },
                    ...(
                      d.skill_bonus_notes?.[row.label] ||
                      d.skill_bonus_notes?.[row.skill_name] ||
                      []
                    ).map((label) => ({ label })),
                    { label: ui("help.exotic.what") },
                    { label: ui("help.skill.pool") },
                    { label: ui("help.exotic.nodefault") },
                  ]}
                >
                  {tr(row.skill_name)}
                </HelpTip>
              </span>
              <RangeInput
                min={1}
                max={row.rating_max}
                value={rating}
                label={tr(row.skill_name)}
                title={ui("skills.ratingHint", { max: row.rating_max })}
                onDraft={(value) => draftExotic(row.id, { rating: value })}
                onCommit={(value) =>
                  patchExotic(
                    (ch.exotic_skills || []).map((item) =>
                      item.id === row.id ? { ...item, rating: value } : item,
                    ),
                  )
                }
              />
              <SpecPicker
                options={row.options || []}
                value={extra}
                emptyLabel={ui("common.target")}
                placeholder={ui("common.target")}
                tr={tr}
                onDraft={(next) => draftExotic(row.id, { extra: next })}
                onCommit={(next) => {
                  patchExotic(
                    (ch.exotic_skills || []).map((item) =>
                      item.id === row.id ? { ...item, extra: next } : item,
                    ),
                  );
                }}
              />
              <b>{skillDice(rating, bonus)}</b>
              <button
                className="btn danger"
                onClick={() =>
                  patchExotic((ch.exotic_skills || []).filter((item) => item.id !== row.id))
                }
              >
                {ui("common.delete")}
              </button>
            </div>
          );
        })
      ) : (
        <p className="muted">{ui("skills.emptyExotic")}</p>
      )}
      <div className="option-row">
        {catalog.skills.skills
          .filter((s) => s.exotic || s.name.includes("Exotic"))
          .map((s) => (
            <button
              key={s.id}
              className="btn"
              onClick={() =>
                patchExotic([
                  ...(ch.exotic_skills || []),
                  { skill_name: s.name, extra: "", rating: 1 },
                ])
              }
            >
              {ui("skills.addNamed", { name: tr(s.name) })}
            </button>
          ))}
      </div>
    </>
  );
}
