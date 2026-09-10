"use client";

import type { Catalog, Character, MentorInfo } from "@/lib/types";
import { useUiText } from "@/lib/i18n";
import { limitLabel } from "@/lib/character/format";

export function MentorPicker({
  catalog,
  mentor,
  ch,
  tr,
  onPatch,
  paragon = false,
}: {
  catalog: Catalog;
  mentor?: MentorInfo | null;
  ch: Character;
  tr: (name: string) => string;
  onPatch: (body: Record<string, unknown>) => void;
  /** Pick out of `catalog.paragons` instead — a technomancer's mentor spirit
   * (KC p.102). It shares `mentor_id`, because no character can have both. */
  paragon?: boolean;
}) {
  const { ui } = useUiText();
  const options = (paragon ? catalog.paragons : catalog.mentors) || [];
  return (
    <div className="cyber-item">
      <div>
        <b>{ui(paragon ? "mentor.paragonTitle" : "mentor.title")}</b>
        <div className="muted">
          {mentor ? `${tr(mentor.name)} / ${mentor.source}` : ui("mentor.none")}
        </div>
        <div className="cyber-controls">
          <label>
            {ui(paragon ? "mentor.paragonLabel" : "mentor.label")}
            <select
              value={ch.mentor_id || ""}
              onChange={(e) =>
                onPatch({ mentor_id: e.target.value, mentor_choices: [], mentor_extras: {} })
              }
            >
              <option value="">{ui("common.choose")}</option>
              {options.map((item) => (
                <option key={item.id} value={item.id}>
                  {tr(item.name)}
                </option>
              ))}
            </select>
          </label>
        </div>
        {mentor?.advantage ? <p className="muted">{mentor.advantage}</p> : null}
        {(mentor?.choices || []).map((choice) => (
          <label key={choice.name} className="skill-row">
            <input
              type="checkbox"
              checked={choice.selected}
              onChange={() => {
                const current = new Set(
                  ch.mentor_choices ||
                    mentor!.choices.filter((row) => row.selected).map((row) => row.name),
                );
                if (choice.selected) current.delete(choice.name);
                else {
                  if (choice.set) {
                    mentor!.choices
                      .filter((row) => row.set === choice.set)
                      .forEach((row) => current.delete(row.name));
                  }
                  current.add(choice.name);
                }
                onPatch({ mentor_choices: [...current] });
              }}
            />
            <span>{choice.name}</span>
            {choice.extra_options.length ? (
              <select
                value={choice.extra || ""}
                onChange={(e) =>
                  onPatch({
                    mentor_extras: { ...(ch.mentor_extras || {}), [choice.name]: e.target.value },
                  })
                }
              >
                <option value="">{ui("mentor.chooseTarget")}</option>
                {choice.extra_options.map((name) => (
                  <option key={name} value={name}>
                    {tr(name)}
                  </option>
                ))}
              </select>
            ) : null}
            {/* A power the choice grants may ask for a target of its own once
                the choice's own select is spent on which power it grants. */}
            {(choice.power_targets || []).map((target) => (
              <select
                key={target.key}
                aria-label={`${tr(target.power)} ${ui("mentor.chooseTarget")}`}
                value={target.extra || ""}
                onChange={(e) =>
                  onPatch({
                    mentor_extras: { ...(ch.mentor_extras || {}), [target.key]: e.target.value },
                  })
                }
              >
                <option value="">{ui("mentor.chooseTarget")}</option>
                {target.options.map((name) => (
                  <option key={name} value={name}>
                    {target.kind === "limit" ? limitLabel(name, ui) : tr(name)}
                  </option>
                ))}
              </select>
            ))}
          </label>
        ))}
      </div>
    </div>
  );
}
