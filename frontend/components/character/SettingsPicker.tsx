"use client";

import { useRef, useState } from "react";
import type { Catalog, Character, CharacterSettings } from "@/lib/types";
import { buildMethodPatch } from "@/lib/character/build-method";
import {
  loadSettingsFiles,
  removeSettingsFile,
  saveSettingsFile,
} from "@/lib/character/settings-store";
import { api } from "@/lib/api";
import { errorMessage } from "@/lib/errors";
import type { UiFn } from "@/lib/i18n";

/**
 * The ruleset pulldown: which settings the character is built under, and which
 * rulebooks that leaves buyable.
 *
 * Two sources feed it — Chummer's shipped presets, which come with the catalog,
 * and settings files the user loaded from their own Chummer folder, which live
 * in this browser (`settings-store`). Picking either applies its books, its
 * build method and its house-rule numbers.
 *
 * Ticking a book by hand deviates from whatever was picked, which drops the
 * name: the character is no longer "Standard", and saying so is better than
 * showing a name the books no longer match.
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
  // Read once, lazily — the same shape as `useSheetLayout`. `loadSettingsFiles`
  // swallows a missing / disabled store, so a prerender just sees none.
  const [files, setFiles] = useState<CharacterSettings[]>(loadSettingsFiles);
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const presets = catalog.settings_presets || [];
  const allBooks = catalog.books || [];
  const books = ch.settings?.books || [];
  const name = ch.settings?.name || "";
  const unsupported = ch.settings?.unsupported || [];
  const known = presets.some((p) => p.name === name) || files.some((f) => f.name === name);

  function apply(settings: CharacterSettings, method?: string | null) {
    void patch({
      ...(method ? buildMethodPatch(method, ch) : {}),
      settings,
    });
  }

  function onPick(picked: string) {
    if (!picked) {
      // Back to unrestricted, and back to the printed SR5 numbers: a bare
      // `{name, books}` leaves every knob unset, which is what unset means.
      void patch({ settings: { name: "", books: [] } });
      return;
    }
    const file = files.find((f) => f.name === picked);
    if (file) {
      apply(file);
      return;
    }
    const preset = presets.find((p) => p.name === picked);
    if (preset) apply({ name: preset.name, books: [...preset.books] }, preset.build_method);
  }

  async function onFile(file: File) {
    setError(null);
    try {
      const { settings, build_method } = await api.parseSettings(await file.arrayBuffer());
      setFiles(saveSettingsFile(settings));
      apply(settings, build_method);
    } catch (e) {
      setError(errorMessage(e, ui, "settings.loadFailed"));
    }
  }

  function onForget(target: string) {
    setFiles(removeSettingsFile(target));
    if (name === target) void patch({ settings: { name: "", books: [] } });
  }

  function toggleBook(code: string) {
    const next = books.includes(code) ? books.filter((c) => c !== code) : [...books, code];
    // Deviating from a ruleset makes it the character's own. The numeric knobs
    // are kept — only the books and the name are the user's edit here.
    void patch({ settings: { ...(ch.settings || { books: [] }), name: "", books: next } });
  }

  return (
    <div className="card settings-picker" style={{ marginBottom: 12 }}>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
        <label>
          {ui("settings.preset")}
          <select
            value={known ? name : ""}
            onChange={(e) => onPick(e.target.value)}
            title={ui("settings.presetHint")}
          >
            <option value="">{ui("settings.presetNone")}</option>
            {files.length > 0 ? (
              <optgroup label={ui("settings.groupLoaded")}>
                {files.map((f) => (
                  <option key={`file:${f.name}`} value={f.name}>
                    {f.name}
                  </option>
                ))}
              </optgroup>
            ) : null}
            <optgroup label={ui("settings.groupShipped")}>
              {presets.map((p) => (
                <option key={p.id} value={p.name}>
                  {p.name}
                </option>
              ))}
            </optgroup>
          </select>
        </label>

        <button
          className="btn"
          onClick={() => fileRef.current?.click()}
          title={ui("settings.loadHint")}
        >
          {ui("settings.load")}
        </button>
        <input
          ref={fileRef}
          type="file"
          accept=".xml,text/xml,application/xml"
          hidden
          aria-label={ui("settings.load")}
          onChange={(e) => {
            const file = e.target.files?.[0];
            // clear first, so re-picking the same file fires `change` again
            e.target.value = "";
            if (file) void onFile(file);
          }}
        />

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
        {known && files.some((f) => f.name === name) ? (
          <button
            className="btn"
            onClick={() => onForget(name)}
            title={ui("settings.forgetHint", { name })}
          >
            {ui("settings.forget")}
          </button>
        ) : null}
      </div>

      {error ? <p className="errors">{error}</p> : null}
      {unsupported.length > 0 ? (
        <p className="muted">
          {ui("settings.unsupportedHere", {
            count: unsupported.length,
            tags: unsupported.join(", "),
          })}
        </p>
      ) : null}

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
