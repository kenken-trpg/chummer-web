import { expect, test } from "@playwright/test";
import { waitForEditor } from "./helpers";

/**
 * The "?" boxes: jsdom can say what they contain, but not where they land or
 * whether print drops them. The sidebar sits against the right edge, so a box
 * that hangs off its label's left corner runs off-screen — that is what this
 * watches for.
 */
test.describe("help tips", () => {
  test("open on hover and on the keyboard, and stay on screen", async ({ page }) => {
    await page.goto("/");
    await waitForEditor(page);
    const button = page.getByRole("button", { name: "身体/精神/社交リミット の説明" });
    const tip = page.locator(`[id="${await button.getAttribute("aria-describedby")}"]`);
    const viewport = page.viewportSize()!;

    await expect(tip).toBeHidden();
    await button.hover();
    await expect(tip).toBeVisible();
    // the formula, not the wording around it: which word names the limit is
    // the dictionaries' business and is asserted in the unit suite
    await expect(tip).toContainText("(STR×2 + BOD + REA)");

    // inside the sidebar, which scrolls: what leaves it is clipped, not just
    // off-screen, so the box has to fit the panel and not merely the window
    const box = (await tip.boundingBox())!;
    const side = (await page.locator("aside.side").boundingBox())!;
    expect(box.x).toBeGreaterThanOrEqual(side.x);
    expect(box.x + box.width).toBeLessThanOrEqual(side.x + side.width);
    expect(box.x + box.width).toBeLessThanOrEqual(viewport.width);

    // keyboard: focus shows it, Escape closes what Enter opened
    await page.mouse.move(viewport.width / 2, viewport.height - 5);
    await expect(tip).toBeHidden();
    await button.focus();
    await expect(tip).toBeVisible();
    await page.keyboard.press("Enter");
    await expect(button).toHaveAttribute("aria-expanded", "true");
    await page.keyboard.press("Escape");
    await expect(button).toHaveAttribute("aria-expanded", "false");
  });

  test("stay inside a phone-width screen and print nothing", async ({ page }) => {
    for (const width of [390, 320]) {
      await page.setViewportSize({ width, height: 780 });
      await page.goto("/");
      await waitForEditor(page);
      const button = page.getByRole("button", { name: "身体/精神/社交リミット の説明" });
      const tip = page.locator(`[id="${await button.getAttribute("aria-describedby")}"]`);

      await button.click(); // a phone has no hover
      await expect(tip).toBeVisible();
      const box = (await tip.boundingBox())!;
      const side = (await page.locator("aside.side").boundingBox())!;
      expect(box.x).toBeGreaterThanOrEqual(Math.max(0, side.x));
      expect(box.x + box.width).toBeLessThanOrEqual(Math.min(width, side.x + side.width));
    }

    const button = page.getByRole("button", { name: "身体/精神/社交リミット の説明" });
    const tip = page.locator(`[id="${await button.getAttribute("aria-describedby")}"]`);
    await page.emulateMedia({ media: "print" });
    await expect(tip).toBeHidden();
    await expect(button).toBeHidden();
  });
});
