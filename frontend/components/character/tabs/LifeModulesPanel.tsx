"use client";
import type { MsgKey } from "@/lib/i18n";
import type { TabPanelProps } from "@/components/character/types";
import { lifeModuleRequirementsMet, lifeModuleRequirementText } from "@/lib/character/life-modules";

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
  patch,
}: Pick<TabPanelProps, "catalog" | "character" | "ui" | "patch">) {
  const rows = catalog.life_modules || [];
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
  function remove(index: number) {
    const next: Record<string, string> = {};
    for (const [key, value] of Object.entries(choices)) {
      const [position, slot] = key.split(":");
      const occurrence = Number(position);
      if (occurrence !== index)
        next[`${occurrence > index ? occurrence - 1 : occurrence}:${slot}`] = value;
    }
    void patch({ life_modules: selected.filter((_, i) => i !== index), life_module_choices: next });
  }
  return (
    <div className="card">
      <h2>{ui("life.method")}</h2>
      <p className="warn">{ui("life.experimental")}</p>
      <p className="muted">{ui("life.note")}</p>
      <p>
        {ui("life.total", {
          karma: selected.reduce(
            (sum, id) => sum + (rows.find((row) => row.id === id)?.karma || 0),
            0,
          ),
        })}
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
      {STAGES.map((stage) => {
        const candidates = rows.filter(
          (row) => row.stage === stage && (!books.length || books.includes(row.source)),
        );
        const taken = selected.some((id) => rows.find((row) => row.id === id)?.stage === stage);
        return (
          <section key={stage}>
            <h3>{ui(`life.stage.${stage}` as MsgKey)}</h3>
            {selected.map((id, index) => {
              const row = rows.find((item) => item.id === id);
              if (!row || row.stage !== stage) return null;
              return (
                <div key={`${index}:${id}`}>
                  <strong>{row.name}</strong> {row.parent && `(${row.parent})`} · {row.karma} Karma
                  · {row.source} {row.page}
                  <button
                    disabled={ch.career}
                    onClick={() => remove(index)}
                    aria-label={`${row.name}: ${ui("life.remove")}`}
                  >
                    ×
                  </button>
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
                  {row.choices.map((choice) => (
                    <label key={choice.key}>
                      {ui("life.choice", {
                        name: row.name,
                        kind: choice.name || ui(`life.kind.${choice.kind}` as MsgKey),
                      })}
                      {choice.options.length ? (
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
                        <input
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
                      )}
                    </label>
                  ))}
                </div>
              );
            })}
            <label>
              {ui(`life.stage.${stage}` as MsgKey)}: {ui("life.pick")}
              <select
                value=""
                disabled={ch.career || (taken && STAGES.indexOf(stage) < 3)}
                onChange={(event) => {
                  if (event.target.value)
                    void patch({ life_modules: [...selected, event.target.value] });
                }}
              >
                <option value="">{ui("life.pick")}</option>
                {candidates.map((row) => {
                  const met = lifeModuleRequirementsMet(row.required || [], ch, catalog);
                  return (
                    <option
                      key={row.id}
                      value={row.id}
                      disabled={row.unsupported.length > 0 || !met}
                    >
                      {row.parent ? `${row.parent} / ` : ""}
                      {row.name} ({row.karma})
                      {row.unsupported.length > 0 ? ` — ${ui("life.unsupported")}` : ""}
                      {!!row.required?.length
                        ? ` — ${ui("life.requires", { requirements: lifeModuleRequirementText(row.required) })}`
                        : ""}
                      {!met ? ` — ${ui("life.requirementUnmet")}` : ""}
                    </option>
                  );
                })}
              </select>
            </label>
            {!candidates.length && <p className="muted">{ui("life.empty")}</p>}
          </section>
        );
      })}
    </div>
  );
}
