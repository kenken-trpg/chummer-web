"use client";
import { useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import type {
  ElectronicModificationRecord,
  ElectronicPartsAllocation,
} from "@/lib/types/generated";
import type { InstalledGear } from "@/lib/types";

export function ConstructionRecordEditor({
  mod,
  character: ch,
  d,
  tr,
  ui,
  patch,
}: Pick<TabPanelProps, "character" | "d" | "tr" | "ui" | "patch"> & { mod: InstalledGear }) {
  const [note, setNote] = useState("");
  const records = ch.electronic_modification_records || [];
  const rec = records.find((r) => r.modification_id === mod.id && r.status !== "cancelled");
  const currentAllocations = rec?.allocations || [];
  const [allocations, setAllocations] = useState<ElectronicPartsAllocation[]>(currentAllocations);
  const allocated = allocations.reduce((n, a) => n + a.units, 0);
  const ownReservation = (sid: string) =>
    currentAllocations.filter((a) => a.source_id === sid).reduce((n, a) => n + a.units, 0);
  const sources = [
    ...(d.gear || [])
      .filter((r) => r.parts_available_units != null && !r.parts_supply)
      .map((r) => ({
        id: r.id,
        name: tr(r.name),
        units: (r.parts_available_units || 0) + ownReservation(r.id),
      })),
    ...(ch.electronic_parts_supplies || []).map((s) => ({
      id: s.id!,
      name: s.note || ui("gear.partsSupplies"),
      units:
        s.units -
        records
          .filter((r) => r.id !== rec?.id && (r.status === "completed" || r.status === "pending"))
          .flatMap((r) => r.allocations || [])
          .filter((a) => a.source_id === s.id)
          .reduce((n, a) => n + a.units, 0),
    })),
  ];
  const reasons: Record<string, Parameters<typeof ui>[0]> = {
    attributeExists: "gear.reason.attributeExists",
    attributeMissing: "gear.reason.attributeMissing",
    arrayRequired: "gear.reason.arrayRequired",
    personaExists: "gear.reason.personaExists",
    unsupportedRule: "gear.reason.unsupportedRule",
    invalidHost: "gear.reason.invalidHost",
    recordMismatch: "gear.reason.recordMismatch",
    modificationLimit: "gear.reason.modificationLimit",
    invalidParent: "gear.reason.invalidParent",
  };
  const save = (status: ElectronicModificationRecord["status"]) => {
    const record: ElectronicModificationRecord = {
      ...(rec || {
        id: crypto.randomUUID(),
        modification_id: mod.id,
        host_id: mod.modification_host_id || mod.parent_id || "",
        gear_id: mod.gear_id,
      }),
      status,
      required_units: mod.material_required_units || 0,
      allocations: status === "historical" ? [] : allocations,
      note,
    };
    patch({
      electronic_modification_records: [...records.filter((r) => r.id !== rec?.id), record],
    });
  };
  const pending = mod.modification_status === "pending";
  const completed =
    mod.modification_status === "completed" || mod.modification_status === "historical";
  return (
    <div>
      <p>
        {ui(
          pending
            ? "gear.constructionPending"
            : completed
              ? "gear.constructionCompleted"
              : "gear.constructionUnverified",
        )}
      </p>
      <p>
        {mod.material_required_units == null
          ? ui("gear.materialsUnsupported")
          : ui("gear.materialsCount", {
              required: mod.material_required_units / 4,
              allocated: allocated / 4,
              available: (mod.material_available_units || 0) / 4,
            })}
      </p>
      {mod.modification_reason ? (
        <p>
          {ui("gear.constructionReason", {
            reason: ui(reasons[mod.modification_reason] || "gear.reason.unsupportedRule"),
          })}
        </p>
      ) : null}
      {!completed ? (
        <>
          <p>
            {ui("gear.materialsShortfall", {
              count: Math.max(0, (mod.material_required_units || 0) - allocated) / 4,
            })}
          </p>
          {sources.map((s) => (
            <label key={s.id}>
              {s.name} ({s.units / 4})
              <input
                type="number"
                aria-label={`${tr(mod.name)}: ${s.name}`}
                min={0}
                max={Math.max(0, s.units) / 4}
                step={0.25}
                value={(allocations.find((a) => a.source_id === s.id)?.units || 0) / 4}
                onChange={(e) => {
                  const units = Number(e.target.value) * 4;
                  if (Number.isInteger(units) && units >= 0)
                    setAllocations([
                      ...allocations.filter((a) => a.source_id !== s.id),
                      ...(units ? [{ source_id: s.id, units }] : []),
                    ]);
                }}
              />
            </label>
          ))}
          <button className="btn" onClick={() => save("pending")}>
            {ui("gear.saveDraft")}
          </button>
          <button
            className="btn"
            disabled={
              mod.material_required_units == null ||
              Boolean(mod.modification_reason) ||
              allocated !== mod.material_required_units ||
              sources.some(
                (s) => (allocations.find((a) => a.source_id === s.id)?.units || 0) > s.units,
              )
            }
            onClick={() => save("completed")}
          >
            {ui("gear.completeConstruction")}
          </button>
        </>
      ) : null}
      <label>
        {ui("gear.constructionNote")}
        <input value={note} maxLength={500} onChange={(e) => setNote(e.target.value)} />
      </label>
      {!pending && !completed ? (
        <button className="btn" disabled={!note.trim()} onClick={() => save("historical")}>
          {ui("gear.confirmHistorical")}
        </button>
      ) : null}
      {completed && rec ? (
        <button
          className="btn"
          disabled={!note.trim()}
          onClick={() =>
            patch({
              electronic_modification_records: records.map((r) =>
                r.id === rec.id ? { ...r, status: "cancelled", note } : r,
              ),
            })
          }
        >
          {ui("gear.constructionCorrect")}
        </button>
      ) : null}
      <p className="muted">{ui("gear.constructionRemoveHelp")}</p>
    </div>
  );
}
