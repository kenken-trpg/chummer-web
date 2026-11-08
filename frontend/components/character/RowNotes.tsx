"use client";
import { useState } from "react";
import type { TabPanelProps } from "@/components/character/types";
import { editRow } from "@/lib/character/rows";
import type { UiFn } from "@/lib/i18n";
import type { Character } from "@/lib/types";

type Field = "notes" | "nickname";
type PlayerText = { notes?: string | null; nickname?: string | null };

/** The lists whose rows hold a note (Chummer's `<notes>`). */
export type NotedBucket =
  | "cyberware"
  | "bioware"
  | "armor"
  | "weapons"
  | "weapon_accessories"
  | "commlinks"
  | "cyberdecks"
  | "rccs"
  | "sensors"
  | "optics"
  | "programs"
  | "apps"
  | "gear"
  | "vehicles"
  | "drones"
  | "adept_powers"
  | "qi_foci"
  | "spells"
  | "spirits"
  | "sprites"
  | "foci"
  | "lifestyles";

/** The ones whose rows also take the player's own name for the piece
 *  (`<armorname>`, `<gearname>`, `<vehiclename>`, `<crittername>`). */
const NAMED: ReadonlySet<NotedBucket> = new Set([
  "armor",
  "commlinks",
  "cyberdecks",
  "rccs",
  "sensors",
  "optics",
  "programs",
  "apps",
  "gear",
  "vehicles",
  "drones",
  "spirits",
  "sprites",
  "foci",
  "qi_foci",
]);

/** One text box: what is typed shows at once, and is saved on leaving it. */
export function TextBox({
  value,
  label,
  multiline,
  onSave,
}: {
  value: string;
  label: string;
  multiline?: boolean;
  onSave: (value: string) => void;
}) {
  // what was typed, and the saved text it was typed over: shown while the
  // saved text is still that one, so the box does not spring back while the
  // save is on its way, and gives way to a change made anywhere else
  const [draft, setDraft] = useState<{ text: string; over: string } | null>(null);
  const shown = draft && draft.over === value ? draft.text : value;
  const props = {
    "aria-label": label,
    value: shown,
    onChange: (e: { target: { value: string } }) => setDraft({ text: e.target.value, over: value }),
    onBlur: () => {
      if (shown !== value) onSave(shown);
    },
  };
  return multiline ? <textarea rows={3} {...props} /> : <input type="text" {...props} />;
}

/**
 * The player's own note on a row and, where `named`, their own name for the
 * piece. Nothing is computed from either. Open from the start when something
 * is written; fixed after that, so clearing the last word does not shut it
 * under the cursor.
 */
export function NotesBox({
  text,
  named,
  of,
  ui,
  onSave,
  searchKey,
}: {
  searchKey?: string;
  text: PlayerText;
  named: boolean;
  /** what the row is, for the boxes' labels */
  of: string;
  ui: UiFn;
  onSave: (field: Field, value: string) => void;
}) {
  const notes = text.notes ?? "";
  const nickname = text.nickname ?? "";
  const [opened] = useState(() => !!(notes.trim() || (named && nickname.trim())));
  return (
    <details className="row-notes" data-sheet-search={searchKey} open={opened || undefined}>
      <summary>
        {ui(named ? "rowNotes.summaryNamed" : "rowNotes.summary")}
        {named && nickname.trim() ? ui("rowNotes.nicknameShown", { nickname }) : ""}
      </summary>
      {named ? (
        <label className="row-notes-field">
          {ui("rowNotes.nickname")}
          <TextBox
            value={nickname}
            label={ui("rowNotes.nicknameOf", { name: of })}
            onSave={(value) => onSave("nickname", value)}
          />
        </label>
      ) : null}
      <label className="row-notes-field">
        {ui("rowNotes.notes")}
        <TextBox
          value={notes}
          multiline
          label={ui("rowNotes.notesOf", { name: of })}
          onSave={(value) => onSave("notes", value)}
        />
      </label>
    </details>
  );
}

/** `NotesBox` for row `id` of `ch[bucket]`; nothing when the row is not one
 *  the character holds (a piece the engine adds itself). */
export function RowNotes({
  ch,
  bucket,
  id,
  of,
  ui,
  patch,
}: {
  ch: Character;
  bucket: NotedBucket;
  id: string | null | undefined;
  of: string;
  ui: UiFn;
  patch: TabPanelProps["patch"];
}) {
  const row = ((ch[bucket] ?? []) as Array<{ id?: string | null } & PlayerText>).find(
    (r) => id && r.id === id,
  );
  if (!row) return null;
  return (
    <NotesBox
      text={row}
      searchKey={`${bucket}/${id}`}
      named={NAMED.has(bucket)}
      of={of}
      ui={ui}
      // an updater, read against the character as saved: a note left while
      // another edit is on its way is neither dropped nor undoes that edit
      onSave={(field, value) =>
        patch((cur: Character) => ({
          [bucket]: editRow(cur[bucket] as Array<{ id?: string | null }>, id, { [field]: value }),
        }))
      }
    />
  );
}

/** The note on a quality, keyed as its extras are (`quality_notes`). */
export function QualityNotes({
  ch,
  noteKey,
  of,
  ui,
  patch,
}: {
  ch: Character;
  noteKey: string;
  of: string;
  ui: UiFn;
  patch: TabPanelProps["patch"];
}) {
  return (
    <NotesBox
      searchKey={`qualities/${noteKey}`}
      text={{ notes: ch.quality_notes?.[noteKey] ?? "" }}
      named={false}
      of={of}
      ui={ui}
      onSave={(_, value) =>
        patch((cur: Character) => {
          const notes = { ...(cur.quality_notes || {}) };
          if (value) notes[noteKey] = value;
          else delete notes[noteKey];
          return { quality_notes: notes };
        })
      }
    />
  );
}
