import { expect, test } from "@playwright/test";
import { waitForEditor } from "./helpers";

/**
 * The catalog list used to stop at 58vh, and never grew past 760px whatever
 * the window did, so a tall screen sat half empty. The height comes from the
 * viewport now, which is exactly the kind of thing a later `max-height` put
 * back in the wrong place would undo without anything else noticing.
 *
 * Both bounds matter: the box has to grow, and it has to stay inside one
 * viewport, because the footnote that says the list is cut off is stuck to the
 * bottom of the box and goes out of reach once the box is taller than the
 * window.
 */
test("the catalog list follows a tall window", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 1400 });
  await page.goto("/");
  await waitForEditor(page);

  await page.getByRole("button", { name: "資質", exact: true }).click();
  const list = page.locator(".quality-list");
  await expect(list).toBeVisible();

  const height = await list.evaluate((el) => el.getBoundingClientRect().height);
  expect(height).toBeGreaterThan(900);
  expect(height).toBeLessThanOrEqual(1400);
});
