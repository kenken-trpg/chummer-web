"use client";

import { type ReactNode, useMemo, useState } from "react";

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

type Props<T extends Pickable> = {
  /** Already narrowed to what this tab can actually buy (no parent-only mods). */
  items: T[];
  /** "防具を検索" — used as both the placeholder and the accessible name. */
  label: string;
  tr: (name: string) => string;
  /** The muted detail line under the name. */
  describe: (item: T) => ReactNode;
  onAdd: (item: T) => void;
  addLabel?: string;
  limit?: number;
  /** What an empty search box shows. The default is core-rulebook entries;
   *  lifestyles use a hand-picked set instead. */
  idle?: { keep: (item: T) => boolean; note: string };
};

const CORE_ONLY = "SR5 のみ表示中（検索するとサプリメントも探します）";

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
  addLabel = "購入",
  limit = 40,
  idle,
}: Props<T>) {
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
  const hidden = matched.length - shown.length;

  return (
    <>
      {categories.length > 1 ? (
        <div className="option-row">
          <button className={`tab ${cat === "all" ? "active" : ""}`} onClick={() => setCat("all")}>
            すべて
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
              aria-label={`${tr(item.name)} を${addLabel}`}
            >
              {addLabel}
            </button>
          </div>
        ))}
        <p className="muted picker-footnote" role="status">
          {matched.length === 0
            ? "該当なし"
            : hidden > 0
              ? `他 ${hidden} 件。検索で絞り込んでください`
              : null}
          {!query && matched.length > 0 ? (
            <>
              {hidden > 0 ? " / " : ""}
              {idle ? idle.note : CORE_ONLY}
            </>
          ) : null}
        </p>
      </div>
    </>
  );
}
