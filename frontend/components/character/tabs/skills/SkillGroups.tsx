"use client";
import type { TabPanelProps } from "@/components/character/types";
import { RangeInput } from "@/components/character/RangeInput";
import { skillDice } from "@/lib/character/format";
import { skillLimits } from "./shared";

export function SkillGroups(props: TabPanelProps) {
  const { catalog, character: ch, d, trGroup, ui, patch, setCharacter } = props;
  const { groupMax } = skillLimits(props);
  return (
    <>
      <h3>{ui("skills.groups")}</h3>
      {catalog.skills.groups.map((g) => (
        <div className="skill-row" key={g}>
          <span title={ui("skills.groupHint", { group: trGroup(g), max: groupMax })}>
            {trGroup(g)}
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
          <b>{skillDice(ch.skill_groups[g] || 0, d.skill_group_bonus?.[g])}</b>
        </div>
      ))}
    </>
  );
}
