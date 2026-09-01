import type { SidebarBlockProps } from "@/components/character/sidebar/types";

export function SidebarBudgets({ d }: SidebarBlockProps) {
  return (
    <>
      {(d.career_advancement_karma || 0) > 0 ? (
        <div className="stat">
          <span>成長カルマ</span>
          <b>{d.career_advancement_karma}K</b>
        </div>
      ) : null}
      <div className="stat">
        <span>不利カルマ</span>
        <b>
          {d.karma.negative?.used || 0}
          {d.karma.negative?.max == null ? "" : `/${d.karma.negative.max}`}
        </b>
      </div>
      <div className="stat">
        <span>能力値点</span>
        <b>
          {d.points.attributes.used}/{d.points.attributes.max}
        </b>
      </div>
      <div className="stat">
        <span>特殊点</span>
        <b>
          {d.points.special.used}/{d.points.special.max}
        </b>
      </div>
      <div className="stat">
        <span>技能点</span>
        <b>
          {d.points.skills.used}/{d.points.skills.max}
        </b>
      </div>
      <div className="stat">
        <span>知識点</span>
        <b>
          {d.points.knowledge.used}/{d.points.knowledge.max}
        </b>
      </div>
      <div className="stat">
        <span>コンタクト</span>
        <b>
          {d.contact_points?.used || 0}/{d.contact_points?.free || 0}
          {(d.contact_points?.paid || 0) > 0 ? ` +${d.contact_points?.paid}` : ""}
        </b>
      </div>
      <div className="stat">
        <span>武道</span>
        <b>
          {d.martial_art_points?.styles || 0}/{d.martial_art_points?.style_max || 1}流派 ・{" "}
          {d.martial_art_points?.techniques || 0}/{d.martial_art_points?.technique_max || 5}技
          {(d.martial_art_points?.karma || 0) > 0 ? ` / ${d.martial_art_points?.karma}K` : ""}
        </b>
      </div>
    </>
  );
}
