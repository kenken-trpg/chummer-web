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
            </span>
            <RangeInput
              min={0}
              max={groupMax}
              value={ch.skill_groups[g] || 0}
              label={trGroup(g)}
              title={ui("skills.groupHint", { group: trGroup(g), max: groupMax })}
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
            <b>{skillDice(ch.skill_groups[g] || 0, d.skill_group_bonus?.[g])}</b>
          </div>
        );
      })}
    </>
  );
}
