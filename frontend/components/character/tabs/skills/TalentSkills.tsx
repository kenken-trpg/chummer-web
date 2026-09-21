"use client";
import type { TabPanelProps } from "@/components/character/types";

/** The skills the priority talent hands out at a fixed rating: a Magician's
 *  two magical skills, a Technomancer's three, an Adept's one, an Aspected
 *  Magician's group. The engine raises each pick to that rating and leaves
 *  the free levels out of the points, so all a player does here is name them.
 *
 *  Changing a pick takes the free levels back off the old one, the way
 *  Chummer drops its `FreeBase`; points bought on top of them stay. */
export function TalentSkills({ character: ch, d, tr, ui, patch }: TabPanelProps) {
  const talent = d.talent_skills;
  if (!talent || !talent.qty || !talent.rating) return null;
  const picked = talent.picked;
  const onPick = (index: number, name: string) => {
    const next = Array.from({ length: talent.qty }, (_, i) => picked[i] || "");
    const old = next[index];
    next[index] = name;
    const ratings = { ...((talent.group ? ch.skill_groups : ch.skills) || {}) };
    if (old && old !== name) {
      const left = (ratings[old] || 0) - talent.rating;
      if (left > 0) ratings[old] = left;
      else delete ratings[old];
    }
    patch({
      talent_skills: next.filter(Boolean),
      [talent.group ? "skill_groups" : "skills"]: ratings,
    });
  };
  return (
    <>
      <h3>
        {ui(talent.group ? "skills.talentGroup" : "skills.talent", {
          qty: talent.qty,
          rating: talent.rating,
        })}
      </h3>
      <div className="skill-picks">
        {Array.from({ length: talent.qty }, (_, i) => {
          const current = picked[i] || "";
          const taken = new Set(picked.filter((name) => name !== current));
          return (
            <label key={i}>
              {ui("skills.talentPick", { n: i + 1 })}
              <select value={current} onChange={(e) => onPick(i, e.target.value)}>
                <option value="">{ui("common.choose")}</option>
                {talent.options
                  .filter((name) => !taken.has(name))
                  .map((name) => (
                    <option key={name} value={name}>
                      {tr(name)}
                    </option>
                  ))}
              </select>
            </label>
          );
        })}
      </div>
    </>
  );
}
