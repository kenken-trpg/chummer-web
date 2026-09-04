import type { SidebarBlockProps } from "@/components/character/sidebar/types";

export function SidebarBudgets({ d, ui }: SidebarBlockProps) {
  return (
    <>
      {(d.career_advancement_karma || 0) > 0 ? (
        <div className="stat">
          <span>{ui("side.advancementKarma")}</span>
          <b>{d.career_advancement_karma}K</b>
        </div>
      ) : null}
      <div className="stat">
        <span>{ui("side.negativeKarma")}</span>
        <b>
          {d.karma.negative?.used || 0}
          {d.karma.negative?.max == null ? "" : `/${d.karma.negative.max}`}
        </b>
      </div>
      <div className="stat">
        <span>{ui("side.attrPoints")}</span>
        <b>
          {d.points.attributes.used}/{d.points.attributes.max}
        </b>
      </div>
      <div className="stat">
        <span>{ui("side.specialPoints")}</span>
        <b>
          {d.points.special.used}/{d.points.special.max}
        </b>
      </div>
      <div className="stat">
        <span>{ui("side.skillPoints")}</span>
        <b>
          {d.points.skills.used}/{d.points.skills.max}
        </b>
      </div>
      <div className="stat">
        <span>{ui("side.knowledgePoints")}</span>
        <b>
          {d.points.knowledge.used}/{d.points.knowledge.max}
        </b>
      </div>
      <div className="stat">
        <span>{ui("side.contacts")}</span>
        <b>
          {d.contact_points?.used || 0}/{d.contact_points?.free || 0}
          {(d.contact_points?.paid || 0) > 0 ? ` +${d.contact_points?.paid}` : ""}
        </b>
      </div>
      <div className="stat">
        <span>{ui("side.martial")}</span>
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
