"use client";

// Route-segment error boundary: a render-time throw anywhere below the page
// lands here instead of a blank white screen. Kept dependency-free (no i18n
// hook, no editor state) so it works even when those are what failed.
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <div className="main">
      <h1>問題が発生しました</h1>
      <p className="errors">{error.message || "予期しないエラーです。"}</p>
      <p className="muted">
        入力中の変更はブラウザに保存されています。再読み込みで復帰できることが多いです。
      </p>
      <button className="btn" onClick={reset}>
        再読み込み
      </button>
    </div>
  );
}
