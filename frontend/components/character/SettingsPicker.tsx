"use client";

import { useState } from "react";
import type { Catalog, Character } from "@/lib/types";
import { buildMethodPatch } from "@/lib/character/build-method";
import type { UiFn } from "@/lib/i18n";

/**
 * The ruleset pulldown: which of Chummer's settings the character is built
 * under, and which rulebooks that leaves buyable.
 *
 * Chummer's settings file holds ~150 knobs; what this app honours so far is
 * the book list and the build method, so those are what the control offers.
 * Picking a preset applies both. Ticking a book by hand deviates from the
 * preset, which drops the name — the character is no longer "Standard", and
 * saying so is better than showing a preset name the books no longer match.
 */
export function SettingsPicker({
  catalog,
  character: ch,
  ui,
  tr,
  patch,
}: {
  catalog: Catalog;
  character: Character;
  ui: UiFn;
  tr: (name: string) => string;
  patch: (body: Record<string, unknown>) => void | Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const presets = catalog.settings_presets || [];
  const allBooks = catalog.books || [];
  const books = ch.settings?.books || [];
  const name = ch.settings?.name || "";
  const known = presets.some((p) => p.name === name);

  function applyPreset(presetName: string) {
    if (!presetName) {
      void patch({ settings: { name: "", books: [] } });
      return;
    }
    const preset = presets.find((p) => p.name === presetName);
    if (!preset) return;
    void patch({
      ...buildMethodPatch(preset.build_method, ch),
      settings: { name: preset.name, books: [...preset.books] },
    });
  }

  function toggleBook(code: string) {
    const next = books.includes(code) ? books.filter((c) => c !== code) : [...books, code];
    // Deviating from a preset makes the character's ruleset its own; keeping
    // the old name would misreport what it now allows.
    void patch({ settings: { name: "", books: next } });
  }

  return (
    <div className="card settings-picker" style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <label>
          {ui("settings.preset")}
          <select
            value={known ? name : ""}
            onChange={(e) => applyPreset(e.target.value)}
            title={ui("settings.presetHint")}
          >
            <option value="">{ui("settings.presetNone")}</option>
            {presets.map((p) => (
              <option key={p.id} value={p.name}>
                {p.name}
              </option>
            ))}
          </select>
        </label>
        <span className="muted">
          {books.length === 0
            ? ui("settings.booksAll")
            : ui("settings.booksCount", { count: books.length, total: allBooks.length })}
          {name && !known ? ` ・ ${name}` : ""}
          {!name && books.length > 0 ? ` ・ ${ui("settings.custom")}` : ""}
        </span>
        <button
          className="btn"
          onClick={() => setOpen(!open)}
          aria-expanded={open}
          title={ui("settings.booksHint")}
        >
          {ui(open ? "settings.booksHide" : "settings.booksShow")}
        </button>
      </div>

      {open ? (
        <>
          <div className="book-grid" style={{ marginTop: 8 }}>
            {allBooks.map((book) => (
              <label key={book.code} className="book-check">
                <input
                  type="checkbox"
                  checked={books.includes(book.code)}
                  onChange={() => toggleBook(book.code)}
                />
                <span>
                  {tr(book.name)} <span className="muted">({book.code})</span>
                </span>
              </label>
            ))}
          </div>
          <p className="muted">{ui("settings.booksNote")}</p>
        </>
      ) : null}
    </div>
  );
}
