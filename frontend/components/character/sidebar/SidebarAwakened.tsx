import type { SidebarBlockProps } from "@/components/character/sidebar/types";
import { formatPoints } from "@/lib/character/format";

export function SidebarAwakened({ d, tr, ui }: SidebarBlockProps) {
  return (
    <>
      {d.enabled_tabs.includes("initiation") ? (
        <div className="stat">
          <span>{ui("side.initiation")}</span>
          <b>
            {ui("side.grade", { grade: d.initiation?.grade || 0 })}
            {(d.initiation?.karma || 0) > 0 ? ` / ${d.initiation?.karma}K` : ""}
          </b>
        </div>
      ) : null}
      {d.enabled_tabs.includes("submersion") ? (
        <div className="stat">
          <span>{ui("side.submersion")}</span>
          <b>
            {ui("side.grade", { grade: d.submersion?.grade || 0 })}
            {(d.submersion?.karma || 0) > 0 ? ` / ${d.submersion?.karma}K` : ""}
          </b>
        </div>
      ) : null}
      {d.enabled_tabs.includes("adept") ? (
        <div className="stat">
          <span>{ui("side.powerPoints")}</span>
          <b>
            {formatPoints(d.power_points?.used || 0)}/{formatPoints(d.power_points?.max || 0)}
          </b>
        </div>
      ) : null}
      {d.enabled_tabs.includes("spells") ? (
        <div className="stat">
          <span>{ui("side.spells")}</span>
          <b>
            {d.spell_points?.used || 0}/{d.spell_points?.free || 0}
            {(d.spell_points?.paid || 0) > 0 ? ` +${d.spell_points?.paid}` : ""}
          </b>
        </div>
      ) : null}
      {d.enabled_tabs.includes("spirits") ? (
        <div className="stat">
          <span>{ui("side.spirits")}</span>
          <b>{d.spirits?.length || 0}</b>
        </div>
      ) : null}
      {d.enabled_tabs.includes("foci") ? (
        <div className="stat">
          <span>{ui("side.foci")}</span>
          <b>
            {d.focus_limits?.count || 0}/{d.focus_limits?.count_max || 0}
          </b>
        </div>
      ) : null}
      {d.enabled_tabs.includes("complexforms") ? (
        <div className="stat">
          <span>{ui("side.complexForms")}</span>
          <b>
            {d.complex_form_points?.used || 0}/{d.complex_form_points?.free || 0}
            {(d.complex_form_points?.paid || 0) > 0 ? ` +${d.complex_form_points?.paid}` : ""}
          </b>
        </div>
      ) : null}
      {d.enabled_tabs.includes("sprites") ? (
        <div className="stat">
          <span>{ui("side.sprites")}</span>
          <b>{d.sprites?.length || 0}</b>
        </div>
      ) : null}
      {d.living_persona ? (
        <div className="stat">
          <span>{ui("side.livingPersona")}</span>
          <b>
            DR{d.living_persona.device_rating} / {d.living_persona.attack}/{d.living_persona.sleaze}
            /{d.living_persona.dataprocessing}/{d.living_persona.firewall}
            {(d.living_persona.matrix_initiative_dice || 0) > 0
              ? ` / ${ui("side.matrixInit")}+${d.living_persona.matrix_initiative_dice}d6`
              : ""}
          </b>
        </div>
      ) : null}
      {d.tradition ? (
        <div className="stat">
          <span>{ui("side.tradition")}</span>
          <b>{tr(d.tradition.name)}</b>
        </div>
      ) : null}
      {d.needs_mentor && d.mentor ? (
        <div className="stat">
          <span>{ui("side.mentor")}</span>
          <b>{tr(d.mentor.name)}</b>
        </div>
      ) : null}
      {(d.damage_resistance || 0) > 0 ? (
        <div className="stat">
          <span>{ui("side.damageResist")}</span>
          <b>+{d.damage_resistance}</b>
        </div>
      ) : null}
      {(d.unarmed_dv || 0) > 0 ? (
        <div className="stat">
          <span>{ui("side.unarmedDv")}</span>
          <b>+{d.unarmed_dv}</b>
        </div>
      ) : null}
    </>
  );
}
