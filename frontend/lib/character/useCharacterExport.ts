import { useState } from "react";
import { api } from "@/lib/api";
import { exportFilename } from "@/lib/character/export-filename";
import { buildShareUrl, SHARE_URL_WARN } from "@/lib/character/share";
import { portraitsOf } from "@/lib/character/portrait";
import { errorMessage } from "@/lib/errors";
import type { Catalog, Character } from "@/lib/types";
import { type UdonariumOptions, buildUdonariumConjured, buildUdonariumXml } from "@/lib/udonarium";
import { zipFiles, zipSingleFile } from "@/lib/zip";
import { type Notice } from "@/lib/engine-notices";
import type { UiFn } from "@/lib/i18n";
import type { Locale } from "@/lib/i18n/messages";

/** The export formats the character is checked before being written to. */
export type ExportFormat = "chum5" | "xlsx";

/** Hand the browser a file. The three download paths differed only in what
 *  they put in the blob and what they called it. */
function offer(blob: Blob, filename: string) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

/**
 * Every way the open character leaves this app: the four downloads, the
 * round-trip review that stands between two of them and the file, the share
 * link and the clipboard.
 *
 * Owns only what those need — the pending review and the "copied" flash.
 * The character, the messages and the words come from
 * {@link useCharacterEditor}, which is also where the result is spread into
 * the editor's own shape, so no component sees this hook.
 *
 * `pendingGearCount` is the import's unsettled 装備 rows: they are held in
 * this browser and were never sent, so the round-trip check cannot see them
 * and this hook has to be told.
 */
export function useCharacterExport(opts: {
  ch: Character | null;
  ui: UiFn;
  locale: Locale;
  pendingGearCount: number;
  setError: (message: string | null) => void;
  setNotice: (message: string | null) => void;
}) {
  const { ch, ui, locale, pendingGearCount, setError, setNotice } = opts;
  const [copied, setCopied] = useState<string | null>(null);
  /** what the file would lose, while the player decides whether to export it
   *  anyway. Tied to the exact state it was checked against: any edit (or
   *  switching character) makes it stale, and a stale review is dropped. */
  const [review, setExportReview] = useState<{
    of: Character;
    format: ExportFormat;
    differences: Notice[];
  } | null>(null);
  const exportReview = review && review.of === ch ? review.differences : null;
  /** Which format the pending review was asked for, so the panel can name it. */
  const exportReviewFormat = review && review.of === ch ? review.format : null;

  function download() {
    if (!ch) return;
    offer(
      new Blob([JSON.stringify(ch, null, 2)], { type: "application/json" }),
      exportFilename(ch.name, "json"),
    );
  }

  /**
   * Export a file the character has to be read back out of — after asking the
   * server what reading it back would change. A clean round trip saves straight
   * away; otherwise the differences wait in `exportReview` for
   * {@link confirmExport} or {@link cancelExport}. A failed check is not worth
   * blocking the download over.
   *
   * Both formats go through this: a .chum5 loses what Chummer has no field for,
   * and the キャラシテンプレート .xlsx loses rather more — it is a fixed grid with
   * one free-text column for all the equipment — so both are worth a look
   * before the file is written.
   */
  async function downloadChum5() {
    await checkThenSave("chum5");
  }

  /** Export the character as a キャラシテンプレート-shaped .xlsx. */
  async function downloadXlsx() {
    await checkThenSave("xlsx");
  }

  async function checkThenSave(format: ExportFormat) {
    if (!ch) return;
    const check = format === "chum5" ? api.checkChummerExport : api.checkXlsxExport;
    const differences = await check(ch).catch(() => []);
    // Gear rows waiting to be confirmed are a reason to stop as well, and the
    // round trip cannot see them: they are held in this browser and were never
    // sent, so what it checked is a character that does not have them. A file
    // written now leaves them out, which is worth saying before it is written.
    if (differences.length || pendingGearCount) {
      setExportReview({ of: ch, format, differences });
      return;
    }
    await save(format);
  }

  async function confirmExport() {
    const format = review?.format ?? "chum5";
    setExportReview(null);
    await save(format);
  }

  function cancelExport() {
    setExportReview(null);
  }

  async function save(format: ExportFormat) {
    if (!ch) return;
    try {
      const blob = await (format === "chum5" ? api.exportChummer(ch) : api.exportXlsx(ch));
      offer(blob, exportFilename(ch.name, format));
    } catch (e) {
      setError(errorMessage(e, ui, "app.err.export"));
    }
  }

  /**
   * Save the character as an Udonarium piece: a zip holding one `data.xml`.
   *
   * A zip, because only a zip goes in both ways. Dropping a file on the table
   * reads a bare `.xml`, but the 「ZIP読込」 file input unzips whatever it is
   * handed and dies on a plain xml with "End of central directory not found",
   * its `accept` list notwithstanding. Checked against udonarium.app 1.17.4.
   *
   * Built here rather than on the server: the palette comes out of `derived`,
   * which this browser already has.
   */
  function downloadUdonarium(
    catalog: Catalog,
    tr: (n: string) => string,
    opts: UdonariumOptions = {},
  ) {
    if (!ch) return;
    offer(
      zipSingleFile("data.xml", buildUdonariumXml(ch, catalog, tr, locale, opts)),
      exportFilename(ch.name, "zip", { tag: "udonarium" }),
    );
  }

  /**
   * Save every bound spirit and registered sprite as one zip, a piece each.
   *
   * Udonarium reads every xml an archive holds — checked against
   * udonarium.app 1.17.4 — so a summoner's whole retinue goes on the table in
   * one drop instead of one file per spirit.
   */
  function downloadUdonariumConjured(catalog: Catalog, tr: (n: string) => string) {
    if (!ch) return;
    const files = buildUdonariumConjured(ch, catalog, tr, locale);
    if (!files.length) return;
    offer(zipFiles(files), exportFilename(ch.name, "zip", { tag: "udonarium-conjured" }));
  }

  /** Save JSON for Foundry VTT's shadowrun5e Chummer importer, in the screen's language. */
  async function downloadFvtt() {
    if (!ch) return;
    try {
      // both this and `download` write .json; only the tag tells them apart
      offer(await api.exportFvtt(ch, locale), exportFilename(ch.name, "json", { tag: "fvtt" }));
    } catch (e) {
      setError(errorMessage(e, ui, "app.err.export"));
    }
  }

  /**
   * Copy a read-only `/share#c=…` link for the current character. The state
   * lives entirely in the fragment — nothing is uploaded — so the only limit
   * is URL length; past {@link SHARE_URL_WARN} we still copy but say so.
   */
  async function copyShareLink() {
    if (!ch) return;
    try {
      const url = await buildShareUrl(ch, window.location.href);
      await copyText(url, "share");
      // the copy worked — these are caveats about the link, not failures
      const notes: string[] = [];
      if (url.length > SHARE_URL_WARN) notes.push(ui("share.long", { length: url.length }));
      if (portraitsOf(ch).length) notes.push(ui("share.portrait"));
      setNotice(notes.length ? notes.join(" ") : null);
    } catch (e) {
      setNotice(null);
      setError(errorMessage(e, ui, "share.err.build"));
    }
  }

  async function copyText(text: string, tag: string) {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement("textarea");
      ta.value = text;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      ta.remove();
    }
    setCopied(tag);
    setTimeout(() => setCopied(null), 2000);
  }

  return {
    exportReview,
    exportReviewFormat,
    copied,
    download,
    downloadChum5,
    downloadXlsx,
    downloadFvtt,
    downloadUdonarium,
    downloadUdonariumConjured,
    confirmExport,
    cancelExport,
    copyText,
    copyShareLink,
  };
}
