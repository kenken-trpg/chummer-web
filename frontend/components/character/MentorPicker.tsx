"use client";

import type { Catalog, Character, MentorInfo } from "@/lib/types";

export function MentorPicker({
  catalog,
  mentor,
  ch,
  tr,
  onPatch,
}: {
  catalog: Catalog;
  mentor?: MentorInfo | null;
  ch: Character;
  tr: (name: string) => string;
  onPatch: (body: Record<string, unknown>) => void;
}) {
  return (
    <div className="cyber-item">
      <div>
        <b>メンタースピリット</b>
        <div className="muted">{mentor ? `${tr(mentor.name)} / ${mentor.source}` : "未選択"}</div>
        <div className="cyber-controls">
          <label>
            メンター
            <select value={ch.mentor_id || ""} onChange={(e) => onPatch({ mentor_id: e.target.value, mentor_choices: [], mentor_extras: {} })}>
              <option value="">選択してください</option>
              {(catalog.mentors || []).map((item) => (
                <option key={item.id} value={item.id}>{tr(item.name)}</option>
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
                const current = new Set(ch.mentor_choices || mentor!.choices.filter((row) => row.selected).map((row) => row.name));
                if (choice.selected) current.delete(choice.name);
                else {
                  if (choice.set) {
                    mentor!.choices.filter((row) => row.set === choice.set).forEach((row) => current.delete(row.name));
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
                onChange={(e) => onPatch({ mentor_extras: { ...(ch.mentor_extras || {}), [choice.name]: e.target.value } })}
              >
                <option value="">対象を選択</option>
                {choice.extra_options.map((name) => (
                  <option key={name} value={name}>{tr(name)}</option>
                ))}
              </select>
            ) : null}
          </label>
        ))}
      </div>
    </div>
  );
}
