"use client";
import type { TabPanelProps } from "@/components/character/types";
import { ActiveSkills } from "./skills/ActiveSkills";
import { ExoticSkills } from "./skills/ExoticSkills";
import { GrantedSkills } from "./skills/GrantedSkills";
import { KnowledgePicker } from "./skills/KnowledgePicker";
import { KnowledgeSkills } from "./skills/KnowledgeSkills";
import { SkillGroups } from "./skills/SkillGroups";
import { skillLimits } from "./skills/shared";
import { TalentSkills } from "./skills/TalentSkills";
import { scopeTr } from "@/lib/ui-strings";

export function SkillsTab(props: TabPanelProps) {
  const { d, ui } = props;
  const { skillMax, career, splitKarma, karmaSplit } = skillLimits(props);
  // An active and a knowledge skill can share a name and not a reading:
  // Medicine is 医術 to one and 医学 to the other.
  const active = { ...props, tr: scopeTr(props.tr, "skill") };
  const knowledge = { ...props, tr: scopeTr(props.tr, "knowledge_skill") };
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
      <TalentSkills {...active} />
      <GrantedSkills {...active} />
      <SkillGroups {...active} />
      <ActiveSkills {...active} />
      <ExoticSkills {...active} />
      <KnowledgeSkills {...knowledge} />
      <KnowledgePicker {...knowledge} />
    </div>
  );
}
