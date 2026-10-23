"use client";
import type { TabPanelProps } from "@/components/character/types";
import { HelpTip } from "@/components/help/HelpTip";
import { RangeInput } from "@/components/character/RangeInput";
import { SpecPicker } from "@/components/character/SpecPicker";
import { skillDice } from "@/lib/character/format";
import { editRow } from "@/lib/character/rows";

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
      exotic_skills: editRow(ch.exotic_skills, id, next),
    });
  }

  function lifeRatingRows(row: ExoticRow, value: number): ExoticRow[] {
    const same = (item: ExoticRow) =>
      item.skill_name === row.skill_name &&
      (item.extra || "").toLowerCase() === (row.extra || "").toLowerCase();
    const current = (ch.exotic_skills || []).find(same);
    const others = (ch.exotic_skills || []).filter((item) => !same(item));
    return value > 0
      ? [
          ...others,
          {
            id: current?.id || crypto.randomUUID(),
            skill_name: row.skill_name,
            extra: row.extra,
            rating: value,
          },
        ]
      : others;
  }

  return (
    <>
      <h3>{ui("skills.exotic")}</h3>
      <p className="muted">{ui("skills.exoticNote")}</p>
      {(d.exotic_skills || []).length ? (
        (d.exotic_skills || []).map((row) => {
          const local = (ch.exotic_skills || []).find(
            (item) =>
              item.id === row.id ||
              (item.skill_name === row.skill_name &&
                (item.extra || "").toLowerCase() === row.extra.toLowerCase()),
          );
          const skillId = catalog.skills.skills.find((s) => s.name === row.skill_name)?.id;
          const free =
            d.life_module_skills?.free_active[`exotic:${skillId}:${row.extra.toLowerCase()}`] || 0;
          const extra = local?.extra ?? row.extra ?? "";
          const rating = d.life_module_skills ? local?.rating || 0 : (local?.rating ?? row.rating);
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
                    { label: ui("skills.ratingHint", { max: row.rating_max }) },
                  ]}
                >
                  {tr(row.skill_name)}
                </HelpTip>
              </span>
              <RangeInput
                min={free ? 0 : 1}
                max={Math.max(0, row.rating_max - free)}
                disabled={d.life_module_skills?.frozen}
                value={rating}
                label={tr(row.skill_name)}
                onDraft={(value) =>
                  d.life_module_skills
                    ? setCharacter({ ...ch, exotic_skills: lifeRatingRows(row, value) })
                    : draftExotic(row.id, { rating: value })
                }
                onCommit={(value) =>
                  patchExotic(
                    d.life_module_skills
                      ? lifeRatingRows(row, value)
                      : (ch.exotic_skills || []).map((item) =>
                          item.id === row.id ? { ...item, rating: value } : item,
                        ),
                  )
                }
              />
              <SpecPicker
                disabled={!!free || d.life_module_skills?.frozen}
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
              <b>{skillDice(d.life_module_skills ? row.rating : rating, bonus)}</b>
              <button
                className="btn danger"
                disabled={d.life_module_skills?.frozen || (!!free && !local)}
                onClick={() =>
                  patchExotic(
                    (ch.exotic_skills || []).filter((item) => item.id !== (local?.id || row.id)),
                  )
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
              disabled={d.life_module_skills?.frozen}
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
