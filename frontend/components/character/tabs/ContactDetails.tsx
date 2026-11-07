"use client";
import type { TabPanelProps } from "@/components/character/types";
import { useState } from "react";
import { editRow } from "@/lib/character/rows";
import type { ContactInstall } from "@/lib/types/generated";

/** The contact's own description, as Chummer keeps it. Nothing is computed from these. */
const FIELDS = [
  ["location", "contact.location"],
  ["metatype", "contact.metatype"],
  ["gender", "contact.gender"],
  ["age", "contact.age"],
  ["contact_type", "contact.contactType"],
  ["preferred_payment", "contact.preferredPayment"],
  ["hobbies_vice", "contact.hobbiesVice"],
  ["personal_life", "contact.personalLife"],
] as const;

type Field = (typeof FIELDS)[number][0] | "notes";

export function ContactDetails({
  row,
  character: ch,
  ui,
  patch,
  setCharacter,
}: Pick<TabPanelProps, "character" | "ui" | "patch" | "setCharacter"> & { row: ContactInstall }) {
  const id = row.id ?? "";
  // typed: shown at once; left: saved, as the name above does
  const type = (field: Field, value: string) =>
    setCharacter({ ...ch, contacts: editRow(ch.contacts, id, { [field]: value }) });
  const save = (field: Field, value: string) =>
    patch({ contacts: editRow(ch.contacts, id, { [field]: value }) });
  // open from the start when something is written there; fixed after that,
  // so clearing the last field does not shut it under the cursor
  const [opened] = useState(() =>
    [...FIELDS.map(([field]) => field), "notes" as const].some((field) =>
      (row[field] ?? "").trim(),
    ),
  );

  return (
    <details className="contact-details" open={opened || undefined}>
      <summary>{ui("contact.details")}</summary>
      <div className="cyber-controls">
        {FIELDS.map(([field, label]) => (
          <label key={field}>
            {ui(label)}
            <input
              type="text"
              value={row[field] ?? ""}
              onChange={(e) => type(field, e.target.value)}
              onBlur={(e) => save(field, e.target.value)}
            />
          </label>
        ))}
      </div>
      <label className="contact-notes">
        {ui("contact.notes")}
        <textarea
          rows={3}
          value={row.notes ?? ""}
          onChange={(e) => type("notes", e.target.value)}
          onBlur={(e) => save("notes", e.target.value)}
        />
      </label>
    </details>
  );
}
