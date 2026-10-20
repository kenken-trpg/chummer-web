import { expect, test } from "@playwright/test";
import { waitForEditor } from "./helpers";

/**
 * An attribute's name, slider and total sit on one line. jsdom has no layout,
 * so the unit suite cannot see it when the row loses its grid — which #364 did
 * by slipping another rule in between `.attr-row,` and `.skill-row`.
 */
test("an attribute row lays its name, slider and total side by side", async ({ page }) => {
  await page.goto("/");
  await waitForEditor(page);
  await page.getByRole("button", { name: "能力値", exact: true }).click();
  const row = page.locator(".attr-row").first();
  await expect(row).toBeVisible();
  const [name, slider, total] = await Promise.all(
    [
      row.locator("> span").first(),
      row.locator('input[type="range"]'),
      row.locator("> b").last(),
    ].map(async (el) => (await el.boundingBox())!),
  );
  expect(slider.x).toBeGreaterThan(name.x + name.width - 1);
  expect(total.x).toBeGreaterThan(slider.x + slider.width - 1);
  // one line: the slider starts above where the name ends
  expect(slider.y).toBeLessThan(name.y + name.height);
});
