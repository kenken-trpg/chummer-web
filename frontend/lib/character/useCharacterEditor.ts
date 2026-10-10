import { useEffect, useEffectEvent, useRef, useState } from "react";
import { api, type CharacterSummary } from "@/lib/api";
import { useCharacterHistory } from "@/lib/character/history";
import {
  MAX_PORTRAITS,
  PORTRAIT_TYPES,
  portraitsOf,
  portraitsPatch,
} from "@/lib/character/portrait";
import { clearPendingGear } from "@/lib/character/pending-gear-store";
import { advancesOneLeaf, disjointKeys } from "@/lib/character/patch-queue";
import { useCatalogReload } from "@/lib/character/useCatalogReload";
import { useCharacterExport } from "@/lib/character/useCharacterExport";
import { useCharacterImport } from "@/lib/character/useCharacterImport";
import { errorMessage, MessageError } from "@/lib/errors";
import type { Catalog, Character } from "@/lib/types";
import { makeT, makeTr, makeTrSkillGroup, type TFn } from "@/lib/ui-strings";
import { useUiText } from "@/lib/i18n";
import type { MsgKey } from "@/lib/i18n/messages";
import { onNotice } from "@/lib/notices";

export type { ExportFormat } from "@/lib/character/useCharacterExport";

/**
 * Owns the character-editor state: the loaded catalog, the current
 * `Character`, the roster, the undo/redo history and every mutation that
 * goes through the API (create / open / delete / duplicate / patch / import
 * / export / clipboard). `Page` keeps only view state (the active tab).
 *
 * The three parts that stand on their own live next door and are spread back
 * into one object here, so no component knows the editor is more than one
 * hook: {@link useCharacterImport} (files coming in), {@link useCharacterExport}
 * (files, links and clipboard going out) and {@link useCatalogReload} (the
 * catalog following the character's custom data).
 *
 * `onCharacterOpened` fires after a successful open / new / duplicate /
 * import so the caller can reset the tab.
 */
export function useCharacterEditor(opts: { onCharacterOpened?: () => void } = {}) {
  const { onCharacterOpened } = opts;
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [ch, setCh] = useState<Character | null>(null);
  const [error, setError] = useState<string | null>(null);
  /** Advisories about an action that *succeeded* — never the red error box. */
  const [notice, setNotice] = useState<string | null>(null);
  const [roster, setRoster] = useState<CharacterSummary[]>([]);
  const { ui, locale } = useUiText();
  const history = useCharacterHistory();
  const lastCommitted = useRef<Character | null>(null);
  const busy = useRef(false);
  /** The body on the wire, and the one edit held back behind it. Both are
   *  only set while `busy`, so the unload guard below already covers them. */
  const inFlight = useRef<Record<string, unknown> | null>(null);
  const queued = useRef<Record<string, unknown> | null>(null);
  // `lib/api` and `local-store` have no locale and no React — they report a
  // degraded save / a stale compute as a message key. See `lib/notices`.
  //
  // `ui` is rebuilt on every locale change, but the listener is registered
  // once: an effect event reads the current one without re-subscribing.
  const wordNotice = useEffectEvent((key: MsgKey) => setNotice(ui(key)));
  useEffect(() => {
    onNotice((key) => wordNotice(key));
    return () => onNotice(null);
  }, []);

  // An edit is only kept once the compute answers and IndexedDB commits; a
  // reload or a closed tab before that loses it. `busy` spans exactly that
  // window, so ask the browser to confirm leaving while it is set.
  useEffect(() => {
    const guard = (e: BeforeUnloadEvent) => {
      if (busy.current) e.preventDefault();
    };
    window.addEventListener("beforeunload", guard);
    return () => window.removeEventListener("beforeunload", guard);
  }, []);

  function remember(c: Character) {
    setCh(c);
    lastCommitted.current = c;
    history.reset();
    try {
      localStorage.setItem("lastCharacterId", c.id);
    } catch {}
  }
  async function refreshRoster() {
    setRoster(await api.list().catch(() => []));
  }

  const imports = useCharacterImport({
    ch,
    ui,
    remember,
    refreshRoster,
    setError,
    onCharacterOpened,
  });
  const exports = useCharacterExport({
    ch,
    ui,
    locale,
    pendingGearCount: imports.pendingGear?.length ?? 0,
    setError,
    setNotice,
  });
  useCatalogReload({ ch, catalog, ui, setCatalog, setError });

  // One-time bootstrap: load catalog + roster, then open the last / a new
  // character. The steps that read `remember` and `ui` are effect events, so
  // they see the current ones without making them re-run the bootstrap.
  const openInitial = useEffectEvent(async (list: CharacterSummary[]) => {
    let last: string | null = null;
    try {
      last = localStorage.getItem("lastCharacterId");
    } catch {}
    let opened: Character | null = null;
    if (last && list.some((r) => r.id === last)) {
      opened = await api.get(last).catch(() => null);
    }
    if (opened) {
      remember(opened);
    } else {
      remember(await api.create("Runner"));
      void refreshRoster();
    }
  });
  const onBootError = useEffectEvent((e: unknown) => setError(errorMessage(e, ui, "app.err.boot")));
  useEffect(() => {
    (async () => {
      try {
        const [cat, list] = await Promise.all([api.catalog(), api.list().catch(() => [])]);
        setCatalog(cat);
        setRoster(list);
        await openInitial(list);
      } catch (e) {
        onBootError(e);
      }
    })();
  }, []);

  async function openCharacter(id: string) {
    if (!id || id === ch?.id) return;
    try {
      remember(await api.get(id));
      onCharacterOpened?.();
      // Picked back up rather than dropped: a character imported from a
      // template keeps the rows nobody has settled yet.
      imports.readPendingGear(id);
      setError(null);
    } catch (e) {
      setError(errorMessage(e, ui, "app.err.load"));
    }
  }
  /** Returns false when the backend refused — `deleteCurrent` needs to know,
   *  and the Toolbar's "＋ 新規キャラ" must not reject unhandled. */
  async function newCharacter(): Promise<boolean> {
    try {
      remember(await api.create("Runner"));
      onCharacterOpened?.();
      void refreshRoster();
      setError(null);
      return true;
    } catch (e) {
      setError(errorMessage(e, ui, "app.newFailed"));
      return false;
    }
  }
  async function deleteCurrent() {
    if (!ch) return;
    if (!window.confirm(ui("app.confirm.delete", { name: ch.name || ui("app.unnamed") }))) return;
    const others = roster.filter((r) => r.id !== ch.id);
    // nothing left to attach them to
    clearPendingGear(ch.id);
    await api.remove(ch.id).catch(() => {});
    // deleting the last one mints a replacement; if the backend is down that
    // fails loudly rather than leaving the editor pointing at a deleted id
    if (others[0]) await openCharacter(others[0].id);
    else await newCharacter();
    void refreshRoster();
  }
  async function duplicateCurrent() {
    if (!ch) return;
    const fallbackName = ui("app.copyOf", { name: ch.name || ui("app.unnamed") });
    const name = window.prompt(ui("app.prompt.duplicateName"), fallbackName);
    if (name === null) return;
    try {
      const { id: _id, derived: _d, ...rest } = ch;
      void _id;
      void _d;
      remember(await api.import({ ...rest, name: name || fallbackName }));
      onCharacterOpened?.();
      void refreshRoster();
    } catch (e) {
      setError(errorMessage(e, ui, "app.err.duplicate"));
    }
  }

  /**
   * Send one edit, and hold onto an edit that arrives while it is in flight
   * when — and only when — holding onto it is safe.
   *
   * Patches go one at a time because `api.patch` applies the body to the
   * character as stored. An edit that arrives during that window used to be
   * dropped, which a number input shows by springing back to its old value;
   * see `patch-queue` for why blindly queueing would be worse rather than
   * better, and what makes the queued case safe.
   */
  async function patch(body: Record<string, unknown>) {
    if (!ch) return;
    if (busy.current) {
      // Compare against what is *going* to be sent, not what is on the wire:
      // a third change while the second waits is a step on from the second.
      const previous = queued.current ?? inFlight.current;
      if (!previous) return;
      if (advancesOneLeaf(previous, body)) {
        queued.current = body;
      } else if (disjointKeys(previous, body)) {
        // Fields that do not overlap cannot undo each other, so both edits can
        // wait together — a rename still in flight must not swallow the career
        // switch that was pressed on top of it.
        queued.current = { ...(queued.current ?? {}), ...body };
      }
      return;
    }
    busy.current = true;
    try {
      let send: Record<string, unknown> | null = body;
      while (send) {
        inFlight.current = send;
        queued.current = null;
        const base = lastCommitted.current ?? ch;
        const next = await api.patch(ch.id, send);
        history.record(base);
        setCh(next);
        lastCommitted.current = next;
        setError(null);
        send = queued.current;
      }
    } catch (e) {
      setError(errorMessage(e, ui, "app.err.patch"));
    } finally {
      // A failure drops whatever was waiting: it was composed against a
      // character this one never became, and the person is looking at an
      // error rather than at the edit they expected.
      busy.current = false;
      inFlight.current = null;
      queued.current = null;
    }
  }

  async function restoreSnapshot(snap: Character) {
    if (busy.current) return;
    busy.current = true;
    try {
      const next = await api.compute(snap);
      setCh(next);
      lastCommitted.current = next;
      setError(null);
    } catch (e) {
      setError(errorMessage(e, ui, "app.err.undo"));
    } finally {
      busy.current = false;
    }
  }

  async function undo() {
    if (!ch || busy.current) return;
    const snap = history.stepBack(lastCommitted.current ?? ch);
    if (snap) await restoreSnapshot(snap);
  }
  async function redo() {
    if (!ch || busy.current) return;
    const snap = history.stepForward(lastCommitted.current ?? ch);
    if (snap) await restoreSnapshot(snap);
  }

  /** Add `file` after the portraits already there, while fewer than three. */
  async function onPortraitFile(file: File) {
    if (!ch) return;
    const pics = portraitsOf(ch);
    if (pics.length >= MAX_PORTRAITS) return;
    // the same four the backend keeps (models.clean_portrait); anything else
    // would be dropped there without a word
    if (!PORTRAIT_TYPES.includes(file.type)) {
      setError(ui("app.err.notImage"));
      return;
    }
    if (file.size > 3_000_000) {
      setError(ui("app.err.imageTooBig"));
      return;
    }
    try {
      const dataUrl = await new Promise<string>((resolve, reject) => {
        const r = new FileReader();
        r.onload = () => resolve(String(r.result || ""));
        r.onerror = () => reject(r.error ?? new MessageError("app.err.load"));
        r.readAsDataURL(file);
      });
      await patch(portraitsPatch([...pics, dataUrl]));
    } catch (e) {
      setError(errorMessage(e, ui, "app.err.portraitRead"));
    }
  }

  const tr = makeTr(catalog, locale);
  const trGroup = makeTrSkillGroup(catalog, locale);
  const t: TFn = makeT(catalog, locale);

  return {
    catalog,
    ch,
    error,
    notice,
    exportReview: exports.exportReview,
    exportReviewFormat: exports.exportReviewFormat,
    importReport: imports.importReport,
    dismissImportReport: imports.dismissImportReport,
    importSheetUrl: imports.importSheetUrl,
    pendingGear: imports.pendingGear,
    resolvePendingGear: imports.resolvePendingGear,
    dismissPendingGear: imports.dismissPendingGear,
    roster,
    copied: exports.copied,
    history,
    tr,
    trGroup,
    t,
    setCh,
    setError,
    setNotice,
    refreshRoster,
    openCharacter,
    newCharacter,
    deleteCurrent,
    duplicateCurrent,
    patch,
    restoreSnapshot,
    undo,
    redo,
    onImport: imports.onImport,
    onPortraitFile,
    download: exports.download,
    downloadChum5: exports.downloadChum5,
    downloadXlsx: exports.downloadXlsx,
    downloadFvtt: exports.downloadFvtt,
    downloadUdonarium: exports.downloadUdonarium,
    confirmExport: exports.confirmExport,
    cancelExport: exports.cancelExport,
    copyText: exports.copyText,
    copyShareLink: exports.copyShareLink,
  };
}

export type CharacterEditor = ReturnType<typeof useCharacterEditor>;
