import type { SidebarBlockProps } from "@/components/character/sidebar/types";

export function SidebarCareerEdit({ ch, d, career, patch, ui }: SidebarBlockProps) {
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
          <p className="muted">
            {ui("side.scFormula", {
              karma: d.karma_earned || 0,
              divisor: d.street_cred_divisor || 10,
              earned: d.street_cred_earned || 0,
              extra: ch.street_cred || 0,
              total: d.street_cred || 0,
            })}
          </p>
          {/* SR5 p.373: two points of Street Cred take one of Notoriety off */}
          <div className="option-row">
            <button
              className="btn"
              disabled={(d.street_cred || 0) < 2}
              title={ui("side.scBurnHint")}
              onClick={() => patch({ burnt_street_cred: (ch.burnt_street_cred || 0) + 2 })}
            >
              {ui("side.scBurn")}
            </button>
            {(ch.burnt_street_cred || 0) > 0 ? (
              <>
                <span className="muted">
                  {ui("side.scBurnt", { burnt: ch.burnt_street_cred || 0 })}
                </span>
                <button
                  className="btn"
                  onClick={() =>
                    patch({ burnt_street_cred: Math.max(0, (ch.burnt_street_cred || 0) - 2) })
                  }
                >
                  {ui("side.scUnburn")}
                </button>
              </>
            ) : null}
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
