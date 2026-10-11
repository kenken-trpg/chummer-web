"use client";

import { useCallback, useSyncExternalStore } from "react";
import { type Locale, type MsgKey, catalogLoaded, loadLocale, translate } from "./messages";

export { LOCALES, MESSAGES, catalogLoaded, formatMessage, loadLocale, translate } from "./messages";
export type { Locale, MsgKey } from "./messages";

/** The `ui` callback, for components that take it as a prop rather than
 *  calling the hook themselves (the sidebar blocks). */
export type UiFn = (key: MsgKey, vars?: Record<string, string | number>) => string;

export const LOCALE_STORAGE_KEY = "chummer-web:locale";
const LOCALE_EVENT = "chummer-web:locale-change";
const DEFAULT_LOCALE: Locale = "ja";

function isLocale(v: unknown): v is Locale {
  return v === "ja" || v === "en";
}

function storedLocale(): Locale {
  try {
    const v = window.localStorage.getItem(LOCALE_STORAGE_KEY);
    if (isLocale(v)) return v;
  } catch {
    /* SSR / storage disabled */
  }
  return DEFAULT_LOCALE;
}

/**
 * Which locales have been asked for, so that reading the snapshot repeatedly
 * — which React does — starts the fetch once and attaches one completion
 * handler. A failed fetch is forgotten, so switching again retries it.
 */
const requested = new Set<Locale>();

function ensureCatalog(locale: Locale): void {
  if (catalogLoaded(locale) || requested.has(locale)) return;
  requested.add(locale);
  void loadLocale(locale).then(
    () => {
      try {
        window.dispatchEvent(new Event(LOCALE_EVENT));
      } catch {
        /* non-browser */
      }
    },
    () => requested.delete(locale),
  );
}

/**
 * Persisted UI locale, or the default. Safe on the server (returns default).
 *
 * **A locale whose catalog has not arrived is not reported.** Only `ja` is in
 * the first bundle; the rest are fetched (see `loadLocale`). Answering `en`
 * before its catalog is here would render one pass of English keys in Japanese
 * and then swap, so instead this stays on `ja` and the fetch's completion
 * broadcasts a locale change, which re-renders the tree in English once.
 */
export function readLocale(): Locale {
  const stored = storedLocale();
  if (stored === DEFAULT_LOCALE || catalogLoaded(stored)) return stored;
  ensureCatalog(stored);
  return DEFAULT_LOCALE;
}

export function writeLocale(locale: Locale): void {
  // start the fetch on the click rather than on the next snapshot read
  ensureCatalog(locale);
  try {
    window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
  } catch {
    /* storage disabled */
  }
  try {
    window.dispatchEvent(new Event(LOCALE_EVENT));
  } catch {
    /* non-browser */
  }
}

function subscribe(onChange: () => void): () => void {
  window.addEventListener(LOCALE_EVENT, onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener(LOCALE_EVENT, onChange);
    window.removeEventListener("storage", onChange);
  };
}

/**
 * Current UI locale plus a setter that persists and broadcasts the change so
 * every {@link useLocale} consumer in the tree re-renders together. Backed by
 * `useSyncExternalStore`: SSR and the first client render use the default, then
 * React re-renders with the stored value — no hydration mismatch.
 */
export function useLocale(): [Locale, (l: Locale) => void] {
  const locale = useSyncExternalStore(subscribe, readLocale, () => DEFAULT_LOCALE);
  const setLocale = useCallback((l: Locale) => writeLocale(l), []);
  return [locale, setLocale];
}

/** `ui(key, vars?)` bound to the current locale, plus the locale + setter. */
export function useUiText(): {
  locale: Locale;
  setLocale: (l: Locale) => void;
  ui: UiFn;
} {
  const [locale, setLocale] = useLocale();
  const ui = useCallback(
    (key: MsgKey, vars?: Record<string, string | number>) => translate(locale, key, vars),
    [locale],
  );
  return { locale, setLocale, ui };
}
