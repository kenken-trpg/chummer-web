"use client";

import { useRef, useState } from "react";
import type { Catalog, Character } from "@/lib/types";
import { BookChecklist } from "@/components/character/ruleset/BookChecklist";
import { MergeSummary } from "@/components/character/ruleset/MergeSummary";
import { UnsupportedKnobs } from "@/components/character/ruleset/UnsupportedKnobs";
import { useRulesetLoader } from "@/lib/character/useRulesetLoader";
import type { PatchInput } from "@/lib/character/patch-queue";
import type { UiFn } from "@/lib/i18n";

/**
 * The ruleset pulldown: which settings the character is built under, and which
 * rulebooks that leaves buyable.
 *
 * Two sources feed it — Chummer's shipped presets, which come with the catalog,
 * and settings files the user loaded from their own Chummer folder, which live
 * in this browser (`settings-store`). Picking either applies its books, its
 * build method and its house-rule numbers; `useRulesetLoader` is where that
 * happens.
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
  patch: (body: PatchInput) => void | Promise<void>;
}) {
  const [open, setOpen] = useState(false);
  const folderRef = useRef<HTMLInputElement>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const presets = catalog.settings_presets || [];
  const allBooks = catalog.books || [];
  const { files, error, merge, onPick, onFile, onFolder, onForget } = useRulesetLoader({
    character: ch,
    presets,
    ui,
    patch,
  });
  const books = ch.settings?.books || [];
  const name = ch.settings?.name || "";
  const known = presets.some((p) => p.name === name) || files.some((f) => f.name === name);
  // A settings file that names custom-data directories is unusable without
  // them: every entry they add or re-source is simply missing until the
  // folder is here.
  const needsCustomData = (ch.settings?.customdata || []).length > 0;

  function setBooks(next: (books: string[]) => string[]) {
    // Deviating from a ruleset makes it the character's own. The numeric knobs
    // are kept — only the books and the name are the user's edit here. Built
    // from the character as saved, not as shown: a second tick lands while
    // the first is still being saved.
    void patch((saved) => ({
      settings: {
        ...(saved.settings || { books: [] }),
        name: "",
        books: next(saved.settings?.books || []),
      },
    }));
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
          // `.zip` shares this input rather than getting its own button: on a
          // phone the folder button below opens nothing usable, and a second
          // button that only some devices need is worse than one that takes
          // either shape.
          accept=".xml,.zip,text/xml,application/xml,application/zip"
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
            // copy first: clearing the input empties this same FileList in
            // Chromium, and the clear is what lets the same folder be re-picked
            const list = Array.from(e.target.files ?? []);
            e.target.value = "";
            if (list.length) void onFolder(list);
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

      <div role="alert">{error ? <p className="errors">{error}</p> : null}</div>
      {needsCustomData && !ch.settings?.dataset ? (
        // Warning-coloured, not muted, and with the way out attached: the
        // faint line this replaces said the data was missing but not that a
        // settings file alone never carries it, so it read as "this app
        // cannot load house rules".
        <p className="notice notice-warn">
          {ui("settings.customDataNeeded", { count: (ch.settings?.customdata || []).length })}{" "}
          <button
            className="linklike"
            onClick={() => folderRef.current?.click()}
            title={ui("settings.customDataPickHint")}
          >
            {ui("settings.customDataPick")}
          </button>
        </p>
      ) : null}
      {merge ? <MergeSummary merge={merge} ui={ui} /> : null}
      <UnsupportedKnobs unsupported={ch.settings?.unsupported || []} ui={ui} />

      {open ? (
        <BookChecklist books={books} allBooks={allBooks} onSet={setBooks} tr={tr} ui={ui} />
      ) : null}
    </div>
  );
}
