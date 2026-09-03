"use client";

import { LOCALES, type Locale, useUiText } from "@/lib/i18n";

/** Small language picker for the app chrome. Persists via {@link useUiText}. */
export function LocaleSwitch() {
  const { locale, setLocale, ui } = useUiText();
  return (
    <label className="locale-switch">
      <span className="muted">{ui("locale.label")}</span>
      <select className="btn" value={locale} onChange={(e) => setLocale(e.target.value as Locale)}>
        {LOCALES.map((l) => (
          <option key={l} value={l}>
            {ui(l === "ja" ? "locale.ja" : "locale.en")}
          </option>
        ))}
      </select>
    </label>
  );
}
