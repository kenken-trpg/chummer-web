"use client";

// Last-resort boundary for failures in the root layout itself. It replaces
// <html>/<body>, so it must render them and cannot rely on globals.css.
//
// `useLocale` is the one import: it reads localStorage directly rather than a
// context, so nothing has to have survived above this boundary. `lang` follows
// the same value, which is the point of localising this page at all.
import { useLocale, translate } from "@/lib/i18n";
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const [locale] = useLocale();
  return (
    <html lang={locale}>
      <body
        style={{
          margin: 0,
          padding: "40px 24px",
          fontFamily: "system-ui, sans-serif",
          background: "#0d1114",
          color: "#e8f0f3",
        }}
      >
        <h1 style={{ fontSize: "1.35rem" }}>{translate(locale, "error.title")}</h1>
        <p style={{ color: "#ff6b6b" }}>{error.message || translate(locale, "error.unexpected")}</p>
        <button
          onClick={reset}
          style={{
            font: "inherit",
            color: "inherit",
            background: "#1c262c",
            border: "1px solid #2a3942",
            borderRadius: 6,
            padding: "6px 12px",
            cursor: "pointer",
          }}
        >
          {translate(locale, "error.reload")}
        </button>
      </body>
    </html>
  );
}
