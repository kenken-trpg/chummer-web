import { useState } from "react";
import type { SidebarBlockProps } from "@/components/character/sidebar/types";

export function SidebarCareerRewards({ career, ch, d, patch, ui }: SidebarBlockProps) {
  const rewardLog = d.reward_log || ch.reward_log || [];
  const [rewardLabel, setRewardLabel] = useState("");
  const [rewardKarma, setRewardKarma] = useState(0);
  const [rewardNuyen, setRewardNuyen] = useState(0);
  const [showBreakdown, setShowBreakdown] = useState(false);

  /** Rows are stored with whatever label the user typed, empty included — the
   *  fallback wording is applied when rendering, so an unnamed reward reads in
   *  the *reader's* language rather than the one it was created in. */
  const clean = (row: (typeof rewardLog)[number]) => ({
    id: row.id,
    label: row.label || "",
    karma: Math.max(0, Number(row.karma) || 0),
    nuyen: Math.max(0, Number(row.nuyen) || 0),
  });

  const addReward = () => {
    if (!patch) return;
    const karma = Math.max(0, Number(rewardKarma) || 0);
    const nuyen = Math.max(0, Number(rewardNuyen) || 0);
    if (!karma && !nuyen) return;
    patch({
      reward_log: [
        ...rewardLog.map(clean),
        { id: crypto.randomUUID(), label: rewardLabel.trim(), karma, nuyen },
      ],
    });
    setRewardLabel("");
    setRewardKarma(0);
    setRewardNuyen(0);
  };

  const removeReward = (id: string) => {
    if (!patch) return;
    patch({ reward_log: rewardLog.filter((row) => row.id !== id).map(clean) });
  };

  return (
    <>
      {career && patch ? (
        <div className="career-panel">
          <div className="stat">
            <span>{ui("side.rewardTotal")}</span>
            <b>
              {d.karma_earned || 0}K / {(d.nuyen_earned || 0).toLocaleString()}¥
            </b>
          </div>
          {(rewardLog || []).map((row) => (
            <div className="stat" key={row.id}>
              <span className="muted">
                {row.label || ui("side.reward")} · {row.karma || 0}K /{" "}
                {(row.nuyen || 0).toLocaleString()}¥
              </span>
              <button
                type="button"
                className="btn danger"
                style={{ padding: "2px 6px", fontSize: "0.75rem" }}
                aria-label={`${row.label || ui("side.reward")}: ${ui("side.deleteReward")}`}
                onClick={() => row.id && removeReward(row.id)}
              >
                {ui("side.deleteReward")}
              </button>
            </div>
          ))}
          <label className="muted">
            {ui("side.rewardLabel")}
            <input
              value={rewardLabel}
              onChange={(e) => setRewardLabel(e.target.value)}
              placeholder={ui("side.rewardLabelHint")}
            />
          </label>
          <div className="stat">
            <span>K</span>
            <input
              type="number"
              min={0}
              aria-label={ui("side.karma")}
              value={rewardKarma}
              onChange={(e) => setRewardKarma(Math.max(0, Number(e.target.value) || 0))}
              style={{ width: 56 }}
            />
          </div>
          <div className="stat">
            <span>¥</span>
            <input
              type="number"
              min={0}
              step={1000}
              aria-label={ui("side.nuyen")}
              value={rewardNuyen}
              onChange={(e) => setRewardNuyen(Math.max(0, Number(e.target.value) || 0))}
              style={{ width: 96 }}
            />
          </div>
          <button type="button" className="btn" onClick={addReward}>
            {ui("side.addReward")}
          </button>
          <button type="button" className="btn" onClick={() => setShowBreakdown((v) => !v)}>
            {showBreakdown ? ui("side.hideBreakdown") : ui("side.showBreakdown")}
          </button>
          {showBreakdown ? (
            <div className="career-breakdown">
              <p className="muted">{ui("side.karmaSpend")}</p>
              {(d.karma_spend_breakdown || []).length ? (
                (d.karma_spend_breakdown || []).map((row, idx) => (
                  <div className="stat" key={`k-${row.label}-${idx}`}>
                    <span>{row.label}</span>
                    <b>{row.amount}K</b>
                  </div>
                ))
              ) : (
                <p className="muted">{ui("side.none")}</p>
              )}
              <p className="muted">{ui("side.nuyenSpend")}</p>
              {(d.nuyen_spend_breakdown || []).length ? (
                (d.nuyen_spend_breakdown || []).map((row, idx) => (
                  <div className="stat" key={`y-${row.label}-${idx}`}>
                    <span>{row.label}</span>
                    <b>{row.amount.toLocaleString()}¥</b>
                  </div>
                ))
              ) : (
                <p className="muted">{ui("side.none")}</p>
              )}
            </div>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
