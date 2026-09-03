import { beforeEach, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { LOCALE_STORAGE_KEY, useUiText } from "@/lib/i18n";

function Probe() {
  const { locale, setLocale, ui } = useUiText();
  return (
    <div>
      <span data-testid="v">{ui("tab.check")}</span>
      <button onClick={() => setLocale(locale === "ja" ? "en" : "ja")}>toggle</button>
    </div>
  );
}

beforeEach(() => window.localStorage.clear());

it("defaults to ja, switches locale, and persists the choice", () => {
  render(<Probe />);
  expect(screen.getByTestId("v").textContent).toBe("チェック");

  fireEvent.click(screen.getByText("toggle"));
  expect(screen.getByTestId("v").textContent).toBe("Check");
  expect(window.localStorage.getItem(LOCALE_STORAGE_KEY)).toBe("en");
});

it("adopts a previously stored locale on mount", () => {
  window.localStorage.setItem(LOCALE_STORAGE_KEY, "en");
  render(<Probe />);
  expect(screen.getByTestId("v").textContent).toBe("Check");
});
