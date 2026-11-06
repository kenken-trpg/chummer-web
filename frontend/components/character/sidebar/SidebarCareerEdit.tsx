import { HelpTip } from "@/components/help/HelpTip";
import { BoundedNumberInput } from "@/components/character/BoundedNumberInput";
import type { SidebarBlockProps } from "@/components/character/sidebar/types";

export function SidebarCareerEdit({ ch, d, career, patch, ui }: SidebarBlockProps) {
  return (
    <>
      {career && patch ? (
        <div className="career-panel">
          <div className="stat">
            <span>
              <HelpTip
                label={ui("help.open", { label: ui("side.scEdit") })}
                lines={[{ label: ui("help.career.edit") }]}
              >
                {ui("side.scEdit")}
              </HelpTip>
            </span>
            <BoundedNumberInput
              min={0}
              aria-label={ui("side.scEdit")}
              value={ch.street_cred || 0}
              onCommit={(n) => patch({ street_cred: n })}
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
            <HelpTip
              label={ui("help.open", { label: ui("side.scBurn") })}
              lines={[{ label: ui("help.side.scBurn") }]}
            >
              <button
                className="btn"
                disabled={(d.street_cred || 0) < 2}
                onClick={() => patch({ burnt_street_cred: (ch.burnt_street_cred || 0) + 2 })}
              >
                {ui("side.scBurn")}
              </button>
            </HelpTip>
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
            <span>
              <HelpTip
                label={ui("help.open", { label: ui("side.notorietyBonus") })}
                lines={[{ label: ui("help.career.edit") }]}
              >
                {ui("side.notorietyBonus")}
              </HelpTip>
            </span>
            <BoundedNumberInput
              min={-999}
              aria-label={ui("side.notorietyBonus")}
              value={ch.notoriety_bonus || 0}
              onCommit={(n) => patch({ notoriety_bonus: n })}
              style={{ width: 64 }}
            />
          </div>
          <div className="stat">
            <span>
              <HelpTip
                label={ui("help.open", { label: ui("side.publicAwarenessAward") })}
                lines={[{ label: ui("help.career.edit") }]}
              >
                {ui("side.publicAwarenessAward")}
              </HelpTip>
            </span>
            <BoundedNumberInput
              min={0}
              aria-label={ui("side.publicAwarenessAward")}
              value={ch.public_awareness || 0}
              onCommit={(n) => patch({ public_awareness: n })}
              style={{ width: 64 }}
            />
          </div>
          <p className="muted">{ui("side.awarenessFormula")}</p>
        </div>
      ) : null}
    </>
  );
}
