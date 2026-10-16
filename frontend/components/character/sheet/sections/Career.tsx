import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";
import { useUiText } from "@/lib/i18n";
import { renderNotice } from "@/lib/engine-notices";
import type { MsgKey, UiFn } from "@/lib/i18n";

/** The two reasons Chummer writes itself when a character leaves creation.
 *  Every other label is the player's own and is shown as written; these are
 *  translated for display only, so the save keeps what Chummer wrote. */
const CHUMMER_REWARDS: Record<string, MsgKey> = {
  "Starting Karma": "sheet.reward.startingKarma",
  "Starting Nuyen": "sheet.reward.startingNuyen",
};

function rewardLabel(label: string | undefined, ui: UiFn): string {
  if (!label) return ui("side.reward");
  const key = CHUMMER_REWARDS[label];
  return key ? ui(key) : label;
}

export function CareerSection(s: SheetData) {
  const { character, d, tr } = s;
  const { ui } = useUiText();
  if (!(character.career || d.career)) return null;
  return (
    <Section title="sheet.career">
      <div className="sheet-derived-grid">
        <div>
          <span>{ui("sheet.rewardTotal")}</span>
          <b>
            {d.karma_earned || 0}K / {(d.nuyen_earned || 0).toLocaleString()}¥
          </b>
        </div>
        <div>
          <span>{ui("sheet.advancementKarma")}</span>
          <b>{d.career_advancement_karma || 0}K</b>
        </div>
        <div>
          <span>{ui("sheet.repLine")}</span>
          <b>
            {d.street_cred || 0} / {d.notoriety || 0} / {d.public_awareness || 0}
          </b>
        </div>
      </div>
      {(d.reward_log || []).length ? (
        <div className="sheet-block">
          <h4>{ui("sheet.rewardLog")}</h4>
          <ul className="sheet-list">
            {(d.reward_log || []).map((row) => (
              <li key={row.id}>
                <b>{rewardLabel(row.label, ui)}</b>
                <span className="sheet-dim">
                  {" "}
                  {row.karma}K / {row.nuyen.toLocaleString()}¥
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {(d.karma_spend_breakdown || []).length ? (
        <div className="sheet-block">
          <h4>{ui("sheet.karmaBreakdown")}</h4>
          <ul className="sheet-list">
            {(d.karma_spend_breakdown || []).map((row, idx) => (
              <li key={`ks-${idx}`}>
                <b>{renderNotice(row.notice, ui, tr)}</b>
                <span className="sheet-dim"> {row.amount}K</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {(d.nuyen_spend_breakdown || []).length ? (
        <div className="sheet-block">
          <h4>{ui("sheet.nuyenBreakdown")}</h4>
          <ul className="sheet-list">
            {(d.nuyen_spend_breakdown || []).map((row, idx) => (
              <li key={`ns-${idx}`}>
                <b>{renderNotice(row.notice, ui, tr)}</b>
                <span className="sheet-dim"> {row.amount.toLocaleString()}¥</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </Section>
  );
}
