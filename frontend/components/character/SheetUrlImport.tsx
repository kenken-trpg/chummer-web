"use client";

import { useEffect, useRef, useState } from "react";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { useUiText } from "@/lib/i18n";

/**
 * Reading a キャラシテンプレート straight from its Google Sheets address, for the
 * player who keeps their character in the sheet rather than in a file.
 *
 * Folded away until asked for: it is one way in among several, and the header is
 * already a wall of buttons. The note about sharing is shown with the field
 * rather than saved for the error, because it is the one thing that has to be
 * true before this can work at all.
 */
export function SheetUrlImport({ ed }: { ed: CharacterEditor }) {
  const { ui } = useUiText();
  const { importSheetUrl } = ed;
  const [open, setOpen] = useState(false);
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const field = useRef<HTMLInputElement>(null);
  // The button that opens this is gone the moment it is opened, so focus has to
  // be put somewhere on purpose or it falls back to the top of the page.
  useEffect(() => {
    if (open) field.current?.focus();
  }, [open]);

  if (!open) {
    return (
      <div className="option-row">
        <button className="btn" onClick={() => setOpen(true)} title={ui("toolbar.sheetUrlHint")}>
          {ui("toolbar.sheetUrl")}
        </button>
      </div>
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    try {
      await importSheetUrl(url);
      // Only on success: a URL that was refused is still the one to correct.
      setUrl("");
      setOpen(false);
    } catch {
      // The editor has already put the reason on screen.
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="option-row sheet-url-row" onSubmit={(e) => void submit(e)}>
      <label>
        {ui("toolbar.sheetUrl")}
        <input
          type="url"
          className="sheet-url-field"
          value={url}
          ref={field}
          required
          placeholder="https://docs.google.com/spreadsheets/d/…"
          onChange={(e) => setUrl(e.target.value)}
          aria-label={ui("toolbar.sheetUrl")}
        />
      </label>
      <button className="btn primary" type="submit" disabled={busy || !url.trim()}>
        {busy ? ui("toolbar.sheetUrlReading") : ui("toolbar.sheetUrlRead")}
      </button>
      <button className="btn" type="button" onClick={() => setOpen(false)} disabled={busy}>
        {ui("app.exportReview.cancel")}
      </button>
      <span className="muted">{ui("toolbar.sheetUrlShared")}</span>
    </form>
  );
}
