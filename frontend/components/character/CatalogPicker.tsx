"use client";

import { type ReactNode, useMemo, useState } from "react";
import { type MsgKey, useUiText } from "@/lib/i18n";

/**
 * Every catalog entry the pickers list has at least these. The tabs pass their
 * own concrete types (`ArmorCatalogItem`, `GearCatalogItem`, …); the picker
 * only ever reads the four fields it filters and labels by.
 */
export type Pickable = {
  id: string;
  name: string;
  category?: string;
  source?: string;
};

/**
 * A truncated result list that admits it. For the panels whose rows are too
 * particular for `<CatalogPicker>` — a quality's button turns into 削除 once
 * you own it, a spell's row prices itself against the free allowance — but
 * whose list is cut off the same way.
 */
export function PickerList<T>({
  items,
  limit = 40,
  note,
  children,
}: {
  items: T[];
  limit?: number;
  /** The idle explanation; pass undefined once the user has typed. */
  note?: MsgKey;
  children: (item: T) => ReactNode;
}) {
  const shown = items.slice(0, limit);
  return (
    <>
      {shown.map(children)}
      <PickerFootnote matched={items.length} shown={shown.length} note={note} />
    </>
  );
}

type Props<T extends Pickable> = {
  /** Already narrowed to what this tab can actually buy (no parent-only mods). */
  items: T[];
  /** "防具を検索" — used as both the placeholder and the accessible name. */
  label: string;
  tr: (name: string) => string;
  /** The muted detail line under the name. */
  describe: (item: T) => ReactNode;
  onAdd: (item: T) => void;
  /** Defaults to 購入 / "Buy". */
  addLabel?: string;
  limit?: number;
  /** What an empty search box shows. The default is core-rulebook entries;
   *  lifestyles use a hand-picked set instead. */
  idle?: { keep: (item: T) => boolean; note: MsgKey };
};

/** The default idle note: with an empty search box the lists show
 *  core-rulebook entries only. */
export const CORE_ONLY: MsgKey = "picker.coreOnly";

/**
 * Why the list stops where it does.
 *
 * A list cut off at `limit`, and a list showing core-rulebook entries only,
 * both look exactly like "this game does not have that item". `<CatalogPicker>`
 * renders this itself; the panels that still own their own row markup (a
 * quality's add button changes shape, a spell's is priced) call it directly.
 *
 * `note` is the idle explanation — pass `undefined` once the user has typed,
 * since a search reaches everything.
 */
export function PickerFootnote({
  matched,
  shown,
  note,
}: {
  matched: number;
  shown: number;
  note?: MsgKey;
}) {
  const { ui } = useUiText();
  const hidden = matched - shown;
  return (
    <p className="muted picker-footnote" role="status">
      {matched === 0 ? ui("picker.none") : hidden > 0 ? ui("picker.more", { count: hidden }) : null}
      {note && matched > 0 ? `${hidden > 0 ? " / " : ""}${ui(note)}` : null}
    </p>
  );
}

/**
 * Category chips + search + result list, shared by every "buy something from
 * the catalog" panel.
 *
 * Ten gear panels had this same block copy-pasted, each with its own drift.
 * Two behaviours in it used to be silent, and both read to the user as "that
 * item does not exist":
 *
 * - with an empty search box the list shows core-rulebook entries only, and
 * - the list is cut off at `limit` rows.
 *
 * Both are still true — rendering 3,000 rows is not an improvement — but they
 * are now stated under the list instead of being inferred.
 */
export function CatalogPicker<T extends Pickable>({
  items,
  label,
  tr,
  describe,
  onAdd,
  addLabel,
  limit = 40,
  idle,
}: Props<T>) {
  const { ui } = useUiText();
  const action = addLabel ?? ui("common.buy");
  const [search, setSearch] = useState("");
  const [cat, setCat] = useState("all");

  // Chips come from the listable items, so a chip can never select an empty
  // list (they used to be derived from a slightly wider filter).
  const categories = useMemo(
    () => [...new Set(items.map((item) => item.category).filter(Boolean))].sort() as string[],
    [items],
  );

  const query = search.trim().toLowerCase();
  const matched = items
    .filter((item) => cat === "all" || item.category === cat)
    .filter((item) =>
      query
        ? item.name.toLowerCase().includes(query) ||
          tr(item.name).toLowerCase().includes(query) ||
          (item.category || "").toLowerCase().includes(query)
        : idle
          ? idle.keep(item)
          : (item.source || "SR5") === "SR5",
    );
  const shown = matched.slice(0, limit);

  return (
    <>
      {categories.length > 1 ? (
        <div className="option-row">
          <button className={`tab ${cat === "all" ? "active" : ""}`} onClick={() => setCat("all")}>
            {ui("common.all")}
          </button>
          {categories.map((c) => (
            <button
              key={c}
              className={`tab ${cat === c ? "active" : ""}`}
              onClick={() => setCat(c)}
              aria-pressed={cat === c}
            >
              {tr(c)}
            </button>
          ))}
        </div>
      ) : null}
      <input
        type="search"
        placeholder={label}
        aria-label={label}
        value={search}
        onChange={(e) => setSearch(e.target.value)}
      />

      <div className="quality-list">
        {shown.map((item) => (
          <div className="quality-item" key={item.id}>
            <div>
              <b>{tr(item.name)}</b>
              <div className="muted">{describe(item)}</div>
            </div>
            <button
              className="btn primary"
              onClick={() => onAdd(item)}
              // every one of these reads "購入" on its own; name it by the row
              aria-label={ui("picker.buyLabel", { name: tr(item.name), action })}
            >
              {action}
            </button>
          </div>
        ))}
        <PickerFootnote
          matched={matched.length}
          shown={shown.length}
          note={query ? undefined : idle ? idle.note : CORE_ONLY}
        />
      </div>
    </>
  );
}
