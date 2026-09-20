"use client";
import { SkillPickSelects } from "@/components/character/SkillPickSelects";
import type { TabPanelProps } from "@/components/character/types";
import type { SkillPickSlot } from "@/lib/types";

/** Every skill the character does not buy but has to *name*, gathered on the
 *  tab where a player goes looking for a skill.
 *
 *  Each of these already has a control next to whatever grants it — the
 *  quality on the qualities tab, the ware on its own tab, the adept power on
 *  the adept tab, the mentor's inside its picker. That is the right place to
 *  change one, and the wrong place
 *  to *find* one: nothing on the skills tab said the pick existed, so a
 *  power's skill was a pick you had to know about before you could make it.
 *  The same selects are repeated here, each labelled with what it comes from. */
export function GrantedSkills({ character: ch, d, tr, ui, patch }: TabPanelProps) {
  const powerSlots: SkillPickSlot[] = (d.adept_powers || [])
    .filter((power) => power.select === "skill" && !power.free_only)
    .map((power) => ({
      key: `power:${power.id}`,
      source: power.name,
      source_kind: "power",
      source_id: power.id,
      picked: power.extra || "",
      options: power.options,
      bonus: 0,
      max: 0,
      rating: 0,
      knowledgeskills: false,
    }));
  // A mentor's choice may grant a power that asks for a skill of its own, once
  // the choice's own select is spent on *which* power it grants. `selected` is
  // the engine's answer, so an offered-but-untaken choice asks for nothing.
  const mentorSlots: SkillPickSlot[] = (d.mentor?.choices || [])
    .filter((choice) => choice.selected)
    .flatMap((choice) =>
      (choice.power_targets || [])
        .filter((target) => target.kind === "skill")
        .map((target) => ({
          key: `mentor:${target.key}`,
          source: target.power,
          source_kind: "mentor",
          source_id: target.key,
          picked: target.extra || "",
          options: target.options,
          bonus: 0,
          max: 0,
          rating: 0,
          knowledgeskills: false,
        })),
    );
  const slots = [...(d.skill_pick_slots || []), ...powerSlots, ...mentorSlots];
  if (!slots.length) return null;
  return (
    <>
      <h3>{ui("skills.granted")}</h3>
      <p className="muted">{ui("skills.grantedNote")}</p>
      <SkillPickSelects
        slots={slots}
        tr={tr}
        onPick={(key, skill) => {
          const mentorKey = key.startsWith("mentor:") ? key.slice("mentor:".length) : "";
          if (mentorKey) {
            patch({ mentor_extras: { ...(ch.mentor_extras || {}), [mentorKey]: skill } });
            return;
          }
          const powerId = key.startsWith("power:") ? key.slice("power:".length) : "";
          if (powerId) {
            patch({
              adept_powers: (ch.adept_powers || []).map((row) =>
                row.id === powerId ? { ...row, extra: skill } : row,
              ),
            });
            return;
          }
          patch({ skill_picks: { ...(ch.skill_picks || {}), [key]: skill } });
        }}
      />
    </>
  );
}
