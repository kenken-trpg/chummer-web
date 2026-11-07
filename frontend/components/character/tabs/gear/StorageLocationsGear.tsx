"use client";
import { useState } from "react";
import { TextBox } from "@/components/character/RowNotes";
import type { TabPanelProps } from "@/components/character/types";
import { editRow } from "@/lib/character/rows";
import type { MsgKey } from "@/lib/i18n";
import type { Character, StorageLocation } from "@/lib/types";

/** The lists whose rows of their own may be kept somewhere: everything
 *  Chummer writes under `<gears>` names one of `gear_locations`; armor names
 *  one of `armor_locations`. */
const GEAR_BUCKETS = [
  "commlinks",
  "cyberdecks",
  "rccs",
  "optics",
  "sensors",
  "programs",
  "apps",
  "gear",
] as const;
type Bucket = (typeof GEAR_BUCKETS)[number] | "armor";
type Kind = { places: "gear_locations" | "armor_locations"; buckets: readonly Bucket[] };
const KINDS: { title: MsgKey; kind: Kind }[] = [
  {
    title: "gear.locations.gearTitle",
    kind: { places: "gear_locations", buckets: GEAR_BUCKETS },
  },
  { title: "gear.locations.armorTitle", kind: { places: "armor_locations", buckets: ["armor"] } },
];

type Row = {
  id?: string | null;
  parent_id?: string | null;
  location?: string | null;
  nickname?: string | null;
};
type Shown = { id?: string | null; name?: string; label?: string | null };

/** The derived list a bucket's rows are shown from (armor's is `armor_items`). */
function shownRows(d: TabPanelProps["d"], bucket: Bucket): Shown[] {
  return ((bucket === "armor" ? d.armor_items : d[bucket]) ?? []) as Shown[];
}

/** One thing kept somewhere (or nowhere), and where to move it. */
function Item({
  bucket,
  row,
  label,
  places,
  ui,
  patch,
}: Pick<TabPanelProps, "ui" | "patch"> & {
  bucket: Bucket;
  row: Row;
  label: string;
  places: StorageLocation[];
}) {
  return (
    <div className="muted" style={{ marginTop: 6 }}>
      {label}{" "}
      <select
        aria-label={ui("gear.locations.whereOf", { name: label })}
        value={places.some((p) => p.id === row.location) ? row.location! : ""}
        onChange={(e) => {
          // read now: the updater runs once React has set the box back
          const location = e.target.value || null;
          patch((cur: Character) => ({
            [bucket]: editRow(cur[bucket] as Row[], row.id, { location }),
          }));
        }}
      >
        <option value="">{ui("gear.locations.nowhere")}</option>
        {places.map((p) => (
          <option key={p.id} value={p.id!}>
            {p.name || ui("gear.locations.untitled")}
          </option>
        ))}
      </select>
    </div>
  );
}

function Places({
  title,
  kind,
  character: ch,
  d,
  tr,
  ui,
  patch,
}: Pick<TabPanelProps, "character" | "d" | "tr" | "ui" | "patch"> & { title: MsgKey; kind: Kind }) {
  const [newName, setNewName] = useState("");
  const places = (ch[kind.places] ?? []) as StorageLocation[];
  // the rows of their own, in the order the panels show them; a row the
  // engine has not drawn yet has no name to show, and waits for it
  const items = kind.buckets.flatMap((bucket) => {
    const shown = new Map(shownRows(d, bucket).map((r) => [r.id, r]));
    return ((ch[bucket] ?? []) as Row[])
      .filter((row) => !row.parent_id && shown.has(row.id))
      .map((row) => {
        const s = shown.get(row.id)!;
        const name = tr(s.label || s.name || "");
        return {
          bucket,
          row,
          label: row.nickname?.trim() ? `${name}（${row.nickname}）` : name,
        };
      });
  });
  const known = new Set(places.map((p) => p.id));
  const inPlace = (id: string | null) =>
    items.filter(({ row }) => (id ? row.location === id : !known.has(row.location ?? "")));
  const show = (list: typeof items) =>
    list.map(({ bucket, row, label }) => (
      <Item
        key={`${bucket}:${row.id}`}
        bucket={bucket}
        row={row}
        label={label}
        places={places}
        ui={ui}
        patch={patch}
      />
    ));
  const add = () => {
    const name = newName.trim();
    if (!name) return;
    patch((cur: Character) => ({
      [kind.places]: [...(cur[kind.places] ?? []), { id: crypto.randomUUID(), name, notes: "" }],
    }));
    setNewName("");
  };
  const remove = (id: string) =>
    // what was in it is kept nowhere now, rather than naming a place gone
    patch((cur: Character) => ({
      [kind.places]: (cur[kind.places] ?? []).filter((p) => p.id !== id),
      // only the lists that had something there
      ...Object.fromEntries(
        kind.buckets
          .filter((bucket) => ((cur[bucket] ?? []) as Row[]).some((row) => row.location === id))
          .map((bucket) => [
            bucket,
            ((cur[bucket] ?? []) as Row[]).map((row) =>
              row.location === id ? { ...row, location: null } : row,
            ),
          ]),
      ),
    }));
  const unplaced = inPlace(null);
  return (
    <>
      <h3>{ui(title)}</h3>
      {places.map((place) => {
        const name = place.name || ui("gear.locations.untitled");
        const kept = inPlace(place.id!);
        return (
          <div className="cyber-item" key={place.id}>
            <div>
              <TextBox
                value={place.name ?? ""}
                label={ui("gear.locations.nameOf", { name })}
                onSave={(value) =>
                  patch((cur: Character) => ({
                    [kind.places]: editRow(cur[kind.places], place.id, { name: value.trim() }),
                  }))
                }
              />
              {kept.length ? show(kept) : <div className="muted">{ui("gear.locations.empty")}</div>}
            </div>
            <button
              className="btn danger"
              // beside the name, not stretched down a long list
              style={{ alignSelf: "flex-start" }}
              aria-label={ui("common.deleteLabel", { name })}
              onClick={() => remove(place.id!)}
            >
              {ui("common.delete")}
            </button>
          </div>
        );
      })}
      {unplaced.length ? (
        <div className="cyber-item">
          <div>
            <b>{ui("gear.locations.unplaced")}</b>
            {show(unplaced)}
          </div>
        </div>
      ) : null}
      <div className="option-row">
        <input
          type="text"
          maxLength={200}
          aria-label={`${ui(title)}: ${ui("gear.locations.newName")}`}
          placeholder={ui("gear.locations.newName")}
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") add();
          }}
        />
        <button className="btn" onClick={add} disabled={!newName.trim()}>
          {ui("common.add")}
        </button>
      </div>
    </>
  );
}

/** The places the player keeps things in, and what is in each (Chummer's
 *  gear and armor locations). Nothing is computed from any of it. */
export function StorageLocationsGear(props: TabPanelProps) {
  return (
    <>
      {KINDS.map(({ title, kind }) => (
        <Places key={kind.places} title={title} kind={kind} {...props} />
      ))}
    </>
  );
}
