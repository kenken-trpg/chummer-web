"use client";

import { useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import { HelpTip } from "@/components/help/HelpTip";
import type { LifeModuleTransfer } from "@/lib/types";
import type { LifeModuleSkillPool } from "@/lib/types/life-modules";

type Props = Pick<TabPanelProps, "character" | "ui" | "patch"> & {
  pool: LifeModuleSkillPool;
  tr?: (name: string) => string;
};

export function LifeModuleSkillOverflow({ character: ch, ui, patch, pool, tr = (s) => s }: Props) {
  const [target, setTarget] = useState("");
  const [specific, setSpecific] = useState("");
  const [ranks, setRanks] = useState(1);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const rows = (ch.life_module_transfers || []).filter(
    (row) => row.entry_id === pool.entry_id && row.source_skill_id === pool.source_skill_id,
  );
  const candidate = pool.candidates.find((c) => c.skill_id === target);
  const legal =
    candidate &&
    !candidate.unavailable_reason &&
    candidate.capacity > 0 &&
    Number.isInteger(ranks) &&
    ranks > 0 &&
    ranks <= Math.min(pool.remaining, candidate.capacity) &&
    (!candidate.specific_required || (specific.trim() && !/[\[\]]/.test(specific))) &&
    !rows.some(
      (row) =>
        row.destination_skill_id === target &&
        (row.destination_specific || "").trim().toLowerCase() === specific.trim().toLowerCase(),
    );

  async function save(next: LifeModuleTransfer[]) {
    setBusy(true);
    setFailed(false);
    try {
      await patch({ life_module_transfers: next });
      setTarget("");
      setSpecific("");
      setRanks(1);
    } catch {
      setFailed(true);
    } finally {
      setBusy(false);
    }
  }

  return (
    <fieldset disabled={ch.career || busy} className="life-overflow">
      <legend>
        <HelpTip
          label={ui("help.open", {
            label: ui("life.transfer.title", { name: tr(pool.source_name) }),
          })}
          lines={[{ label: ui("help.lifeModule.overflow") }]}
        >
          {ui("life.transfer.title", { name: tr(pool.source_name) })}
        </HelpTip>
      </legend>
      <p>
        {ui("life.transfer.source", {
          before: pool.before,
          grant: pool.grant,
          kept: pool.kept,
          total: pool.total,
          remaining: pool.remaining,
        })}
      </p>
      {pool.provisional && <p className="warn">{ui("life.transfer.provisional")}</p>}
      {pool.status === "invalid" && <p className="error">{ui("life.transfer.invalid")}</p>}
      {pool.unallocatable > 0 && (
        <p className="warn">{ui("life.transfer.lost", { count: pool.unallocatable })}</p>
      )}
      {rows.map((row) => (
        <div key={row.id} className="life-entry-heading">
          <span>
            {tr(
              pool.candidates.find((c) => c.skill_id === row.destination_skill_id)?.name ||
                ui("life.transfer.unknown"),
            )}
            {row.destination_specific ? ` (${row.destination_specific})` : ""}: +{row.ranks}
          </span>
          <button
            type="button"
            onClick={() =>
              save((ch.life_module_transfers || []).filter((item) => item.id !== row.id))
            }
          >
            {ui("life.transfer.remove")}
          </button>
        </div>
      ))}
      {pool.remaining > 0 && pool.status !== "invalid" ? (
        <div className="life-choices">
          <label className="life-field">
            {ui("life.transfer.target")}
            <select
              value={target}
              onChange={(e) => {
                setTarget(e.target.value);
                setSpecific("");
              }}
            >
              <option value="">{ui("life.pending")}</option>
              {pool.candidates.map((c) => (
                <option
                  key={c.skill_id}
                  value={c.skill_id}
                  disabled={!!c.unavailable_reason || c.capacity === 0}
                >
                  {tr(c.name)} ({c.attribute}, +{c.capacity})
                </option>
              ))}
            </select>
          </label>
          {candidate?.specific_required && (
            <label className="life-field">
              {ui("life.transfer.specific")}
              <input
                value={specific}
                maxLength={200}
                onChange={(e) => setSpecific(e.target.value)}
              />
            </label>
          )}
          <label className="life-field">
            {ui("life.transfer.ranks")}
            <input
              type="number"
              min={1}
              max={Math.min(pool.remaining, candidate?.capacity || pool.remaining)}
              step={1}
              value={ranks}
              onChange={(e) => setRanks(Number(e.target.value))}
            />
          </label>
          <button
            type="button"
            disabled={!legal || busy || !!ch.career}
            onClick={() =>
              save([
                ...(ch.life_module_transfers || []),
                {
                  id: crypto.randomUUID(),
                  entry_id: pool.entry_id,
                  source_skill_id: pool.source_skill_id,
                  grant_fingerprint: pool.grant_fingerprint,
                  destination_skill_id: target,
                  destination_specific: specific.trim(),
                  ranks,
                },
              ])
            }
          >
            {ui("life.transfer.add")}
          </button>
        </div>
      ) : null}
      {failed && (
        <p className="error" role="alert">
          {ui("life.transfer.failed")}
        </p>
      )}
    </fieldset>
  );
}
