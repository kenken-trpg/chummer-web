import type { SidebarBlockProps } from "@/components/character/sidebar/types";

export function SidebarCareerEdit({ ch, career, patch, ui }: SidebarBlockProps) {
  return (
    <>
      {career && patch ? (
        <div className="career-panel">
          <div className="stat">
            <span>{ui("side.scEdit")}</span>
            <input
              type="number"
              min={0}
              aria-label={ui("side.scEdit")}
              value={ch.street_cred || 0}
              onChange={(e) => patch({ street_cred: Math.max(0, Number(e.target.value) || 0) })}
              style={{ width: 64 }}
            />
          </div>
          <div className="stat">
            <span>{ui("side.notorietyBonus")}</span>
            <input
              type="number"
              aria-label={ui("side.notorietyBonus")}
              value={ch.notoriety_bonus || 0}
              onChange={(e) => patch({ notoriety_bonus: Number(e.target.value) || 0 })}
              style={{ width: 64 }}
            />
          </div>
          <p className="muted">{ui("side.awarenessFormula")}</p>
        </div>
      ) : null}
    </>
  );
}
