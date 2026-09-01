import { useState } from "react";
import type { SidebarBlockProps } from "@/components/character/sidebar/types";

export function SidebarCareerRewards({ career, ch, d, patch }: SidebarBlockProps) {
  const rewardLog = d.reward_log || ch.reward_log || [];
  const [rewardLabel, setRewardLabel] = useState("");
  const [rewardKarma, setRewardKarma] = useState(0);
  const [rewardNuyen, setRewardNuyen] = useState(0);
  const [showBreakdown, setShowBreakdown] = useState(false);

  const addReward = () => {
    if (!patch) return;
    const karma = Math.max(0, Number(rewardKarma) || 0);
    const nuyen = Math.max(0, Number(rewardNuyen) || 0);
    if (!karma && !nuyen) return;
    const next = [
      ...rewardLog.map((row) => ({
        id: row.id,
        label: row.label || "報酬",
        karma: Math.max(0, Number(row.karma) || 0),
        nuyen: Math.max(0, Number(row.nuyen) || 0),
      })),
      {
        id: crypto.randomUUID(),
        label: rewardLabel.trim() || "報酬",
        karma,
        nuyen,
      },
    ];
    patch({ reward_log: next });
    setRewardLabel("");
    setRewardKarma(0);
    setRewardNuyen(0);
  };

  const removeReward = (id: string) => {
    if (!patch) return;
    patch({
      reward_log: rewardLog
        .filter((row) => row.id !== id)
        .map((row) => ({
          id: row.id,
          label: row.label || "報酬",
          karma: Math.max(0, Number(row.karma) || 0),
          nuyen: Math.max(0, Number(row.nuyen) || 0),
        })),
    });
  };

  return (
    <>
      {career && patch ? (
        <div className="career-panel">
          <div className="stat">
            <span>報酬合計</span>
            <b>
              {d.karma_earned || 0}K / {(d.nuyen_earned || 0).toLocaleString()}¥
            </b>
          </div>
          {(rewardLog || []).map((row) => (
            <div className="stat" key={row.id}>
              <span className="muted">
                {row.label || "報酬"} · {row.karma || 0}K / {(row.nuyen || 0).toLocaleString()}¥
              </span>
              <button
                type="button"
                className="btn danger"
                style={{ padding: "2px 6px", fontSize: "0.75rem" }}
                onClick={() => row.id && removeReward(row.id)}
              >
                削除
              </button>
            </div>
          ))}
          <label className="muted">
            ラベル
            <input
              value={rewardLabel}
              onChange={(e) => setRewardLabel(e.target.value)}
              placeholder="Run 名など"
            />
          </label>
          <div className="stat">
            <span>K</span>
            <input
              type="number"
              min={0}
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
              value={rewardNuyen}
              onChange={(e) => setRewardNuyen(Math.max(0, Number(e.target.value) || 0))}
              style={{ width: 96 }}
            />
          </div>
          <button type="button" className="btn" onClick={addReward}>
            報酬を追加
          </button>
          <button type="button" className="btn" onClick={() => setShowBreakdown((v) => !v)}>
            {showBreakdown ? "内訳を隠す" : "成長／買い物の内訳"}
          </button>
          {showBreakdown ? (
            <div className="career-breakdown">
              <p className="muted">カルマ消費</p>
              {(d.karma_spend_breakdown || []).length ? (
                (d.karma_spend_breakdown || []).map((row, idx) => (
                  <div className="stat" key={`k-${row.label}-${idx}`}>
                    <span>{row.label}</span>
                    <b>{row.amount}K</b>
                  </div>
                ))
              ) : (
                <p className="muted">なし</p>
              )}
              <p className="muted">ニューエン消費</p>
              {(d.nuyen_spend_breakdown || []).length ? (
                (d.nuyen_spend_breakdown || []).map((row, idx) => (
                  <div className="stat" key={`y-${row.label}-${idx}`}>
                    <span>{row.label}</span>
                    <b>{row.amount.toLocaleString()}¥</b>
                  </div>
                ))
              ) : (
                <p className="muted">なし</p>
              )}
            </div>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
