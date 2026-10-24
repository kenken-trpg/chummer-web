"use client";
import { useId, useRef, useState } from "react";
import { LifeModulePicker } from "./LifeModulePicker";
import { LifeModuleSkillOverflow } from "./LifeModuleSkillOverflow";
import type { MsgKey } from "@/lib/i18n";
import type { TabPanelProps } from "@/components/character/types";
import { sourceBit } from "@/lib/character/format";
import { HelpTip } from "@/components/help/HelpTip";
import {
  lifeModuleAlreadyTaken,
  lifeModuleOrderPatch,
  lifeModuleRequirementsMet,
  lifeModuleRequirementText,
} from "@/lib/character/life-modules";

const STAGES = [
  "Nationality",
  "Formative Years",
  "Teen Years",
  "Further Education",
  "Real Life",
] as const;

export function LifeModulesPanel({
  catalog,
  character: ch,
  ui,
  patch: rawPatch,
  tr = (s) => s,
}: Pick<TabPanelProps, "catalog" | "character" | "ui" | "patch"> & { tr?: TabPanelProps["tr"] }) {
  const [pending, setPending] = useState(false);
  const sending = useRef(false);
  async function patch(body: Record<string, unknown>) {
    if (sending.current) return;
    sending.current = true;
    setPending(true);
    try {
      await rawPatch(body);
    } finally {
      sending.current = false;
      setPending(false);
    }
  }
  const rows = catalog.life_modules || [];
  const optionListId = useId();
  const [search, setSearch] = useState("");
  const query = search.trim().toLowerCase();
  const selected = ch.life_modules || [];
  const choices = ch.life_module_choices || {};
  const books = ch.settings?.books || [];
  const freePositive = selected.reduce(
    (sum, id) => sum + (rows.find((row) => row.id === id)?.free_positive_qualities || 0),
    0,
  );
  const freeNegative = selected.reduce(
    (sum, id) => sum + (rows.find((row) => row.id === id)?.free_negative_qualities || 0),
    0,
  );
  const skillResult = ch.derived.life_module_skills;
  function remove(index: number) {
    void patch(
      lifeModuleOrderPatch(
        ch,
        selected.map((_, i) => i).filter((i) => i !== index),
      ),
    );
  }
  function move(index: number, direction: number) {
    const stage = rows.find((row) => row.id === selected[index])?.stage;
    const neighbors = selected
      .map((id, i) => ({ i, stage: rows.find((row) => row.id === id)?.stage }))
      .filter((item) => item.stage === stage)
      .map((item) => item.i);
    const at = neighbors.indexOf(index);
    const other = neighbors[at + direction];
    if (other === undefined) return;
    const order = selected.map((_, i) => i);
    [order[index], order[other]] = [order[other], order[index]];
    void patch(lifeModuleOrderPatch(ch, order));
  }
  return (
    <fieldset
      className="card life-modules"
      disabled={pending}
      aria-label={ui("life.method")}
      style={{ minWidth: 0 }}
    >
      <h2>{ui("life.method")}</h2>
      <p className="warn">{ui("life.experimental")}</p>
      <p className="muted">{ui("life.note")}</p>
      {skillResult && (
        <p className="muted">
          <HelpTip
            label={ui("help.open", { label: ui("life.transfer.capsLabel") })}
            lines={[
              { label: ui("help.lifeModule.caps") },
              { label: ui("help.lifeModule.overflow") },
            ]}
          >
            {ui("life.transfer.caps", {
              active: skillResult.policy.active_cap,
              knowledge: skillResult.policy.knowledge_cap,
            })}
          </HelpTip>
        </p>
      )}
      {(ch.life_module_transfers || [])
        .filter(
          (transfer) =>
            !skillResult?.pools.some(
              (pool) =>
                pool.entry_id === transfer.entry_id &&
                pool.source_skill_id === transfer.source_skill_id,
            ),
        )
        .map((transfer) => (
          <div className="error" key={transfer.id}>
            {ui("life.transfer.orphan", { ranks: transfer.ranks })}
            <button
              disabled={ch.career}
              onClick={() =>
                patch({
                  life_module_transfers: (ch.life_module_transfers || []).filter(
                    (row) => row.id !== transfer.id,
                  ),
                })
              }
            >
              {ui("life.transfer.remove")}
            </button>
          </div>
        ))}
      <div className="life-summary">
        <p>
          <HelpTip
            label={ui("help.open", { label: ui("life.totalLabel") })}
            lines={[
              { label: ui("help.lifeModule.karma") },
              ...(freePositive || freeNegative
                ? [{ label: ui("help.lifeModule.freeQuality") }]
                : []),
            ]}
          >
            {ui("life.total", {
              karma: selected.reduce(
                (sum, id) => sum + (rows.find((row) => row.id === id)?.karma || 0),
                0,
              ),
            })}
          </HelpTip>
        </p>
        <p>
          {ui("life.nuyen", {
            amount: selected.reduce(
              (sum, id) => sum + (rows.find((row) => row.id === id)?.nuyen || 0),
              0,
            ),
          })}
        </p>
        {freePositive || freeNegative ? (
          <p>{ui("life.freeQuality", { positive: freePositive, negative: freeNegative })}</p>
        ) : null}
      </div>
      <label className="life-field">
        {ui("life.search")}
        <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} />
      </label>
      {selected.map((id, index) =>
        rows.some((row) => row.id === id) ? null : (
          <div className="life-entry" key={`${index}:${id}`}>
            <p className="error">{ui("engine.life.unknown", { name: id })}</p>
            <button
              disabled={ch.career}
              onClick={() => remove(index)}
              aria-label={`${id}: ${ui("life.remove")}`}
            >
              {ui("life.remove")}
            </button>
          </div>
        ),
      )}
      {STAGES.map((stage) => {
        const candidates = rows.filter(
          (row) => row.stage === stage && (!books.length || books.includes(row.source)),
        );
        const filtered = candidates.filter((row) =>
          [row.name, row.parent, row.story, row.source].some((text) =>
            text.toLowerCase().includes(query),
          ),
        );
        const taken = selected.some((id) => rows.find((row) => row.id === id)?.stage === stage);
        return (
          <section className="life-stage" key={stage}>
            <div className="life-stage-heading">
              <h3>{stage}</h3>
              <span className={taken ? "life-status" : "muted"}>
                {ui(taken ? "life.stageSelected" : "life.stagePending")}
              </span>
            </div>
            {STAGES.indexOf(stage) >= 3 && <p className="muted">{ui("life.repeatable")}</p>}
            {selected.map((id, index) => {
              const row = rows.find((item) => item.id === id);
              if (!row || row.stage !== stage) return null;
              return (
                <div className="life-entry" key={`${index}:${id}`}>
                  <div className="life-entry-heading">
                    <div>
                      <h4>{row.name}</h4>
                      {row.parent && <p className="muted">{row.parent}</p>}
                      <p className="muted">
                        {row.karma} Karma · {sourceBit(row, ui)}
                      </p>
                    </div>
                    <button
                      disabled={ch.career}
                      onClick={() => remove(index)}
                      aria-label={`${row.name}: ${ui("life.remove")}`}
                    >
                      {ui("life.remove")}
                    </button>
                  </div>
                  {ch.life_module_rules_version === 2 && STAGES.indexOf(stage) >= 3 && (
                    <div>
                      <button
                        disabled={
                          ch.career ||
                          !selected
                            .slice(0, index)
                            .some((id) => rows.find((r) => r.id === id)?.stage === stage)
                        }
                        onClick={() => move(index, -1)}
                      >
                        {ui("life.moveEarlier")}
                      </button>
                      <button
                        disabled={
                          ch.career ||
                          !selected
                            .slice(index + 1)
                            .some((id) => rows.find((r) => r.id === id)?.stage === stage)
                        }
                        onClick={() => move(index, 1)}
                      >
                        {ui("life.moveLater")}
                      </button>
                    </div>
                  )}
                  {skillResult?.pools
                    .filter((pool) => pool.entry_id === ch.life_module_entry_ids?.[index])
                    .map((pool) => (
                      <LifeModuleSkillOverflow
                        key={`${pool.key}:${pool.grant_fingerprint}`}
                        catalog={catalog}
                        character={ch}
                        pool={pool}
                        ui={ui}
                        patch={patch}
                        tr={tr}
                      />
                    ))}
                  {skillResult?.losses
                    .filter((loss) => loss.entry_id === ch.life_module_entry_ids?.[index])
                    .map((loss) => (
                      <p className="warn" key={loss.skill_key}>
                        {ui("life.transfer.loss", {
                          name: tr(
                            catalog.skills.skills.find((s) => `skill:${s.id}` === loss.skill_key)
                              ?.name || "",
                          ),
                          count: loss.lost,
                        })}
                      </p>
                    ))}
                  {row.story && (
                    <details className="life-story">
                      <summary>{ui("life.description")}</summary>
                      <p>{row.story}</p>
                    </details>
                  )}
                  {lifeModuleAlreadyTaken(
                    row,
                    { ...ch, life_modules: selected.slice(0, index) },
                    catalog,
                  ) && <p className="error">{ui("life.alreadyTaken")}</p>}
                  {row.unsupported.length > 0 && <p className="error">{ui("life.unsupported")}</p>}
                  {!!row.required?.length && (
                    <p
                      className={
                        lifeModuleRequirementsMet(row.required, ch, catalog) ? "muted" : "error"
                      }
                    >
                      {ui("life.requires", {
                        requirements: lifeModuleRequirementText(row.required),
                      })}
                      {!lifeModuleRequirementsMet(row.required, ch, catalog) &&
                        ` — ${ui("life.requirementUnmet")}`}
                    </p>
                  )}
                  <div className="life-choices">
                    {row.choices.map((choice) => (
                      <label className="life-field" key={choice.key}>
                        {ui("life.choice", {
                          name: row.name,
                          kind: choice.name || ui(`life.kind.${choice.kind}` as MsgKey),
                        })}
                        {choice.options.length && !choice.allow_custom ? (
                          <select
                            disabled={ch.career}
                            value={choices[`${index}:${choice.key}`] || ""}
                            onChange={(event) =>
                              patch({
                                life_module_choices: {
                                  ...choices,
                                  [`${index}:${choice.key}`]: event.target.value,
                                },
                              })
                            }
                          >
                            <option value="">{ui("life.pending")}</option>
                            {choice.options.map((option) => (
                              <option key={option} value={option}>
                                {option}
                              </option>
                            ))}
                          </select>
                        ) : (
                          <>
                            <input
                              type="text"
                              list={
                                choice.allow_custom
                                  ? `${optionListId}-${index}-${choice.key}`
                                  : undefined
                              }
                              disabled={ch.career}
                              value={choices[`${index}:${choice.key}`] || ""}
                              onChange={(event) =>
                                patch({
                                  life_module_choices: {
                                    ...choices,
                                    [`${index}:${choice.key}`]: event.target.value,
                                  },
                                })
                              }
                            />
                            {choice.allow_custom && (
                              <datalist id={`${optionListId}-${index}-${choice.key}`}>
                                {choice.options.map((option) => (
                                  <option key={option} value={option} />
                                ))}
                              </datalist>
                            )}
                          </>
                        )}
                      </label>
                    ))}
                  </div>
                </div>
              );
            })}
            {!!filtered.length && (
              <LifeModulePicker
                key={ch.id}
                stage={stage}
                candidates={filtered}
                taken={taken}
                repeatable={STAGES.indexOf(stage) >= 3}
                catalog={catalog}
                character={ch}
                ui={ui}
                patch={patch}
              />
            )}
            {!candidates.length && <p className="muted">{ui("life.empty")}</p>}
            {!!candidates.length && !filtered.length && (
              <p className="muted">{ui("life.noMatches")}</p>
            )}
          </section>
        );
      })}
    </fieldset>
  );
}
