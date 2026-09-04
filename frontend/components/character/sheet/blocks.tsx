import type { ReactNode } from "react";
import type { InstalledDrone } from "@/lib/types";
import { vehicleCM } from "@/lib/character/format";
import { type MsgKey, useUiText } from "@/lib/i18n";

/** Minimal shape the initiation / submersion grade lists share. */
type GradeItem = { grade: number; name: string; extra?: string | null; kind?: string };

export function Section({
  title,
  children,
  empty,
}: {
  /** The key, not the words: a section cannot hard-code its own heading. */
  title: MsgKey;
  children: ReactNode;
  empty?: boolean;
}) {
  const { ui } = useUiText();
  if (empty) return null;
  return (
    <section className="sheet-section">
      <h3>{ui(title)}</h3>
      {children}
    </section>
  );
}

export function GradeList({ items, tr }: { items: GradeItem[]; tr: (n: string) => string }) {
  const { ui } = useUiText();
  const grades = Array.from(new Set(items.map((i) => Number(i.grade) || 0))).sort((a, b) => a - b);
  return (
    <ul className="sheet-list">
      {grades.map((g) => (
        <li key={g}>
          <b>{ui("sheet.grade", { grade: g })}</b>
          <span className="sheet-dim">
            {" "}
            {items
              .filter((i) => (Number(i.grade) || 0) === g)
              .map(
                (i) =>
                  `${tr(i.name)}${i.extra ? `（${tr(i.extra)}）` : ""}${i.kind === "art" ? ui("sheet.art") : ""}`,
              )
              .join("、")}
          </span>
        </li>
      ))}
    </ul>
  );
}

export function VehicleBlock({ v, tr }: { v: InstalledDrone; tr: (n: string) => string }) {
  const { ui } = useUiText();
  const mods = (v.mods || []).filter((m) => !m.parent_id);
  const mounts = v.weapon_mounts || [];
  const sensors = v.sensors || [];
  const gear = (v.gear || []).filter((g) => !g.parent_id);
  const tracks = v.slot_tracks || [];
  return (
    <div className="sheet-block">
      <h4>
        {tr(v.name)}
        {v.seats ? ui("sheet.seats", { seats: v.seats }) : ""}
      </h4>
      <div className="sheet-derived-grid sheet-vehicle-stats">
        <div>
          <span>{ui("sheet.veh.handling")}</span>
          <b>{v.handling || "-"}</b>
        </div>
        <div>
          <span>{ui("sheet.veh.speed")}</span>
          <b>{v.speed || "-"}</b>
        </div>
        <div>
          <span>{ui("sheet.veh.accel")}</span>
          <b>{v.accel || "-"}</b>
        </div>
        <div>
          <span>{ui("sheet.veh.body")}</span>
          <b>{v.body || "-"}</b>
        </div>
        <div>
          <span>{ui("sheet.veh.armor")}</span>
          <b>{v.armor || "-"}</b>
        </div>
        <div>
          <span>{ui("sheet.veh.pilot")}</span>
          <b>{v.pilot || "-"}</b>
        </div>
        <div>
          <span>{ui("sheet.veh.sensor")}</span>
          <b>{v.sensor || "-"}</b>
        </div>
        <div>
          <span>{ui("sheet.veh.physicalCm")}</span>
          <b>{vehicleCM(v.body)}</b>
        </div>
      </div>
      {mods.length ? (
        <p className="sheet-note">
          {ui("sheet.veh.mods", {
            list: mods
              .map((m) => `${tr(m.name)}${(m.rating || 0) > 1 ? ` R${m.rating}` : ""}`)
              .join(ui("common.listSep")),
          })}
        </p>
      ) : null}
      {mounts.length ? (
        <p className="sheet-note">
          {ui("sheet.veh.mounts", {
            list: mounts
              .map(
                (m) =>
                  `${tr(m.label || m.name)}${
                    m.weapon_name ? `＝${tr(m.weapon_name)}` : ui("sheet.veh.mountEmpty")
                  }`,
              )
              .join(ui("common.listSep")),
          })}
        </p>
      ) : null}
      {sensors.length ? (
        <p className="sheet-note">
          {ui("sheet.veh.sensors", {
            list: sensors.map((row) => tr(row.name)).join(ui("common.listSep")),
          })}
        </p>
      ) : null}
      {gear.length ? (
        <p className="sheet-note">
          {ui("sheet.veh.gear", {
            list: gear.map((g) => tr(g.name)).join(ui("common.listSep")),
          })}
        </p>
      ) : null}
      {tracks.length ? (
        <p className="sheet-note">
          {ui("sheet.veh.slots", {
            list: tracks
              .map((row) => `${row.label} ${row.used}/${row.max}`)
              .join(` ${ui("common.termSep")} `),
          })}
        </p>
      ) : null}
    </div>
  );
}
