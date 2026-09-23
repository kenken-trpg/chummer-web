import { expect, test, type Page } from "@playwright/test";
import { chummerFixture, waitForEditor } from "./helpers";

/**
 * Nothing may run off the side of a phone screen.
 *
 * jsdom has no layout, so the unit suite cannot see this at all: a grid whose
 * fixed tracks add up past the viewport does not wrap, it widens the document,
 * and the whole page — sticky tab bar included — slides sideways under every
 * touch. The tabs were measured at 320-1024px and only the narrow end was
 * broken, so these are the widths that guard it.
 *
 * A real save, not the character the editor mints on load: an empty character
 * has no knowledge skill, no cyberware with an accessory under it, and none of
 * the rows with a delete button that were what actually overflowed.
 */
const WIDTHS = [320, 390, 768];

/**
 * Every element under `.main` whose right edge is past the viewport. Anything
 * inside an x-scrollable box is meant to extend past it, so it is skipped —
 * the tab strip and the priority table are both deliberately scrollable.
 */
function overflowing(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const scrollable = (el: Element) => {
      for (let p: Element | null = el; p; p = p.parentElement) {
        const ov = getComputedStyle(p).overflowX;
        if (ov === "auto" || ov === "scroll") return true;
      }
      return false;
    };
    const width = document.documentElement.clientWidth;
    const out: string[] = [];
    for (const el of Array.from(document.querySelectorAll(".main *"))) {
      const rect = el.getBoundingClientRect();
      if (rect.width > 0 && rect.left + rect.width > width + 1 && !scrollable(el)) {
        const cls = typeof el.className === "string" ? el.className.trim() : "";
        out.push(el.tagName.toLowerCase() + (cls ? "." + cls.split(/\s+/).join(".") : ""));
      }
    }
    return [...new Set(out)];
  });
}

for (const width of WIDTHS) {
  test(`no tab runs off a ${width}px screen`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    await waitForEditor(page);
    await page.getByLabel("読込 (JSON/.chum5)").setInputFiles(await chummerFixture());
    await expect(page.getByRole("textbox", { name: "キャラクター名" })).toHaveValue("Ghile Mear");

    const tabs = page.locator(".tabs .tab");
    for (let i = 0; i < (await tabs.count()); i++) {
      const tab = tabs.nth(i);
      const name = (await tab.textContent())!.trim();
      await tab.click();
      // the heavy tabs render their rows in an effect after the click resolves
      await expect.poll(() => overflowing(page), { timeout: 5_000 }).toEqual([]);
      expect(
        await page.evaluate(() => document.documentElement.scrollWidth),
        `${name} widens the document at ${width}px`,
      ).toBeLessThanOrEqual(width + 1);
    }
  });
}

test("the priority table scrolls inside its own box", async ({ page }) => {
  // it is six columns of cards and cannot be made to fit; what it must not do
  // is take the page with it
  await page.setViewportSize({ width: 390, height: 900 });
  await page.goto("/");
  await waitForEditor(page);
  const box = page.locator(".table-scroll");
  await expect(box).toBeVisible();
  const scroll = await box.evaluate((el) => [el.scrollWidth, el.clientWidth]);
  expect(scroll[0]).toBeGreaterThan(scroll[1]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(391);
});
