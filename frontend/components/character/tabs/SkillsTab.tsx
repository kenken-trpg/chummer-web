"use client";
import type { TabPanelProps } from "@/components/character/types";
import { ActiveSkills } from "./skills/ActiveSkills";
import { ExoticSkills } from "./skills/ExoticSkills";
import { KnowledgePicker } from "./skills/KnowledgePicker";
import { KnowledgeSkills } from "./skills/KnowledgeSkills";
import { SkillGroups } from "./skills/SkillGroups";
import { skillLimits } from "./skills/shared";

export function SkillsTab(props: TabPanelProps) {
  const { d, ui } = props;
  const { skillMax, career, splitKarma, karmaSplit } = skillLimits(props);
  return (
    <div className="card">
      <p className="muted">
        {ui("skills.points", {
          skills: `${d.points.skills.used}/${d.points.skills.max}`,
          groups: `${d.points.skill_groups.used}/${d.points.skill_groups.max}`,
          knowledge: `${d.points.knowledge.used}/${d.points.knowledge.max}`,
        })}
        {career ? ui("skills.careerNote", { max: skillMax }) : ui("skills.chargenNote")}
      </p>
      {splitKarma && karmaSplit && karmaSplit.karma + karmaSplit.knowledge_karma > 0 ? (
        <p className="muted">
          {ui("skills.karmaSpent", {
            karma: karmaSplit.karma,
            knowledge: karmaSplit.knowledge_karma,
          })}
        </p>
      ) : null}
      <SkillGroups {...props} />
      <ActiveSkills {...props} />
      <ExoticSkills {...props} />
      <KnowledgeSkills {...props} />
      <KnowledgePicker {...props} />
    </div>
  );
}
