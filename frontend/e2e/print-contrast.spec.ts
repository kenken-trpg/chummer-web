import { expect, test, type Page } from "@playwright/test";
import { chummerFixture, waitForEditor } from "./helpers";

/**
 * Nothing on the print sheet may be dark-on-dark.
 *
 * The print sheet is white paper: `.character-sheet--print` sets a white
 * background and turns the values black, and `@media print` does the same to
 * the screen layouts. A box that carries its own background from the screen
 * theme is not reached by either, so its black values land on the dark panel
 * they used to sit on — the text is selectable and copyable but invisible,
 * which is exactly how the vehicle / drone stat boxes shipped.
 *
 * jsdom has no cascade and no computed colours, so the unit suite cannot see
 * this; and asserting on one selector would only guard the one box we already
 * know about. This sweeps every opaque background inside the sheet instead.
 */

/** sRGB relative luminance, the WCAG definition. */
const LUMINANCE = `(r, g, b) => {
  const lin = (v) => {
    const c = v / 255;
    return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
  };
  return 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
}`;

/** Every element in the sheet painting an opaque background darker than paper. */
function darkBackgrounds(page: Page): Promise<string[]> {
  return page.evaluate(`(() => {
    const luminance = ${LUMINANCE};
    const out = [];
    for (const el of Array.from(document.querySelectorAll("article *"))) {
      const bg = getComputedStyle(el).backgroundColor;
      const m = bg.match(/rgba?\\((\\d+),\\s*(\\d+),\\s*(\\d+)(?:,\\s*([\\d.]+))?\\)/);
      if (!m) continue;
      const alpha = m[4] === undefined ? 1 : Number(m[4]);
      // a transparent or barely-tinted background lets the paper through
      if (alpha < 0.5) continue;
      if (luminance(Number(m[1]), Number(m[2]), Number(m[3])) >= 0.5) continue;
      const cls = typeof el.className === "string" ? el.className.trim() : "";
      out.push(el.tagName.toLowerCase() + (cls ? "." + cls.split(/\\s+/).join(".") : "") + " " + bg);
    }
    return Array.from(new Set(out));
  })()`);
}

/** A real save, so the sheet has the vehicles, drones and gear a blank one lacks. */
async function openSheet(page: Page) {
  await page.goto("/");
  await waitForEditor(page);
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)").setInputFiles(await chummerFixture());
  await expect(page.getByRole("textbox", { name: "キャラクター名" })).toHaveValue("Ghile Mear");
  await page.getByRole("button", { name: "シート", exact: true }).click();
}

test("the 卓用 A4 layout paints nothing dark, on screen or on paper", async ({ page }) => {
  await openSheet(page);
  await page.getByRole("combobox", { name: "レイアウト" }).selectOption("print");
  await expect(page.locator("article.character-sheet--print")).toBeVisible();

  expect(await darkBackgrounds(page)).toEqual([]);
  await page.emulateMedia({ media: "print" });
  expect(await darkBackgrounds(page)).toEqual([]);
});

test("the standard layout paints nothing dark once it is on paper", async ({ page }) => {
  await openSheet(page);
  await page.emulateMedia({ media: "print" });
  expect(await darkBackgrounds(page)).toEqual([]);
});
