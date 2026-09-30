import { HelpTip } from "@/components/help/HelpTip";
import type { SidebarBlockProps } from "@/components/character/sidebar/types";

export function SidebarBudgets({ d, ui }: SidebarBlockProps) {
  return (
    <>
      {(d.career_advancement_karma || 0) > 0 ? (
        <div className="stat">
          <span>
            <HelpTip
              label={ui("help.open", { label: ui("side.advancementKarma") })}
              lines={[{ label: ui("help.points.advancement") }]}
            >
              {ui("side.advancementKarma")}
            </HelpTip>
          </span>
          <b>{d.career_advancement_karma}K</b>
        </div>
      ) : null}
      <div className="stat">
        <span>
          <HelpTip
            label={ui("help.open", { label: ui("side.negativeKarma") })}
            lines={[
              { label: ui("help.points.negativeKarma") },
              { label: ui("help.quality.negative") },
            ]}
          >
            {ui("side.negativeKarma")}
          </HelpTip>
        </span>
        <b>
          {d.karma.negative?.used || 0}
          {d.karma.negative?.max == null ? "" : `/${d.karma.negative.max}`}
        </b>
      </div>
      <div className="stat">
        <span>
          <HelpTip
            label={ui("help.open", { label: ui("side.attrPoints") })}
            lines={[{ label: ui("help.points.attr") }]}
          >
            {ui("side.attrPoints")}
          </HelpTip>
        </span>
        <b>
          {d.points.attributes.used}/{d.points.attributes.max}
        </b>
      </div>
      <div className="stat">
        <span>
          <HelpTip
            label={ui("help.open", { label: ui("side.specialPoints") })}
            lines={[{ label: ui("help.points.special") }]}
          >
            {ui("side.specialPoints")}
          </HelpTip>
        </span>
        <b>
          {d.points.special.used}/{d.points.special.max}
        </b>
      </div>
      <div className="stat">
        <span>
          <HelpTip
            label={ui("help.open", { label: ui("side.skillPoints") })}
            lines={[{ label: ui("help.points.skills") }]}
          >
            {ui("side.skillPoints")}
          </HelpTip>
        </span>
        <b>
          {d.points.skills.used}/{d.points.skills.max}
        </b>
      </div>
      <div className="stat">
        <span>
          <HelpTip
            label={ui("help.open", { label: ui("side.knowledgePoints") })}
            lines={[{ label: ui("help.points.knowledge") }, { label: ui("help.knowledge.cost") }]}
          >
            {ui("side.knowledgePoints")}
          </HelpTip>
        </span>
        <b>
          {d.points.knowledge.used}/{d.points.knowledge.max}
        </b>
      </div>
      <div className="stat">
        <span>
          <HelpTip
            label={ui("help.open", { label: ui("side.contacts") })}
            lines={[{ label: ui("help.points.contacts") }]}
          >
            {ui("side.contacts")}
          </HelpTip>
        </span>
        <b>
          {d.contact_points?.used || 0}/{d.contact_points?.free || 0}
          {(d.contact_points?.paid || 0) > 0 ? ` +${d.contact_points?.paid}` : ""}
        </b>
      </div>
      <div className="stat">
        <span>
          <HelpTip
            label={ui("help.open", { label: ui("side.martial") })}
            lines={[
              { label: ui("help.points.martial") },
              { label: ui("help.martial.style") },
              { label: ui("help.martial.technique") },
            ]}
          >
            {ui("side.martial")}
          </HelpTip>
        </span>
        <b>
          {ui("side.martialValue", {
            styles: d.martial_art_points?.styles || 0,
            styleMax: d.martial_art_points?.style_max || 1,
            techniques: d.martial_art_points?.techniques || 0,
            techniqueMax: d.martial_art_points?.technique_max || 5,
          })}
          {(d.martial_art_points?.karma || 0) > 0 ? ` / ${d.martial_art_points?.karma}K` : ""}
        </b>
      </div>
    </>
  );
}
