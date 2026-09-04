"use client";

import { useCallback, useSyncExternalStore } from "react";
import { type Locale, type MsgKey, translate } from "./messages";

export { LOCALES, MESSAGES, formatMessage, translate } from "./messages";
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

/** Persisted UI locale, or the default. Safe on the server (returns default). */
export function readLocale(): Locale {
  try {
    const v = window.localStorage.getItem(LOCALE_STORAGE_KEY);
    if (isLocale(v)) return v;
  } catch {
    /* SSR / storage disabled */
  }
  return DEFAULT_LOCALE;
}

export function writeLocale(locale: Locale): void {
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
