import type { SidebarBlockProps } from "@/components/character/sidebar/types";
import { formatPoints } from "@/lib/character/format";

export function SidebarAwakened({ d, tr }: SidebarBlockProps) {
  return (
    <>
      {d.enabled_tabs.includes("initiation") ? (
        <div className="stat">
          <span>イニシエーション</span>
          <b>
            等級 {d.initiation?.grade || 0}
            {(d.initiation?.karma || 0) > 0 ? ` / ${d.initiation?.karma}K` : ""}
          </b>
        </div>
      ) : null}
      {d.enabled_tabs.includes("submersion") ? (
        <div className="stat">
          <span>サブマージョン</span>
          <b>
            等級 {d.submersion?.grade || 0}
            {(d.submersion?.karma || 0) > 0 ? ` / ${d.submersion?.karma}K` : ""}
          </b>
        </div>
      ) : null}
      {d.enabled_tabs.includes("adept") ? (
        <div className="stat">
          <span>パワー点</span>
          <b>
            {formatPoints(d.power_points?.used || 0)}/{formatPoints(d.power_points?.max || 0)}
          </b>
        </div>
      ) : null}
      {d.enabled_tabs.includes("spells") ? (
        <div className="stat">
          <span>術式</span>
          <b>
            {d.spell_points?.used || 0}/{d.spell_points?.free || 0}
            {(d.spell_points?.paid || 0) > 0 ? ` +${d.spell_points?.paid}` : ""}
          </b>
        </div>
      ) : null}
      {d.enabled_tabs.includes("spirits") ? (
        <div className="stat">
          <span>精霊</span>
          <b>{d.spirits?.length || 0}</b>
        </div>
      ) : null}
      {d.enabled_tabs.includes("foci") ? (
        <div className="stat">
          <span>フォーカス</span>
          <b>
            {d.focus_limits?.count || 0}/{d.focus_limits?.count_max || 0}
          </b>
        </div>
      ) : null}
      {d.enabled_tabs.includes("complexforms") ? (
        <div className="stat">
          <span>複合体</span>
          <b>
            {d.complex_form_points?.used || 0}/{d.complex_form_points?.free || 0}
            {(d.complex_form_points?.paid || 0) > 0 ? ` +${d.complex_form_points?.paid}` : ""}
          </b>
        </div>
      ) : null}
      {d.enabled_tabs.includes("sprites") ? (
        <div className="stat">
          <span>スプライト</span>
          <b>{d.sprites?.length || 0}</b>
        </div>
      ) : null}
      {d.living_persona ? (
        <div className="stat">
          <span>リビングペルソナ</span>
          <b>
            DR{d.living_persona.device_rating} / {d.living_persona.attack}/{d.living_persona.sleaze}
            /{d.living_persona.dataprocessing}/{d.living_persona.firewall}
            {(d.living_persona.matrix_initiative_dice || 0) > 0
              ? ` / マトリクスInit+${d.living_persona.matrix_initiative_dice}d6`
              : ""}
          </b>
        </div>
      ) : null}
      {d.tradition ? (
        <div className="stat">
          <span>伝統</span>
          <b>{tr(d.tradition.name)}</b>
        </div>
      ) : null}
      {d.needs_mentor && d.mentor ? (
        <div className="stat">
          <span>メンター</span>
          <b>{tr(d.mentor.name)}</b>
        </div>
      ) : null}
      {(d.damage_resistance || 0) > 0 ? (
        <div className="stat">
          <span>ダメージ抵抗</span>
          <b>+{d.damage_resistance}</b>
        </div>
      ) : null}
      {(d.unarmed_dv || 0) > 0 ? (
        <div className="stat">
          <span>非武装DV</span>
          <b>+{d.unarmed_dv}</b>
        </div>
      ) : null}
    </>
  );
}
