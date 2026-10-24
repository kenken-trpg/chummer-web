"use client";

import { useId, useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import { HelpTip } from "@/components/help/HelpTip";
import { KNOW_CATS, knowCatLabel } from "@/lib/character/constants";
import type { LifeModuleTransfer } from "@/lib/types";
import type { LifeModuleSkillPool } from "@/lib/types/life-modules";

type Props = Pick<TabPanelProps, "catalog" | "character" | "ui" | "patch"> & {
  pool: LifeModuleSkillPool;
  tr?: (name: string) => string;
};

export function LifeModuleSkillOverflow({
  catalog,
  character: ch,
  ui,
  patch,
  pool,
  tr = (s) => s,
}: Props) {
  const knowledge = pool.kind === "knowledge";
  const suggestionsId = useId();
  const [target, setTarget] = useState("");
  const [knowledgeTarget, setKnowledgeTarget] = useState("");
  const [knowledgeCategory, setKnowledgeCategory] = useState<(typeof KNOW_CATS)[number]>("Street");
  const [specific, setSpecific] = useState("");
  const [ranks, setRanks] = useState(1);
  const [busy, setBusy] = useState(false);
  const [failed, setFailed] = useState(false);
  const rows = (ch.life_module_transfers || []).filter(
    (row) =>
      row.entry_id === pool.entry_id &&
      row.source_skill_id === pool.source_skill_id &&
      (row.source_kind || "active") === (pool.kind || "active"),
  );
  const result = ch.derived.life_module_skills;
  const knowledgeName = knowledgeTarget.trim();
  const knownCategory =
    result?.knowledge_categories?.[knowledgeName] ||
    ch.knowledge_categories?.[knowledgeName] ||
    catalog.skills.knowledge.find((item) => item.name === knowledgeName)?.category;
  const knowledgeCapacity = Math.max(
    0,
    (result?.policy.knowledge_cap || 9) -
      (result?.free_knowledge[knowledgeName] || 0) -
      (ch.knowledge_skills[knowledgeName] || 0),
  );
  const knowledgeLegal =
    knowledgeName.length > 0 &&
    knowledgeName.length <= 200 &&
    knowledgeName !== pool.source_name &&
    !result?.native_languages.includes(knowledgeName) &&
    !ch.native_languages?.includes(knowledgeName) &&
    !/[\[\]]/.test(knowledgeName) &&
    (!knownCategory || knownCategory === knowledgeCategory) &&
    !rows.some((row) => row.destination_skill_id.trim() === knowledgeName) &&
    Number.isInteger(ranks) &&
    ranks > 0 &&
    ranks <= Math.min(pool.remaining, knowledgeCapacity);
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
      setKnowledgeTarget("");
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
          lines={[
            {
              label: ui(
                knowledge ? "help.lifeModule.knowledgeOverflow" : "help.lifeModule.overflow",
              ),
            },
          ]}
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
              knowledge
                ? row.destination_skill_id
                : pool.candidates.find((c) => c.skill_id === row.destination_skill_id)?.name ||
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
          {knowledge ? (
            <>
              <label className="life-field">
                {ui("life.transfer.knowledgeTarget")}
                <input
                  value={knowledgeTarget}
                  maxLength={200}
                  list={suggestionsId}
                  onChange={(e) => {
                    const name = e.target.value;
                    setKnowledgeTarget(name);
                    const category =
                      result?.knowledge_categories?.[name] ||
                      ch.knowledge_categories?.[name] ||
                      catalog.skills.knowledge.find((item) => item.name === name)?.category;
                    if (category && KNOW_CATS.some((cat) => cat === category)) {
                      setKnowledgeCategory(category as (typeof KNOW_CATS)[number]);
                    }
                  }}
                />
                <datalist id={suggestionsId}>
                  {Array.from(
                    new Set([
                      ...catalog.skills.knowledge.map((item) => item.name),
                      ...Object.keys(result?.free_knowledge || {}),
                      ...Object.keys(ch.knowledge_skills),
                    ]),
                  ).map((name) => (
                    <option key={name} value={name} />
                  ))}
                </datalist>
              </label>
              <label className="life-field">
                {ui("life.transfer.knowledgeCategory")}
                <select
                  value={knowledgeCategory}
                  onChange={(e) =>
                    setKnowledgeCategory(e.target.value as (typeof KNOW_CATS)[number])
                  }
                >
                  {KNOW_CATS.map((cat) => (
                    <option key={cat} value={cat}>
                      {knowCatLabel(cat, ui)}
                    </option>
                  ))}
                </select>
              </label>
            </>
          ) : (
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
          )}
          {!knowledge && candidate?.specific_required && (
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
              max={Math.min(
                pool.remaining,
                knowledge ? knowledgeCapacity : candidate?.capacity || pool.remaining,
              )}
              step={1}
              value={ranks}
              onChange={(e) => setRanks(Number(e.target.value))}
            />
          </label>
          <button
            type="button"
            disabled={!(knowledge ? knowledgeLegal : legal) || busy || !!ch.career}
            onClick={() =>
              save([
                ...(ch.life_module_transfers || []),
                {
                  id: crypto.randomUUID(),
                  entry_id: pool.entry_id,
                  source_skill_id: pool.source_skill_id,
                  grant_fingerprint: pool.grant_fingerprint,
                  source_kind: knowledge ? "knowledge" : "active",
                  destination_skill_id: knowledge ? knowledgeName : target,
                  destination_specific: knowledge ? "" : specific.trim(),
                  destination_category: knowledge ? knowledgeCategory : null,
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
