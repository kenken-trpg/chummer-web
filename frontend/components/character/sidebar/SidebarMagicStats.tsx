import type { MsgKey } from "@/lib/i18n";
import type { SidebarBlockProps } from "@/components/character/sidebar/types";

/** The defence lines that are only shown when they differ from `general`.
 *  Listed by name rather than `keyof`, because `spell_defense` also carries a
 *  `decrease` map that is not a number and has no line of its own. */
const SPELL_DEFENCE: [
  MsgKey,
  "direct_mana" | "detection" | "mental_manipulation" | "mana_illusion" | "physical_illusion",
][] = [
  ["side.def.directMana", "direct_mana"],
  ["side.def.detection", "detection"],
  ["side.def.mentalManipulation", "mental_manipulation"],
  ["side.def.manaIllusion", "mana_illusion"],
  ["side.def.physicalIllusion", "physical_illusion"],
];

/** Test modifiers, shown only when non-zero. */
const TEST_MODS: [MsgKey, keyof NonNullable<SidebarBlockProps["d"]["test_mods"]>][] = [
  ["side.memory", "memory"],
  ["side.composure", "composure"],
  ["side.judge", "judge_intentions"],
  ["side.dodge", "dodge"],
  ["side.surprise", "surprise"],
];

export function SidebarMagicStats({ d, ui }: SidebarBlockProps) {
  return (
    <>
      {(d.fatigue_resist || 0) !== 0 ? (
        <div className="stat">
          <span>{ui("side.fatigueResist")}</span>
          <b>+{d.fatigue_resist}</b>
        </div>
      ) : null}
      {(d.spell_resistance || 0) !== 0 ? (
        <div className="stat">
          <span>{ui("side.spellResist")}</span>
          <b>+{d.spell_resistance}</b>
        </div>
      ) : null}
      {d.spell_defense
        ? SPELL_DEFENCE.map(([key, field]) => {
            const value = d.spell_defense![field];
            if (value === d.spell_defense!.general) return null;
            return (
              <div className="stat" key={key}>
                <span>{ui(key)}</span>
                <b>
                  {Number(value) > 0 ? "+" : ""}
                  {value}
                </b>
              </div>
            );
          })
        : null}
      {(d.action_dice_pools || []).map((row, idx) => (
        <div className="stat" key={`adp-${row.name}-${idx}`}>
          <span>{row.category ? `${row.category}: ${row.name}` : row.name}</span>
          <b>
            {row.bonus > 0 ? "+" : ""}
            {row.bonus}
          </b>
        </div>
      ))}
      {TEST_MODS.map(([key, field]) => {
        const value = d.test_mods?.[field] || 0;
        if (value === 0) return null;
        return (
          <div className="stat" key={key}>
            <span>{ui(key)}</span>
            <b>
              {value > 0 ? "+" : ""}
              {value}
            </b>
          </div>
        );
      })}
      <div className="stat">
        <span>{ui("common.essence")}</span>
        <b>
          {d.essence}
          {d.essence_lost_cyber || d.essence_lost_bio || d.essence_penalty
            ? `（C −${d.essence_lost_cyber ?? 0} / B −${d.essence_lost_bio ?? 0}${
                d.essence_penalty || 0 ? ` / ${ui("side.essenceOther")} −${d.essence_penalty}` : ""
              }）`
            : ""}
        </b>
      </div>
      {(d.cyberware_ess_multiplier || 100) !== 100 ? (
        <div className="stat">
          <span>{ui("side.cyberEss")}</span>
          <b>×{(d.cyberware_ess_multiplier || 100) / 100}</b>
        </div>
      ) : null}
      {(d.bioware_ess_multiplier || 100) !== 100 ? (
        <div className="stat">
          <span>{ui("side.bioEss")}</span>
          <b>×{(d.bioware_ess_multiplier || 100) / 100}</b>
        </div>
      ) : null}
    </>
  );
}
