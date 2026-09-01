import type { SheetData } from "@/lib/character/sheet-data";
import { Section } from "@/components/character/sheet/blocks";

export function CareerSection(s: SheetData) {
  const { character, d } = s;
  if (!(character.career || d.career)) return null;
  return (
    <Section title="キャリア">
      <div className="sheet-derived-grid">
        <div>
          <span>報酬合計</span>
          <b>
            {d.karma_earned || 0}K / {(d.nuyen_earned || 0).toLocaleString()}¥
          </b>
        </div>
        <div>
          <span>成長カルマ</span>
          <b>{d.career_advancement_karma || 0}K</b>
        </div>
        <div>
          <span>SC / 悪名 / 周知</span>
          <b>
            {d.street_cred || 0} / {d.notoriety || 0} / {d.public_awareness || 0}
          </b>
        </div>
      </div>
      {(d.reward_log || []).length ? (
        <div className="sheet-block">
          <h4>報酬履歴</h4>
          <ul className="sheet-list">
            {(d.reward_log || []).map((row) => (
              <li key={row.id}>
                <b>{row.label}</b>
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
          <h4>カルマ消費内訳</h4>
          <ul className="sheet-list">
            {(d.karma_spend_breakdown || []).map((row, idx) => (
              <li key={`ks-${idx}`}>
                <b>{row.label}</b>
                <span className="sheet-dim"> {row.amount}K</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
      {(d.nuyen_spend_breakdown || []).length ? (
        <div className="sheet-block">
          <h4>買い物内訳</h4>
          <ul className="sheet-list">
            {(d.nuyen_spend_breakdown || []).map((row, idx) => (
              <li key={`ns-${idx}`}>
                <b>{row.label}</b>
                <span className="sheet-dim"> {row.amount.toLocaleString()}¥</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </Section>
  );
}
