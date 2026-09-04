"use client";

// Route-segment error boundary: a render-time throw anywhere below the page
// lands here instead of a blank white screen. It touches no editor state and
// no character data — the things most likely to be what failed. `useUiText` is
// safe here: it is backed by `useSyncExternalStore` over localStorage, with no
// provider above it to have failed.
import { useUiText } from "@/lib/i18n";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const { ui } = useUiText();
  return (
    <div className="main">
      <h1>{ui("error.title")}</h1>
      <p className="errors">{error.message || ui("error.unexpected")}</p>
      <p className="muted">{ui("error.saved")}</p>
      <button className="btn" onClick={reset}>
        {ui("error.reload")}
      </button>
    </div>
  );
}
