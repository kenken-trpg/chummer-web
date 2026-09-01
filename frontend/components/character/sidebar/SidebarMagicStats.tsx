import type { SidebarBlockProps } from "@/components/character/sidebar/types";

export function SidebarMagicStats({ d }: SidebarBlockProps) {
  return (
    <>
      {(d.fatigue_resist || 0) !== 0 ? (
        <div className="stat">
          <span>疲労抵抗</span>
          <b>+{d.fatigue_resist}</b>
        </div>
      ) : null}
      {(d.spell_resistance || 0) !== 0 ? (
        <div className="stat">
          <span>呪文抵抗</span>
          <b>+{d.spell_resistance}</b>
        </div>
      ) : null}
      {d.spell_defense &&
        [
          ["直接マナ", d.spell_defense.direct_mana],
          ["探知", d.spell_defense.detection],
          ["精神操作", d.spell_defense.mental_manipulation],
          ["マナ幻影", d.spell_defense.mana_illusion],
          ["物理幻影", d.spell_defense.physical_illusion],
        ].map(([label, value]) =>
          value !== d.spell_defense!.general ? (
            <div className="stat" key={label}>
              <span>{label}</span>
              <b>
                {Number(value) > 0 ? "+" : ""}
                {value}
              </b>
            </div>
          ) : null,
        )}
      {(d.action_dice_pools || []).map((row, idx) => (
        <div className="stat" key={`adp-${row.name}-${idx}`}>
          <span>{row.category ? `${row.category}: ${row.name}` : row.name}</span>
          <b>
            {row.bonus > 0 ? "+" : ""}
            {row.bonus}
          </b>
        </div>
      ))}
      {(d.test_mods?.memory || 0) !== 0 ? (
        <div className="stat">
          <span>記憶</span>
          <b>
            {d.test_mods!.memory! > 0 ? "+" : ""}
            {d.test_mods!.memory}
          </b>
        </div>
      ) : null}
      {(d.test_mods?.composure || 0) !== 0 ? (
        <div className="stat">
          <span>冷静</span>
          <b>
            {d.test_mods!.composure! > 0 ? "+" : ""}
            {d.test_mods!.composure}
          </b>
        </div>
      ) : null}
      {(d.test_mods?.judge_intentions || 0) !== 0 ? (
        <div className="stat">
          <span>意図看破</span>
          <b>
            {d.test_mods!.judge_intentions! > 0 ? "+" : ""}
            {d.test_mods!.judge_intentions}
          </b>
        </div>
      ) : null}
      {(d.test_mods?.dodge || 0) !== 0 ? (
        <div className="stat">
          <span>回避</span>
          <b>
            {d.test_mods!.dodge! > 0 ? "+" : ""}
            {d.test_mods!.dodge}
          </b>
        </div>
      ) : null}
      {(d.test_mods?.surprise || 0) !== 0 ? (
        <div className="stat">
          <span>奇襲</span>
          <b>
            {d.test_mods!.surprise! > 0 ? "+" : ""}
            {d.test_mods!.surprise}
          </b>
        </div>
      ) : null}
      <div className="stat">
        <span>エッセンス</span>
        <b>
          {d.essence}
          {d.essence_lost_cyber || d.essence_lost_bio || d.essence_penalty
            ? `（C −${d.essence_lost_cyber ?? 0} / B −${d.essence_lost_bio ?? 0}${d.essence_penalty || 0 ? ` / その他 −${d.essence_penalty}` : ""}）`
            : ""}
        </b>
      </div>
      {(d.cyberware_ess_multiplier || 100) !== 100 ? (
        <div className="stat">
          <span>サイバーESS</span>
          <b>×{(d.cyberware_ess_multiplier || 100) / 100}</b>
        </div>
      ) : null}
      {(d.bioware_ess_multiplier || 100) !== 100 ? (
        <div className="stat">
          <span>バイオESS</span>
          <b>×{(d.bioware_ess_multiplier || 100) / 100}</b>
        </div>
      ) : null}
    </>
  );
}
