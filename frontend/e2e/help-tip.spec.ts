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
    const button = page.getByRole("button", { name: "物理/精神/社会リミット の説明" });
    const tip = page.locator(`[id="${await button.getAttribute("aria-describedby")}"]`);
    const viewport = page.viewportSize()!;

    await expect(tip).toBeHidden();
    await button.hover();
    await expect(tip).toBeVisible();
    await expect(tip).toContainText("物理リミット = (BOD×2 + AGI + REA + STR)");

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
    await page.setViewportSize({ width: 390, height: 780 });
    await page.goto("/");
    await waitForEditor(page);
    const button = page.getByRole("button", { name: "物理/精神/社会リミット の説明" });
    const tip = page.locator(`[id="${await button.getAttribute("aria-describedby")}"]`);

    await button.click(); // a phone has no hover
    await expect(tip).toBeVisible();
    const box = (await tip.boundingBox())!;
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.x + box.width).toBeLessThanOrEqual(390);

    await page.emulateMedia({ media: "print" });
    await expect(tip).toBeHidden();
    await expect(button).toBeHidden();
  });
});
