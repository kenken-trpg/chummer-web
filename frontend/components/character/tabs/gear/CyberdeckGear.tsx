"use client";
import { AddonSelect } from "@/components/character/AddonSelect";
import { CatalogPicker } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { DEFAULT_ARRAY_ORDER, MATRIX_ATTRS } from "@/lib/character/constants";
import { swapMatrixOrder } from "@/lib/character/gear";

export function CyberdeckGear({ catalog, character: ch, d, tr, patch }: TabPanelProps) {
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
              <AddonSelect
                rowName={tr(item.name)}
                prompt="プログラムを追加"
                tr={tr}
                options={(catalog.programs || []).filter(
                  (prog) =>
                    prog.program_host === "cyberdecks" &&
                    prog.source === "SR5" &&
                    !(d.programs || []).some(
                      (row) => row.parent_id === item.id && row.gear_id === prog.id,
                    ),
                )}
                onAdd={(prog) =>
                  patch({
                    programs: [
                      ...(ch.programs || []),
                      {
                        gear_id: prog.id,
                        rating: Math.max(1, prog.minrating || 1),
                        parent_id: item.id,
                      },
                    ],
                  })
                }
              />
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

      <CatalogPicker
        items={catalog.cyberdecks || []}
        label="サイバーデッキを検索"
        tr={tr}
        describe={(item) => (
          <>
            {item.name} / DR {item.devicerating}
            {item.attributearray ? ` / ${item.attributearray}` : ""} / プログラム {item.programs} /{" "}
            {item.cost}¥ / {item.avail || "-"} / {item.source}
          </>
        )}
        onAdd={(item) =>
          patch({
            cyberdecks: [
              ...(ch.cyberdecks || []),
              { gear_id: item.id, rating: Math.max(1, item.minrating || 1) },
            ],
          })
        }
      />
    </>
  );
}
