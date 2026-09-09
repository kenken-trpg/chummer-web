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
import { CustomDataShapeError, readCustomDataFolder } from "@/lib/character/customdata-store";
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
  const [merge, setMerge] = useState<{ applied: number; skipped: string[] } | null>(null);
  const folderRef = useRef<HTMLInputElement>(null);
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
  // A settings file that names custom-data directories is unusable without
  // them: every entry they add or re-source is simply missing until the
  // folder is here.
  const needsCustomData = (ch.settings?.customdata || []).length > 0;

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

  async function onFolder(list: FileList) {
    setError(null);
    setMerge(null);
    try {
      const contents = await readCustomDataFolder(list);
      const wanted = ch.settings?.customdata || [];
      const res = await api.uploadCustomData(contents, wanted);
      setMerge({
        applied: res.applied,
        skipped: res.skipped.map((s) => `${s.source}: ${s.reason}`),
      });
      // the hash is what every later request carries; the files stay here
      void patch({
        settings: { ...(ch.settings || { name: "", books: [] }), dataset: res.dataset },
      });
    } catch (e) {
      setError(
        e instanceof CustomDataShapeError
          ? ui("settings.customDataNotAFolder")
          : errorMessage(e, ui, "settings.customDataFailed"),
      );
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

        {needsCustomData ? (
          <button
            className="btn"
            onClick={() => folderRef.current?.click()}
            title={ui("settings.customDataHint")}
          >
            {ui(ch.settings?.dataset ? "settings.customDataReload" : "settings.customData", {
              count: (ch.settings?.customdata || []).length,
            })}
          </button>
        ) : null}
        <input
          ref={folderRef}
          type="file"
          hidden
          multiple
          aria-label={ui("settings.customData", {
            count: (ch.settings?.customdata || []).length,
          })}
          // a directory pick: the settings file names directories, so the
          // whole `customdata/` tree is what has to come across
          {...({ webkitdirectory: "", directory: "" } as Record<string, string>)}
          onChange={(e) => {
            const list = e.target.files;
            e.target.value = "";
            if (list && list.length) void onFolder(list);
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
      {needsCustomData && !ch.settings?.dataset ? (
        <p className="muted">{ui("settings.customDataNeeded")}</p>
      ) : null}
      {merge ? (
        <p className="muted">
          {ui("settings.customDataApplied", { count: merge.applied })}
          {merge.skipped.length > 0
            ? ` ・ ${ui("settings.customDataSkipped", {
                count: merge.skipped.length,
                items: merge.skipped.join(" / "),
              })}`
            : ""}
        </p>
      ) : null}
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
