import { useEffect, useEffectEvent, useRef, useState } from "react";
import { api, type CharacterSummary } from "@/lib/api";
import { useCharacterHistory } from "@/lib/character/history";
import {
  MAX_PORTRAITS,
  PORTRAIT_TYPES,
  portraitsOf,
  portraitsPatch,
} from "@/lib/character/portrait";
import { buildShareUrl, SHARE_URL_WARN } from "@/lib/character/share";
import { errorMessage, MessageError } from "@/lib/errors";
import type { Catalog, Character } from "@/lib/types";
import { renderNotice, type Notice } from "@/lib/engine-notices";
import { makeT, makeTr, makeTrSkillGroup, type TFn } from "@/lib/ui-strings";
import { useUiText } from "@/lib/i18n";
import { onNotice } from "@/lib/notices";

/** The catalog key of the vendored data: no dataset, no directories. */
const NO_CUSTOM_DATA = "|";

/**
 * Owns the character-editor state: the loaded catalog, the current
 * `Character`, the roster, the undo/redo history and every mutation that
 * goes through the API (create / open / delete / duplicate / patch / import
 * / export / clipboard). `Page` keeps only view state (the active tab).
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
  const [copied, setCopied] = useState<string | null>(null);
  /** what a .chum5 would lose, while the player decides whether to export it
   *  anyway. Tied to the exact state it was checked against: any edit (or
   *  switching character) makes it stale, and a stale review is dropped. */
  const [review, setExportReview] = useState<{ of: Character; differences: Notice[] } | null>(null);
  const exportReview = review && review.of === ch ? review.differences : null;
  const [roster, setRoster] = useState<CharacterSummary[]>([]);
  const { ui, locale } = useUiText();
  const history = useCharacterHistory();
  const lastCommitted = useRef<Character | null>(null);
  const busy = useRef(false);
  // `ui` is rebuilt on every locale change; the notice listener is registered
  // once, so it reads the current one through a ref instead of re-subscribing.
  const uiRef = useRef(ui);
  uiRef.current = ui;

  // `lib/api` and `local-store` have no locale and no React — they report a
  // degraded save / a stale compute as a message key. See `lib/notices`.
  useEffect(() => {
    onNotice((key) => setNotice(uiRef.current(key)));
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

  /**
   * Re-read the catalog when the character's custom data changes.
   *
   * The pick lists are built from the catalog, so a merged pack only reaches
   * them if the catalog is the one that pack produces. Keyed on the dataset
   * hash and the enabled directories — the two halves the server keys its
   * merge by — so switching rulesets, or loading the folder for the one
   * already applied, both refetch, and nothing else does.
   *
   * The old catalog stays on screen while the new one is on its way: it is
   * ~3 MB, and blanking every list for the length of that request reads worse
   * than lists that are briefly a merge behind. A failure leaves the old one
   * in place and says so, for the same reason.
   */
  const dataset = ch?.settings?.dataset ?? "";
  const enabledDirs = (ch?.settings?.customdata ?? []).join("|");
  const catalogKey = `${dataset}|${enabledDirs}`;
  /** The key of the catalog now in `catalog`. The bootstrap fetches the plain
   *  one, which is what no dataset and no directories spell. */
  const loadedKey = useRef(NO_CUSTOM_DATA);
  const catalogLoaded = catalog !== null;
  // `ui` only words the failure; re-running on a locale switch would refetch
  // 3 MB to change a sentence that is not on screen.
  const onReloadError = useEffectEvent((e: unknown) =>
    setError(errorMessage(e, ui, "app.err.catalogReload")),
  );
  useEffect(() => {
    if (!catalogLoaded || loadedKey.current === catalogKey) return;
    let live = true;
    (async () => {
      try {
        const next = await api.catalog({
          dataset,
          customdata: enabledDirs.split("|").filter(Boolean),
        });
        if (!live) return;
        loadedKey.current = catalogKey;
        setCatalog(next);
      } catch (e) {
        if (live) onReloadError(e);
      }
    })();
    return () => {
      live = false;
    };
  }, [catalogKey, catalogLoaded, dataset, enabledDirs]);

  async function openCharacter(id: string) {
    if (!id || id === ch?.id) return;
    try {
      remember(await api.get(id));
      onCharacterOpened?.();
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

  async function patch(body: Record<string, unknown>) {
    if (!ch || busy.current) return;
    busy.current = true;
    const base = lastCommitted.current ?? ch;
    try {
      const next = await api.patch(ch.id, body);
      history.record(base);
      setCh(next);
      lastCommitted.current = next;
      setError(null);
    } catch (e) {
      setError(errorMessage(e, ui, "app.err.patch"));
    } finally {
      busy.current = false;
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

  function download() {
    if (!ch) return;
    const blob = new Blob([JSON.stringify(ch, null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${ch.name || "character"}.json`;
    a.click();
    URL.revokeObjectURL(a.href);
  }

  /**
   * Export a .chum5 — after asking the server what reading it back would
   * change. A clean round trip saves straight away; otherwise the differences
   * wait in `exportReview` for {@link confirmChum5} or {@link cancelChum5}.
   * A failed check is not worth blocking the download over.
   */
  async function downloadChum5() {
    if (!ch) return;
    const differences = await api.checkChummerExport(ch).catch(() => []);
    if (differences.length) {
      setExportReview({ of: ch, differences });
      return;
    }
    await saveChum5();
  }

  async function confirmChum5() {
    setExportReview(null);
    await saveChum5();
  }

  function cancelChum5() {
    setExportReview(null);
  }

  async function saveChum5() {
    if (!ch) return;
    try {
      const blob = await api.exportChummer(ch);
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `${ch.name || "character"}.chum5`;
      a.click();
      URL.revokeObjectURL(a.href);
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

  async function onImport(file: File) {
    setError(null);
    try {
      if (/\.chum5(lz)?$/i.test(file.name)) {
        const { character, warnings } = await api.importChummer(await file.arrayBuffer());
        remember(character);
        onCharacterOpened?.();
        if (warnings.length) {
          setError(
            ui("app.importWarnings", {
              count: warnings.length,
              details: warnings
                .slice(0, 15)
                .map((w) => renderNotice(w, ui, tr))
                .join(" / "),
            }),
          );
        }
      } else {
        remember(await api.import(JSON.parse(await file.text())));
        onCharacterOpened?.();
      }
      void refreshRoster();
    } catch (e) {
      setError(errorMessage(e, ui, "app.err.load"));
    }
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
    exportReview,
    roster,
    copied,
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
    onImport,
    onPortraitFile,
    download,
    downloadChum5,
    confirmChum5,
    cancelChum5,
    copyText,
    copyShareLink,
  };
}

export type CharacterEditor = ReturnType<typeof useCharacterEditor>;
