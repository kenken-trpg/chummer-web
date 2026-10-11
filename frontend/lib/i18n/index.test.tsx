import { beforeEach, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { LOCALE_STORAGE_KEY, useUiText } from "@/lib/i18n";

function Probe() {
  const { locale, setLocale, ui } = useUiText();
  return (
    <div>
      <span data-testid="v">{ui("tab.check")}</span>
      <span data-testid="l">{locale}</span>
      <button onClick={() => setLocale(locale === "ja" ? "en" : "ja")}>toggle</button>
    </div>
  );
}

beforeEach(() => window.localStorage.clear());

it("defaults to ja, switches locale, and persists the choice", async () => {
  render(<Probe />);
  expect(screen.getByTestId("v").textContent).toBe("チェック");

  fireEvent.click(screen.getByText("toggle"));

  // the choice is stored at once; the words follow the catalog's arrival
  expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe("en");
  await waitFor(() => expect(screen.getByTestId("v").textContent).toBe("Check"));
});

it("adopts a previously stored locale on mount", async () => {
  window.localStorage.setItem(LOCALE_STORAGE_KEY, "en");
  render(<Probe />);
  await waitFor(() => expect(screen.getByTestId("v").textContent).toBe("Check"));
});

/**
 * Only `ja` is bundled, so a stored `en` cannot be honoured on the first
 * render. What must not happen is reporting `en` while the catalog is still in
 * flight: `ui()` would answer in Japanese for a tree that believes it is
 * English, which is how a half-translated screen happens. It stays `ja` until
 * the words are there, then swaps in one go.
 */
it("does not claim a locale whose catalog has not arrived", async () => {
  // a fresh registry, or an earlier test in this file has already fetched `en`
  vi.resetModules();
  const { LOCALE_STORAGE_KEY: KEY, useUiText: useText } = await import("@/lib/i18n");
  window.localStorage.setItem(KEY, "en");

  function FreshProbe() {
    const { locale, ui } = useText();
    return <span data-testid="p">{`${locale}:${ui("tab.check")}`}</span>;
  }

  render(<FreshProbe />);
  expect(screen.getByTestId("p").textContent).toBe("ja:チェック");
  await waitFor(() => expect(screen.getByTestId("p").textContent).toBe("en:Check"));
});
