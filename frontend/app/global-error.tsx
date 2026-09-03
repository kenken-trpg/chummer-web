"use client";

// Last-resort boundary for failures in the root layout itself. It replaces
// <html>/<body>, so it must render them and cannot rely on globals.css.
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="ja">
      <body
        style={{
          margin: 0,
          padding: "40px 24px",
          fontFamily: "system-ui, sans-serif",
          background: "#0d1114",
          color: "#e8f0f3",
        }}
      >
        <h1 style={{ fontSize: "1.35rem" }}>問題が発生しました</h1>
        <p style={{ color: "#ff6b6b" }}>{error.message || "予期しないエラーです。"}</p>
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
          再読み込み
        </button>
      </body>
    </html>
  );
}
