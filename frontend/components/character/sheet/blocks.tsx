/* eslint-disable @typescript-eslint/no-explicit-any */
import type { ReactNode } from "react";
import { vehicleCM } from "@/lib/character/format";

export function Section({
  title,
  children,
  empty,
}: {
  title: string;
  children: ReactNode;
  empty?: boolean;
}) {
  if (empty) return null;
  return (
    <section className="sheet-section">
      <h3>{title}</h3>
      {children}
    </section>
  );
}

export function GradeList({ items, tr }: { items: any[]; tr: (n: string) => string }) {
  const grades = Array.from(new Set(items.map((i) => Number(i.grade) || 0))).sort((a, b) => a - b);
  return (
    <ul className="sheet-list">
      {grades.map((g) => (
        <li key={g}>
          <b>等級 {g}</b>
          <span className="sheet-dim">
            {" "}
            {items
              .filter((i) => (Number(i.grade) || 0) === g)
              .map(
                (i) =>
                  `${tr(i.name)}${i.extra ? `（${tr(i.extra)}）` : ""}${i.kind === "art" ? "〔術〕" : ""}`,
              )
              .join("、")}
          </span>
        </li>
      ))}
    </ul>
  );
}

export function VehicleBlock({ v, tr }: { v: any; tr: (n: string) => string }) {
  const mods = (v.mods || []).filter((m: any) => !m.parent_id);
  const mounts = v.weapon_mounts || [];
  const sensors = v.sensors || [];
  const gear = (v.gear || []).filter((g: any) => !g.parent_id);
  const tracks = v.slot_tracks || [];
  return (
    <div className="sheet-block">
      <h4>
        {tr(v.name)}
        {v.seats ? `（座席 ${v.seats}）` : ""}
      </h4>
      <div className="sheet-derived-grid sheet-vehicle-stats">
        <div>
          <span>機動</span>
          <b>{v.handling || "-"}</b>
        </div>
        <div>
          <span>速度</span>
          <b>{v.speed || "-"}</b>
        </div>
        <div>
          <span>加速</span>
          <b>{v.accel || "-"}</b>
        </div>
        <div>
          <span>車体</span>
          <b>{v.body || "-"}</b>
        </div>
        <div>
          <span>装甲</span>
          <b>{v.armor || "-"}</b>
        </div>
        <div>
          <span>パイロット</span>
          <b>{v.pilot || "-"}</b>
        </div>
        <div>
          <span>センサー</span>
          <b>{v.sensor || "-"}</b>
        </div>
        <div>
          <span>物理CM</span>
          <b>{vehicleCM(v.body)}</b>
        </div>
      </div>
      {mods.length ? (
        <p className="sheet-note">
          改造:{" "}
          {mods
            .map((m: any) => `${tr(m.name)}${(m.rating || 0) > 1 ? ` R${m.rating}` : ""}`)
            .join("、")}
        </p>
      ) : null}
      {mounts.length ? (
        <p className="sheet-note">
          ウェポンマウント:{" "}
          {mounts
            .map(
              (m: any) =>
                `${tr(m.label || m.name)}${m.weapon_name ? `＝${tr(m.weapon_name)}` : "（空）"}`,
            )
            .join("、")}
        </p>
      ) : null}
      {sensors.length ? (
        <p className="sheet-note">センサー機器: {sensors.map((s: any) => tr(s.name)).join("、")}</p>
      ) : null}
      {gear.length ? (
        <p className="sheet-note">搭載ギア: {gear.map((g: any) => tr(g.name)).join("、")}</p>
      ) : null}
      {tracks.length ? (
        <p className="sheet-note">
          スロット: {tracks.map((s: any) => `${s.label} ${s.used}/${s.max}`).join(" ・ ")}
        </p>
      ) : null}
    </div>
  );
}
