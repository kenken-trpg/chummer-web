"use client";
import { useState } from "react";
import { CatalogPicker } from "@/components/character/CatalogPicker";
import type { TabPanelProps } from "@/components/character/types";
import { WareRow } from "@/components/character/WareRow";
import { R5_SLOT_LABELS } from "@/lib/character/constants";
import {
  dropDrone,
  dropTree,
  vehicleFits,
  vehicleForbidden,
  vehicleInteriorFits,
  wareFitsVehicleMod,
} from "@/lib/character/gear";
import { removeWareTree, wareBounds } from "@/lib/character/ware";

export function VehicleDroneGear({
  catalog,
  character: ch,
  d,
  tr,
  patch,
  mode,
}: TabPanelProps & { mode: "drone" | "vehicle" }) {
  const [slotPick, setSlotPick] = useState<Record<string, string>>({});

  return (
    <>
      <>
        {((mode === "drone" ? d.drones : d.vehicles) || []).map((item) => {
          const addons = (catalog.vehicle_mods || []).filter(
            (mod) =>
              mod.purchasable !== false &&
              String(mod.cost || "").trim() !== "0" &&
              vehicleFits(mod.required, item) &&
              !vehicleForbidden(mod.forbidden, item) &&
              !(item.mods || []).some((row) => row.mod_id === mod.id),
          );
          const sizes = (catalog.weapon_mounts || []).filter(
            (mod) => mod.category === "Size" && vehicleFits(mod.required, item),
          );
          const mountedIds = new Set(
            (item.weapon_mounts || []).map((row) => row.weapon_install_id).filter(Boolean),
          );
          const freeWeapons = (d.weapons || []).filter(
            (weapon) => !weapon.mounted_on && !mountedIds.has(weapon.id),
          );
          return (
            <div className="cyber-item" key={item.id}>
              <div>
                <b>{tr(item.name)}</b>
                <div className="muted">
                  {item.name} / {tr(item.category)} / HND {item.handling} / SPD {item.speed} / ACC{" "}
                  {item.accel} / BOD {item.body} / ARM {item.armor} / PLT {item.pilot} / SNR{" "}
                  {item.sensor}
                  {item.seats ? ` / SEAT ${item.seats}` : ""}
                  {(item.slot_tracks || []).length
                    ? ` / ${(item.slot_tracks || []).map((track) => `${track.label} ${track.used}/${track.max}`).join(" · ")}`
                    : item.slots_max
                      ? ` / スロット ${item.slots_used ?? 0}/${item.slots_max}`
                      : ""}
                  {" / "}
                  {item.nuyen.toLocaleString()}¥ / {item.source}
                </div>
                {(item.mods || []).map((mod) => {
                  const hosted = (d.cyberware || []).filter((row) => row.parent_id === mod.id);
                  const wareOptions = (mod.subsystems || []).length
                    ? catalog.cyberware.items.filter((ware) => wareFitsVehicleMod(ware, mod))
                    : [];
                  const warePickKey = `${mod.id}-ware`;
                  const chosenWare = slotPick[warePickKey] || wareOptions[0]?.id || "";
                  return (
                    <div className="muted" key={mod.id} style={{ marginTop: 6 }}>
                      {tr(mod.name)}
                      {mod.rating_max > 0 ? ` R${mod.rating}` : ""}
                      {mod.included ? " / 付属" : ` / ${mod.nuyen.toLocaleString()}¥`}
                      {mod.slots ? ` / スロット ${mod.slots}` : ""}
                      {mod.capacity_max
                        ? ` / 容量 ${mod.capacity_used ?? 0}/${mod.capacity_max}`
                        : ""}
                      {R5_SLOT_LABELS[mod.category] ? ` / ${R5_SLOT_LABELS[mod.category]}` : null}
                      {mod.included ? null : (
                        <>
                          {" "}
                          <button
                            className="btn danger"
                            onClick={() =>
                              patch({
                                vehicle_mods: (ch.vehicle_mods || []).filter(
                                  (row) => row.id !== mod.id,
                                ),
                                cyberware: removeWareTree(ch.cyberware || [], mod.id),
                              })
                            }
                          >
                            外す
                          </button>
                        </>
                      )}
                      {mod.rating_max > 0 && !mod.included ? (
                        <label>
                          Rating
                          <input
                            type="number"
                            min={1}
                            max={mod.rating_max}
                            value={mod.rating}
                            onChange={(e) =>
                              patch({
                                vehicle_mods: (ch.vehicle_mods || []).map((row) =>
                                  row.id === mod.id
                                    ? { ...row, rating: Number(e.target.value) }
                                    : row,
                                ),
                              })
                            }
                          />
                        </label>
                      ) : null}
                      {hosted.map((child) => (
                        <WareRow
                          key={child.id}
                          item={child}
                          childrenItems={(d.cyberware || []).filter(
                            (row) => row.parent_id === child.id,
                          )}
                          catalogItems={catalog.cyberware.items}
                          grades={catalog.cyberware.grades.filter(
                            (g) => !(d.disabled_cyberware_grades || []).includes(g.name),
                          )}
                          kind="cyberware"
                          tr={tr}
                          slotValue={slotPick[child.id] || ""}
                          wareRanges={d.ware_ranges}
                          nested
                          onSlotChange={(wareId) =>
                            setSlotPick((cur) => ({ ...cur, [child.id]: wareId }))
                          }
                          onPatchRow={(id, next) =>
                            patch({
                              cyberware: (ch.cyberware || []).map((row) =>
                                row.id === id ? { ...row, ...next } : row,
                              ),
                            })
                          }
                          onRemove={(id) =>
                            patch({
                              cyberware: removeWareTree(ch.cyberware || [], id),
                            })
                          }
                          onAddChild={(wareId) => {
                            const spec = catalog.cyberware.items.find((w) => w.id === wareId);
                            if (!spec) return;
                            const range = wareBounds(spec, d.ware_ranges);
                            patch({
                              cyberware: [
                                ...(ch.cyberware || []),
                                {
                                  ware_id: spec.id,
                                  rating: range.min,
                                  grade: child.grade,
                                  wireless: true,
                                  parent_id: child.id,
                                },
                              ],
                            });
                          }}
                        />
                      ))}
                      {wareOptions.length ? (
                        <div className="slot-picker">
                          <select
                            aria-label={`${tr(mod.name)}: 強化を追加`}
                            value={chosenWare}
                            onChange={(e) =>
                              setSlotPick((cur) => ({ ...cur, [warePickKey]: e.target.value }))
                            }
                          >
                            {wareOptions.map((ware) => {
                              const range = wareBounds(ware, d.ware_ranges);
                              const showRange = range.max > range.min || range.max > 1;
                              return (
                                <option key={ware.id} value={ware.id}>
                                  {tr(ware.name)} /{" "}
                                  {ware.capacity ? `[${ware.capacity}]` : ware.category}
                                  {showRange ? ` R${range.min}-${range.max}` : ""}
                                </option>
                              );
                            })}
                          </select>
                          <button
                            className="btn primary"
                            disabled={!chosenWare}
                            onClick={() => {
                              const spec = wareOptions.find((w) => w.id === chosenWare);
                              if (!spec) return;
                              const range = wareBounds(spec, d.ware_ranges);
                              patch({
                                cyberware: [
                                  ...(ch.cyberware || []),
                                  {
                                    ware_id: spec.id,
                                    rating: range.min,
                                    grade: "Standard",
                                    wireless: true,
                                    parent_id: mod.id,
                                  },
                                ],
                              });
                              setSlotPick((cur) => ({ ...cur, [warePickKey]: "" }));
                            }}
                          >
                            スロットに追加
                          </button>
                        </div>
                      ) : null}
                    </div>
                  );
                })}
                {addons.length ? (
                  <div className="cyber-controls">
                    <select
                      aria-label={`${tr(item.name)}: 改造を追加`}
                      value={slotPick[item.id] || ""}
                      onChange={(e) =>
                        setSlotPick((cur) => ({ ...cur, [item.id]: e.target.value }))
                      }
                    >
                      <option value="">改造を追加</option>
                      {addons
                        // used to lift as soon as the catalog search box below
                        // had text in it, which nothing signposted
                        .filter((mod) => mod.source === "SR5" || mod.source === "R5")
                        .map((mod) => (
                          <option key={mod.id} value={mod.id}>
                            {tr(mod.name)} ({mod.cost}¥)
                          </option>
                        ))}
                    </select>
                    <button
                      className="btn"
                      disabled={!slotPick[item.id]}
                      onClick={() => {
                        const wareId = slotPick[item.id];
                        const spec = addons.find((mod) => mod.id === wareId);
                        if (!spec) return;
                        patch({
                          vehicle_mods: [
                            ...(ch.vehicle_mods || []),
                            {
                              mod_id: spec.id,
                              parent_id: item.id,
                              rating: Math.max(1, spec.minrating || 1),
                            },
                          ],
                        });
                        setSlotPick((cur) => ({ ...cur, [item.id]: "" }));
                      }}
                    >
                      装着
                    </button>
                  </div>
                ) : null}
                {(item.weapon_mounts || []).map((mount) => (
                  <div className="muted" key={mount.id} style={{ marginTop: 6 }}>
                    {tr(mount.label || mount.name)}
                    {mount.included ? " / 付属" : ` / ${mount.nuyen.toLocaleString()}¥`}
                    {mount.slots ? ` / スロット ${mount.slots}` : ""}
                    {mount.weapon_name ? ` / ${tr(mount.weapon_name)}` : " / 未搭載"}
                    {mount.included ? null : (
                      <>
                        {" "}
                        <button
                          className="btn danger"
                          onClick={() =>
                            patch({
                              weapon_mounts: (ch.weapon_mounts || []).filter(
                                (row) => row.id !== mount.id,
                              ),
                            })
                          }
                        >
                          外す
                        </button>
                      </>
                    )}
                    <div className="cyber-controls">
                      <select
                        aria-label={`${tr(mount.name)}: 武器を搭載`}
                        value={mount.weapon_install_id || ""}
                        onChange={(e) =>
                          patch({
                            weapon_mounts: (ch.weapon_mounts || []).map((row) =>
                              row.id === mount.id
                                ? { ...row, weapon_install_id: e.target.value || null }
                                : row,
                            ),
                          })
                        }
                      >
                        <option value="">武器を搭載</option>
                        {mount.weapon_install_id && mount.weapon_name ? (
                          <option value={mount.weapon_install_id}>{tr(mount.weapon_name)}</option>
                        ) : null}
                        {freeWeapons.map((weapon) => (
                          <option key={weapon.id} value={weapon.id}>
                            {tr(weapon.name)}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>
                ))}
                {sizes.length ? (
                  <div className="cyber-controls">
                    <select
                      aria-label={`${tr(item.name)}: 武器マウントを追加`}
                      value={slotPick[`${item.id}-mount`] || ""}
                      onChange={(e) =>
                        setSlotPick((cur) => ({ ...cur, [`${item.id}-mount`]: e.target.value }))
                      }
                    >
                      <option value="">武器マウントを追加</option>
                      {sizes
                        .filter((mod) => mod.source === "SR5" || mod.source === "R5")
                        .map((mod) => (
                          <option key={mod.id} value={mod.id}>
                            {tr(mod.name)} ({mod.cost}¥)
                          </option>
                        ))}
                    </select>
                    <button
                      className="btn"
                      disabled={!slotPick[`${item.id}-mount`]}
                      onClick={() => {
                        const wareId = slotPick[`${item.id}-mount`];
                        const spec = sizes.find((mod) => mod.id === wareId);
                        if (!spec) return;
                        patch({
                          weapon_mounts: [
                            ...(ch.weapon_mounts || []),
                            { size_id: spec.id, parent_id: item.id },
                          ],
                        });
                        setSlotPick((cur) => ({ ...cur, [`${item.id}-mount`]: "" }));
                      }}
                    >
                      装着
                    </button>
                  </div>
                ) : null}
                {(item.sensors || []).map((sensor) => {
                  const functions = (d.sensors || []).filter(
                    (child) => child.parent_id === sensor.id,
                  );
                  const sensorAddons = (catalog.sensors || []).filter(
                    (mod) =>
                      (sensor.addoncategories || []).includes(mod.category) &&
                      mod.category !== "Custom" &&
                      !functions.some((child) => child.gear_id === mod.id),
                  );
                  return (
                    <div className="muted" key={sensor.id} style={{ marginTop: 6 }}>
                      {tr(sensor.name)}
                      {sensor.rating_max > 0 ? ` R${sensor.rating}` : ""}
                      {sensor.capacity_max
                        ? ` / 容量 ${sensor.capacity_used}/${sensor.capacity_max}`
                        : ""}
                      {sensor.included ? " / 付属" : ` / ${sensor.nuyen.toLocaleString()}¥`}
                      {functions.map((child) => (
                        <div key={child.id} style={{ marginTop: 4, marginLeft: 12 }}>
                          {tr(child.name)}
                          {child.capacity_cost ? ` / 容量 ${child.capacity_cost}` : ""}{" "}
                          <button
                            className="btn danger"
                            onClick={() =>
                              patch({
                                sensors: (ch.sensors || []).filter((row) => row.id !== child.id),
                              })
                            }
                          >
                            外す
                          </button>
                        </div>
                      ))}
                      {sensorAddons.length ? (
                        <div className="cyber-controls">
                          <select
                            aria-label={`${tr(sensor.name)}: 機能を追加`}
                            value={slotPick[sensor.id] || ""}
                            onChange={(e) =>
                              setSlotPick((cur) => ({ ...cur, [sensor.id]: e.target.value }))
                            }
                          >
                            <option value="">機能を追加</option>
                            {sensorAddons
                              .filter((mod) => mod.source === "SR5")
                              .map((mod) => (
                                <option key={mod.id} value={mod.id}>
                                  {tr(mod.name)} ({mod.cost}¥)
                                </option>
                              ))}
                          </select>
                          <button
                            className="btn"
                            disabled={!slotPick[sensor.id]}
                            onClick={() => {
                              const wareId = slotPick[sensor.id];
                              const spec = sensorAddons.find((mod) => mod.id === wareId);
                              if (!spec) return;
                              patch({
                                sensors: [
                                  ...(ch.sensors || []),
                                  {
                                    gear_id: spec.id,
                                    rating: Math.max(1, spec.minrating || 1),
                                    parent_id: sensor.id,
                                  },
                                ],
                              });
                              setSlotPick((cur) => ({ ...cur, [sensor.id]: "" }));
                            }}
                          >
                            装着
                          </button>
                        </div>
                      ) : null}
                    </div>
                  );
                })}
                {(item.gear || []).map((acc) => (
                  <div className="muted" key={acc.id} style={{ marginTop: 6 }}>
                    {tr(acc.label || acc.name)}
                    {acc.rating_max > 0 ? ` R${acc.rating}` : ""}
                    {acc.included ? " / 付属" : ` / ${acc.nuyen.toLocaleString()}¥`}
                    {acc.included ? null : (
                      <>
                        {" "}
                        <button
                          className="btn danger"
                          onClick={() =>
                            patch({
                              gear: dropTree(ch.gear || [], acc.id),
                            })
                          }
                        >
                          外す
                        </button>
                      </>
                    )}
                    {acc.rating_max > 0 && !acc.included ? (
                      <label>
                        Rating
                        <input
                          type="number"
                          min={1}
                          max={acc.rating_max}
                          value={acc.rating}
                          onChange={(e) =>
                            patch({
                              gear: (ch.gear || []).map((row) =>
                                row.id === acc.id
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
                    aria-label={`${tr(item.name)}: 内装ギアを追加`}
                    value={slotPick[`${item.id}-gear`] || ""}
                    onChange={(e) =>
                      setSlotPick((cur) => ({ ...cur, [`${item.id}-gear`]: e.target.value }))
                    }
                  >
                    <option value="">内装ギアを追加</option>
                    {(catalog.gear || [])
                      .filter(
                        (mod) => vehicleInteriorFits(mod) && String(mod.cost || "").trim() !== "0",
                      )
                      .filter((mod) => mod.source === "SR5")
                      .filter((mod) => !(item.gear || []).some((row) => row.gear_id === mod.id))
                      .map((mod) => (
                        <option key={mod.id} value={mod.id}>
                          {tr(mod.name)} ({mod.cost}¥)
                        </option>
                      ))}
                  </select>
                  <button
                    className="btn"
                    disabled={!slotPick[`${item.id}-gear`]}
                    onClick={() => {
                      const wareId = slotPick[`${item.id}-gear`];
                      const spec = (catalog.gear || []).find((mod) => mod.id === wareId);
                      if (!spec) return;
                      patch({
                        gear: [
                          ...(ch.gear || []),
                          {
                            gear_id: spec.id,
                            rating: Math.max(1, spec.minrating || 1),
                            parent_id: item.id,
                          },
                        ],
                      });
                      setSlotPick((cur) => ({ ...cur, [`${item.id}-gear`]: "" }));
                    }}
                  >
                    装着
                  </button>
                </div>
              </div>
              <button
                className="btn danger"
                onClick={() =>
                  patch(dropDrone(ch, item.id, mode === "vehicle" ? "vehicles" : "drones"))
                }
              >
                削除
              </button>
            </div>
          );
        })}
      </>

      {mode === "drone" ? (
        <CatalogPicker
          items={catalog.drones || []}
          label="ドローンを検索"
          tr={tr}
          describe={(item) => (
            <>
              {item.name} / {tr(item.category)} / HND {item.handling} / SPD {item.speed} / PLT{" "}
              {item.pilot} / SNR {item.sensor} / {item.cost}¥ / {item.avail || "-"} / {item.source}
            </>
          )}
          onAdd={(item) => patch({ drones: [...(ch.drones || []), { gear_id: item.id }] })}
        />
      ) : (
        <CatalogPicker
          items={catalog.vehicles || []}
          label="車両を検索"
          tr={tr}
          describe={(item) => (
            <>
              {item.name} / {tr(item.category)} / HND {item.handling} / SPD {item.speed} / SEAT{" "}
              {item.seats || "-"} / {item.cost}¥ / {item.avail || "-"} / {item.source}
            </>
          )}
          onAdd={(item) => patch({ vehicles: [...(ch.vehicles || []), { gear_id: item.id }] })}
        />
      )}
    </>
  );
}
