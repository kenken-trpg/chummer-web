"use client";
import type { TabPanelProps } from "@/components/character/types";
import { HelpTip } from "@/components/help/HelpTip";
import { RangeInput } from "@/components/character/RangeInput";
import { skillDice } from "@/lib/character/format";
import { KarmaLevels, skillLimits } from "./shared";

export function SkillGroups(props: TabPanelProps) {
  const { catalog, character: ch, d, tr, trGroup, ui, patch, setCharacter } = props;
  const { groupMax, splitKarma, karmaSplit } = skillLimits(props);
  return (
    <>
      <h3>{ui("skills.groups")}</h3>
      {catalog.skills.groups.map((g) => {
        const members = catalog.skills.skills
          .filter((s) => s.skillgroup === g)
          .map((s) => tr(s.name));
        const lifeGroup = d.life_module_skills?.groups.find((item) => item.name === g);
        const unequal = !!lifeGroup && !lifeGroup.uniform;
        return (
          <div className={splitKarma ? "skill-row has-karma" : "skill-row"} key={g}>
            <span>
              <HelpTip
                label={ui("help.open", { label: trGroup(g) })}
                lines={[
                  { label: ui("skills.groupHint", { group: trGroup(g), max: groupMax }) },
                  ...(members.length
                    ? [
                        {
                          label: ui("help.group.members", {
                            skills: members.join(ui("help.group.sep")),
                          }),
                        },
                      ]
                    : []),
                  { label: ui("help.group.cost") },
                  { label: ui("help.group.break") },
                ]}
              >
                {trGroup(g)}
              </HelpTip>
              {unequal && <small>{ui("life.groupUnequal")}</small>}
              {unequal && (ch.skill_groups[g] || 0) > 0 && (
                <button
                  disabled={d.life_module_skills?.frozen}
                  onClick={() => {
                    const skills = { ...ch.skills };
                    for (const skill of catalog.skills.skills.filter((s) => s.skillgroup === g))
                      skills[skill.name] = Math.max(
                        skills[skill.name] || 0,
                        ch.skill_groups[g] || 0,
                      );
                    patch({ skills, skill_groups: { ...ch.skill_groups, [g]: 0 } });
                  }}
                >
                  {ui("life.groupConvert")}
                </button>
              )}
            </span>
            <RangeInput
              min={0}
              max={Math.max(0, groupMax - (lifeGroup?.free_uniform_rating || 0))}
              disabled={unequal || d.life_module_skills?.frozen}
              value={ch.skill_groups[g] || 0}
              label={trGroup(g)}
              onDraft={(value) =>
                setCharacter({ ...ch, skill_groups: { ...ch.skill_groups, [g]: value } })
              }
              onCommit={(value) => patch({ skill_groups: { ...ch.skill_groups, [g]: value } })}
            />
            <KarmaLevels
              name={g}
              rating={ch.skill_groups[g] || 0}
              levels={karmaSplit?.group_levels}
              field="skill_group_karma"
              props={props}
              label={trGroup(g)}
            />
            <b>
              {d.life_module_skills?.frozen
                ? (() => {
                    const ratings = catalog.skills.skills
                      .filter((s) => s.skillgroup === g)
                      .map((s) => d.skill_totals[s.name] || 0);
                    return new Set(ratings).size === 1
                      ? skillDice(ratings[0], d.skill_group_bonus?.[g])
                      : "—";
                  })()
                : skillDice(ch.skill_groups[g] || 0, d.skill_group_bonus?.[g])}
            </b>
          </div>
        );
      })}
    </>
  );
}
