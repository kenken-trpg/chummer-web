"use client";

import type { TabPanelProps } from "@/components/character/types";

import { useState } from "react";
import { cfDuration, cfTarget, testLine } from "@/lib/character/format";

export function ComplexFormsTab({
  catalog,
  character: ch,
  d,
  tr,
  patch,
  setCharacter,
}: TabPanelProps) {
  const [cfSearch, setCfSearch] = useState("");

  return (
    <div className="card">
      <p className="muted">
        優先度の無料枠 {d.complex_form_points?.used || 0}/{d.complex_form_points?.free || 0}
        {(d.complex_form_points?.paid || 0) > 0
          ? ` ・ 追加 ${d.complex_form_points?.paid}×4カルマ`
          : ""}
        {d.fade_resist ? ` ・ フェード抵抗 ${d.fade_resist.attrs} ${d.fade_resist.pool}` : ""}
        。スレッディングは Software+RES[Level]。Level が共振力超なら物理フェード。
      </p>
      {(d.complex_forms || []).map((item) => (
        <div className="cyber-item" key={item.id}>
          <div>
            <b>{tr(item.label || item.name)}</b>
            <div className="muted">
              {item.name} / {cfTarget(item.target)} / {cfDuration(item.duration)} / {item.fv}
              {` @ L${item.level} → フェード ${item.fade == null ? "特殊" : `${item.fade}${item.fade_code || ""}`}`}
              {item.free ? " / 無料" : ` / ${item.karma}カルマ`}
              {" / "}
              {item.source}
            </div>
            {item.test ? <div className="muted">{testLine(item.test, "フェード")}</div> : null}
            <div className="cyber-controls">
              <label>
                Level
                <input
                  type="number"
                  min={item.level_min}
                  max={item.level_max}
                  value={item.level}
                  onChange={(e) =>
                    patch({
                      complex_forms: (ch.complex_forms || []).map((row) =>
                        row.id === item.id ? { ...row, level: Number(e.target.value) } : row,
                      ),
                    })
                  }
                />
              </label>
              {item.needs_extra ? (
                <label>
                  能力値
                  <select
                    value={item.extra || ""}
                    onChange={(e) =>
                      patch({
                        complex_forms: (ch.complex_forms || []).map((row) =>
                          row.id === item.id ? { ...row, extra: e.target.value } : row,
                        ),
                      })
                    }
                  >
                    <option value="">選択してください</option>
                    {(item.options || []).map((name) => (
                      <option key={name} value={name}>
                        {tr(name)}
                      </option>
                    ))}
                  </select>
                </label>
              ) : null}
            </div>
          </div>
          <button
            className="btn danger"
            onClick={() =>
              patch({
                complex_forms: (ch.complex_forms || []).filter((row) => row.id !== item.id),
              })
            }
          >
            削除
          </button>
        </div>
      ))}
      <input
        type="search"
        placeholder="複合体を検索"
        value={cfSearch}
        onChange={(e) => setCfSearch(e.target.value)}
      />
      <div className="quality-list">
        {(catalog.complex_forms || [])
          .filter((item) => !(ch.complex_forms || []).some((row) => row.form_id === item.id))
          .filter((item) => {
            const q = cfSearch.trim().toLowerCase();
            if (q) {
              return (
                item.name.toLowerCase().includes(q) ||
                tr(item.name).toLowerCase().includes(q) ||
                (item.target || "").toLowerCase().includes(q)
              );
            }
            return item.source === "SR5";
          })
          .slice(0, 40)
          .map((item) => {
            const paid = (d.complex_form_points?.used || 0) >= (d.complex_form_points?.free || 0);
            const blocked = (item.required || []).length
              ? `必要 ${item.required!.map((name) => tr(name)).join("・")}`
              : "";
            return (
              <div className="quality-item" key={item.id}>
                <div>
                  <b>{tr(item.name)}</b>
                  <div className="muted">
                    {item.name} / {cfTarget(item.target)} / {cfDuration(item.duration)} / {item.fv}{" "}
                    / {item.source}
                    {item.needs_extra ? " / マトリクス能力値が必要" : ""}
                    {blocked ? ` / ${blocked}` : ""}
                    {paid ? " / 4カルマ" : " / 無料"}
                  </div>
                </div>
                <button
                  className="btn primary"
                  onClick={() =>
                    patch({
                      complex_forms: [...(ch.complex_forms || []), { form_id: item.id }],
                    })
                  }
                >
                  追加
                </button>
              </div>
            );
          })}
      </div>
    </div>
  );
}
