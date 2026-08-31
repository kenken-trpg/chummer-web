"use client";

import { useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import { DEFAULT_ARRAY_ORDER, MATRIX_ATTRS } from "@/lib/character/constants";
import { swapMatrixOrder } from "@/lib/character/gear";
import { deviceRatingBit } from "@/lib/character/format";

export function CyberdeckGear({
  catalog,
  character: ch,
  d,
  tr,
  patch,
  setCharacter,
}: TabPanelProps) {
  const [gearSearch, setGearSearch] = useState("");
  const [gearCat, setGearCat] = useState("all");
  const [slotPick, setSlotPick] = useState<Record<string, string>>({});
  const [extraPick, setExtraPick] = useState<Record<string, string>>({});

  return (
    <>
      <>
        {(d.cyberdecks || []).length ? (
          <p className="muted">
            作成時に配列の4数を ATK / SLZ / DP / FW
            へ割り当てます。値を選ぶと、その数値を持っていた項目と入れ替わります。
          </p>
        ) : null}
        {(d.cyberdecks || []).map((item) => (
          <div className="cyber-item" key={item.id}>
            <div>
              <b>{tr(item.name)}</b>
              <div className="muted">
                {item.name} / DR {item.device_rating} / ATK {item.attack} / SLZ {item.sleaze} / DP{" "}
                {item.dataprocessing} / FW {item.firewall} / プログラム {item.program_used ?? 0}/
                {item.program_max ?? item.programs ?? 0} / {item.nuyen.toLocaleString()}¥ /{" "}
                {item.source}
              </div>
              {item.rating_max > 0 ? (
                <div className="cyber-controls">
                  <label>
                    Rating
                    <input
                      type="number"
                      min={1}
                      max={item.rating_max}
                      value={item.rating}
                      onChange={(e) =>
                        patch({
                          cyberdecks: (ch.cyberdecks || []).map((row) =>
                            row.id === item.id ? { ...row, rating: Number(e.target.value) } : row,
                          ),
                        })
                      }
                    />
                  </label>
                </div>
              ) : null}
              {item.can_reorder && (item.array || []).length === 4 ? (
                <div className="matrix-array">
                  {MATRIX_ATTRS.map(([key, label]) => (
                    <label key={key}>
                      {label}
                      <select
                        value={String((item.array_order || DEFAULT_ARRAY_ORDER).indexOf(key))}
                        onChange={(e) =>
                          patch({
                            cyberdecks: (ch.cyberdecks || []).map((row) =>
                              row.id === item.id
                                ? {
                                    ...row,
                                    array_order: swapMatrixOrder(
                                      item.array_order,
                                      key,
                                      Number(e.target.value),
                                    ),
                                  }
                                : row,
                            ),
                          })
                        }
                      >
                        {(item.array || []).map((n, i) => (
                          <option key={`${key}-${i}`} value={i}>
                            {n}
                          </option>
                        ))}
                      </select>
                    </label>
                  ))}
                </div>
              ) : null}
              {(d.programs || [])
                .filter((prog) => prog.parent_id === item.id)
                .map((prog) => (
                  <div className="muted" key={prog.id} style={{ marginTop: 6 }}>
                    {tr(prog.name)}
                    {prog.rating_max > 0 ? ` R${prog.rating}` : ""}
                    {` / ${prog.nuyen.toLocaleString()}¥`}{" "}
                    <button
                      className="btn danger"
                      onClick={() =>
                        patch({
                          programs: (ch.programs || []).filter((row) => row.id !== prog.id),
                        })
                      }
                    >
                      外す
                    </button>
                    {prog.rating_max > 0 ? (
                      <label>
                        Rating
                        <input
                          type="number"
                          min={1}
                          max={prog.rating_max}
                          value={prog.rating}
                          onChange={(e) =>
                            patch({
                              programs: (ch.programs || []).map((row) =>
                                row.id === prog.id
                                  ? { ...row, rating: Number(e.target.value) }
                                  : row,
                              ),
                            })
                          }
                        />
                      </label>
                    ) : null}
                  </div>
                ))}
              <div className="cyber-controls">
                <select
                  value={slotPick[item.id] || ""}
                  onChange={(e) => setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))}
                >
                  <option value="">プログラムを追加</option>
                  {(catalog.programs || [])
                    .filter((prog) => prog.program_host === "cyberdecks")
                    .filter(
                      (prog) =>
                        !(d.programs || []).some(
                          (row) => row.parent_id === item.id && row.gear_id === prog.id,
                        ),
                    )
                    .filter((prog) => prog.source === "SR5")
                    .map((prog) => (
                      <option key={prog.id} value={prog.id}>
                        {tr(prog.name)} ({prog.cost}¥)
                      </option>
                    ))}
                </select>
                <button
                  className="btn"
                  disabled={!slotPick[item.id]}
                  onClick={() => {
                    const wareId = slotPick[item.id];
                    const spec = (catalog.programs || []).find((prog) => prog.id === wareId);
                    if (!spec) return;
                    patch({
                      programs: [
                        ...(ch.programs || []),
                        {
                          gear_id: spec.id,
                          rating: Math.max(1, spec.minrating || 1),
                          parent_id: item.id,
                        },
                      ],
                    });
                    setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
                  }}
                >
                  装着
                </button>
              </div>
            </div>
            <button
              className="btn danger"
              onClick={() =>
                patch({
                  cyberdecks: (ch.cyberdecks || []).filter((row) => row.id !== item.id),
                  programs: (ch.programs || []).filter((row) => row.parent_id !== item.id),
                })
              }
            >
              削除
            </button>
          </div>
        ))}
      </>

      <input
        type="search"
        placeholder="サイバーデッキを検索"
        value={gearSearch}
        onChange={(e) => setGearSearch(e.target.value)}
      />

      <div className="quality-list">
        {(catalog.cyberdecks || [])
          .filter((item) => {
            const q = gearSearch.trim().toLowerCase();
            if (q)
              return item.name.toLowerCase().includes(q) || tr(item.name).toLowerCase().includes(q);
            return item.source === "SR5";
          })
          .slice(0, 40)
          .map((item) => (
            <div className="quality-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / DR {item.devicerating}
                  {item.attributearray ? ` / ${item.attributearray}` : ""} / プログラム{" "}
                  {item.programs} / {item.cost}¥ / {item.avail || "-"} / {item.source}
                </div>
              </div>
              <button
                className="btn primary"
                onClick={() =>
                  patch({
                    cyberdecks: [
                      ...(ch.cyberdecks || []),
                      { gear_id: item.id, rating: Math.max(1, item.minrating || 1) },
                    ],
                  })
                }
              >
                購入
              </button>
            </div>
          ))}
      </div>
    </>
  );
}
