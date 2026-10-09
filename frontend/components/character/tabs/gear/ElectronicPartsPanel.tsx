"use client";
import { useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import type { ElectronicPartsSupply } from "@/lib/types/generated";

const PARTS = ["f56affe6-0159-4f7a-ba4d-b5283bd25c44", "ec53ae4e-086f-4817-8cc2-ec574aa7cd51"];

export function ElectronicPartsPanel({
  catalog,
  character: ch,
  d,
  tr,
  ui,
  patch,
}: Pick<TabPanelProps, "catalog" | "character" | "d" | "tr" | "ui" | "patch">) {
  const [historyNote, setHistoryNote] = useState("");
  const [kind, setKind] = useState<NonNullable<ElectronicPartsSupply["kind"]>>("salvaged");
  const [packs, setPacks] = useState(1);
  const [note, setNote] = useState("");
  const [equipment, setEquipment] = useState("");
  const [purchase, setPurchase] = useState(PARTS[0]);
  const [qty, setQty] = useState(1);
  const supplies = ch.electronic_parts_supplies || [];
  const records = ch.electronic_modification_records || [];
  const goods = (catalog.gear || []).filter((r) => PARTS.includes(r.id));
  const product = goods.find((r) => r.id === purchase);
  const sourceUsage = (id: string, status: string) =>
    records
      .filter((r) => r.status === status)
      .flatMap((r) => r.allocations || [])
      .filter((a) => a.source_id === id)
      .reduce((n, a) => n + a.units, 0);
  return (
    <details>
      <summary>{ui("gear.partsSupplies")}</summary>
      <p className="muted">{ui("gear.partsExportLimit")}</p>
      {(d.gear || [])
        .filter((r) => r.parts_purchased_units != null && !r.parts_supply)
        .map((r) => (
          <p key={r.id}>
            {tr(r.name)}:{" "}
            {ui("gear.partsRemaining", {
              remaining: (r.parts_remaining_units || 0) / 4,
              purchased: (r.parts_purchased_units || 0) / 4,
              used: (r.parts_used_units || 0) / 4,
              reserved: (r.parts_reserved_units || 0) / 4,
            })}{" "}
            / {r.nuyen.toLocaleString()}¥
          </p>
        ))}
      {supplies.map((s) => (
        <p key={s.id}>
          {ui(
            s.kind === "equipment"
              ? "gear.partsEquipment"
              : s.kind === "gm"
                ? "gear.partsGm"
                : "gear.partsSalvaged",
          )}
          : {s.note} /{" "}
          {ui("gear.partsRemaining", {
            remaining: (s.units - sourceUsage(s.id!, "completed")) / 4,
            purchased: s.units / 4,
            used: sourceUsage(s.id!, "completed") / 4,
            reserved: sourceUsage(s.id!, "pending") / 4,
          })}
        </p>
      ))}
      <label>
        {ui("gear.partsSupplyKind")}
        <select value={kind} onChange={(e) => setKind(e.target.value as typeof kind)}>
          <option value="salvaged">{ui("gear.partsSalvaged")}</option>
          <option value="equipment">{ui("gear.partsEquipment")}</option>
          <option value="gm">{ui("gear.partsGm")}</option>
        </select>
      </label>
      {kind === "equipment" ? (
        <label>
          {ui("common.target")}
          <select
            value={equipment}
            onChange={(e) => {
              const selected = (d.gear || []).find((r) => r.id === e.target.value);
              setEquipment(e.target.value);
              if (selected)
                setPacks(
                  (selected.qty || 1) *
                    (selected.gear_id === "4edec80a-e8df-4817-9728-4a6fc04d183e" ? 2 : 10),
                );
            }}
          >
            <option value="">{ui("common.selectShort")}</option>
            {(d.gear || [])
              .filter(
                (r) =>
                  [
                    "4edec80a-e8df-4817-9728-4a6fc04d183e",
                    "d0c85aa4-5686-452b-9f1a-7c603ac43258",
                  ].includes(r.gear_id) &&
                  r.extra === "Hardware" &&
                  !supplies.some((s) => s.equipment_id === r.id),
              )
              .map((r) => (
                <option key={r.id} value={r.id}>
                  {tr(r.name)}
                </option>
              ))}
          </select>
        </label>
      ) : null}
      <label>
        {ui("gear.materialsUnits")}
        <input
          type="number"
          min={0.25}
          max={25000}
          step={0.25}
          value={packs}
          onChange={(e) => setPacks(Number(e.target.value))}
        />
      </label>
      <label>
        {ui("gear.constructionNote")}
        <input value={note} maxLength={500} onChange={(e) => setNote(e.target.value)} />
      </label>
      <button
        className="btn"
        disabled={
          !note.trim() ||
          packs <= 0 ||
          !Number.isInteger(packs * 4) ||
          (kind === "equipment" && !equipment)
        }
        onClick={() => {
          patch({
            electronic_parts_supplies: [
              ...supplies,
              {
                id: crypto.randomUUID(),
                kind,
                units: packs * 4,
                note,
                equipment_id: kind === "equipment" ? equipment : null,
              },
            ],
          });
          setNote("");
        }}
      >
        {ui("gear.partsSupplyAdd")}
      </button>
      {goods.length ? (
        <div>
          <label>
            {ui("gear.partsPurchase")}
            <select value={purchase} onChange={(e) => setPurchase(e.target.value)}>
              {goods.map((r) => (
                <option key={r.id} value={r.id}>
                  {tr(r.name)}
                </option>
              ))}
            </select>
          </label>
          <label>
            {ui("gear.partsPurchaseQty")}
            <input
              type="number"
              value={qty}
              min={1}
              max={999}
              onChange={(e) => setQty(Number(e.target.value))}
            />
          </label>
          <p>
            {ui("gear.partsPurchaseReview", {
              packs: qty * (purchase === PARTS[1] ? 5 : 1),
              cost: Number(product?.cost || 0) * qty,
            })}
          </p>
          <button
            className="btn"
            disabled={!Number.isInteger(qty) || qty < 1 || qty > 999}
            onClick={() =>
              patch({ gear: [...(ch.gear || []), { gear_id: purchase, qty, rating: 1 }] })
            }
          >
            {ui("gear.partsPurchase")}
          </button>
        </div>
      ) : null}
      <b>{ui("gear.partsHistory")}</b>
      <label>
        {ui("gear.constructionNote")}
        <input
          value={historyNote}
          maxLength={500}
          onChange={(e) => setHistoryNote(e.target.value)}
        />
      </label>
      {records.map((r) => (
        <p key={r.id}>
          {tr((catalog.gear || []).find((g) => g.id === r.gear_id)?.name || r.gear_id)} /{" "}
          {ui(
            r.status === "pending"
              ? "gear.constructionPending"
              : r.status === "cancelled"
                ? "gear.constructionCancelled"
                : r.status === "historical"
                  ? "gear.constructionHistorical"
                  : "gear.constructionCompleted",
          )}{" "}
          / {(r.required_units || 0) / 4} / {r.note}
          {!(ch.gear || []).some((g) => g.id === r.modification_id)
            ? ` / ${ui("gear.constructionMissing")}`
            : ""}
          {(r.status === "completed" || r.status === "historical") &&
          !(ch.gear || []).some((g) => g.id === r.modification_id) ? (
            <button
              className="btn"
              disabled={!historyNote.trim()}
              onClick={() =>
                patch({
                  electronic_modification_records: records.map((saved) =>
                    saved.id === r.id
                      ? { ...saved, status: "cancelled", note: historyNote }
                      : saved,
                  ),
                })
              }
            >
              {ui("gear.constructionCorrect")}
            </button>
          ) : null}
        </p>
      ))}
    </details>
  );
}
