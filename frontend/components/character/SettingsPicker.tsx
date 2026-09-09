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
import {
  CustomDataShapeError,
  readStyleFolder,
  recallFolder,
  rememberFolder,
  type CustomDataFiles,
} from "@/lib/character/customdata-store";
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
 * A published ruleset is one folder holding `settings/` and `customdata/`, so
 * that folder is what the load button asks for: every settings file in it
 * joins the pulldown at once, and picking one of them merges the custom data
 * it names without asking for the folder a second time.
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
  // The last folder's files, so a second ruleset from the same pick merges
  // without another trip through the file dialog. Null until one is picked or
  // `recallFolder` finds the previous session's.
  const [folder, setFolder] = useState<CustomDataFiles | null>(null);
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

  /**
   * Apply a ruleset, merging its custom data when the folder is already here.
   *
   * The dataset hash is per settings file, not per folder: two files in one
   * pick enable different directories, so each needs its own merge. Waiting
   * for it keeps the character from being patched twice.
   */
  async function apply(settings: CharacterSettings, method?: string | null): Promise<void> {
    const base = { ...(method ? buildMethodPatch(method, ch) : {}) };
    const wanted = settings.customdata || [];
    const files = wanted.length > 0 ? (folder ?? (await recallFolder())) : null;
    if (!files) {
      await patch({ ...base, settings });
      return;
    }
    setFolder(files);
    try {
      await patch({ ...base, settings: { ...settings, ...(await merged(files, wanted)) } });
    } catch (e) {
      // The ruleset still applies — it is the custom data that did not, and
      // the missing-data line below says so.
      await patch({ ...base, settings });
      setError(errorMessage(e, ui, "settings.customDataFailed"));
    }
  }

  /** Merge `wanted` out of `files` and report it. Returns the hash to carry. */
  async function merged(files: CustomDataFiles, wanted: string[]): Promise<{ dataset: string }> {
    const res = await api.uploadCustomData(files, wanted);
    setMerge({
      applied: res.applied,
      skipped: res.skipped.map((s) => `${s.source}: ${s.reason}`),
    });
    return { dataset: res.dataset };
  }

  function onPick(picked: string) {
    if (!picked) {
      // Back to unrestricted, and back to the printed SR5 numbers: a bare
      // `{name, books}` leaves every knob unset, which is what unset means.
      void patch({ settings: { name: "", books: [] } });
      return;
    }
    setError(null);
    setMerge(null);
    const file = files.find((f) => f.name === picked);
    if (file) {
      void apply(file);
      return;
    }
    const preset = presets.find((p) => p.name === picked);
    if (preset) void apply({ name: preset.name, books: [...preset.books] }, preset.build_method);
  }

  async function onFile(file: File) {
    setError(null);
    setMerge(null);
    try {
      const { settings, build_method } = await api.parseSettings(await file.arrayBuffer());
      setFiles(saveSettingsFile(settings));
      await apply(settings, build_method);
    } catch (e) {
      setError(errorMessage(e, ui, "settings.loadFailed"));
    }
  }

  /**
   * A whole ruleset folder: every settings file in it, and the custom data.
   *
   * All of the settings files join the pulldown, because that is what the
   * folder offers — but only one can be applied, and picking for the user
   * would be a guess. One file applies itself; several leave the choice in
   * the pulldown, with the folder already here so the choice merges.
   */
  async function onFolder(list: FileList) {
    setError(null);
    setMerge(null);
    try {
      const pick = await readStyleFolder(list);
      if (Object.keys(pick.customdata).length > 0) {
        setFolder(pick.customdata);
        await rememberFolder(pick.customdata);
      }
      let loaded: CharacterSettings[] = [];
      let first: { settings: CharacterSettings; build_method: string | null } | null = null;
      for (const file of pick.settings) {
        const parsed = await api.parseSettings(new TextEncoder().encode(file.text).buffer);
        loaded = saveSettingsFile(parsed.settings);
        first ??= parsed;
      }
      if (loaded.length > 0) setFiles(loaded);
      if (pick.settings.length === 1 && first) {
        await apply(first.settings, first.build_method);
        return;
      }
      // No settings half — a bare `customdata/` pick for the ruleset already
      // applied, which is the pre-folder way of doing it and still works.
      const wanted = ch.settings?.customdata || [];
      if (pick.settings.length === 0 && wanted.length > 0) {
        await patch({
          settings: {
            ...(ch.settings || { name: "", books: [] }),
            ...(await merged(pick.customdata, wanted)),
          },
        });
      }
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

        <button
          className="btn"
          onClick={() => folderRef.current?.click()}
          title={ui("settings.folderHint")}
        >
          {ui("settings.folder")}
        </button>
        <input
          ref={folderRef}
          type="file"
          hidden
          multiple
          aria-label={ui("settings.folder")}
          // a directory pick: `settings/` and `customdata/` are siblings in a
          // published ruleset, so the folder holding both is what comes across
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
