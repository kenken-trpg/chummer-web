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
    // and the box goes with it, though the button still has focus — CSS
    // `:focus-within` used to keep it up after the state said closed
    await expect(button).toBeFocused();
    await expect(tip).toBeHidden();
  });

  test("a second click closes it, and the pointer can cross to the box", async ({ page }) => {
    await page.goto("/");
    await waitForEditor(page);
    const button = page.getByRole("button", { name: "身体/精神/社交リミット の説明" });
    const tip = page.locator(`[id="${await button.getAttribute("aria-describedby")}"]`);

    // still hovered and focused after the second click, which is what kept
    // the box up before
    await button.click();
    await expect(tip).toBeVisible();
    await button.click();
    await expect(tip).toBeHidden();

    // Escape with only the pointer on it, focus elsewhere
    await page.mouse.move(0, 0);
    await button.blur();
    await button.hover();
    await expect(tip).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(tip).toBeHidden();

    // hover, then walk the pointer straight down across the gap into the box
    // a pixel at a time, with no focus to hold it open on the way
    await page.mouse.move(0, 0);
    await button.hover();
    await expect(tip).toBeVisible();
    await expect(button).not.toBeFocused();
    const from = (await button.boundingBox())!;
    const to = (await tip.boundingBox())!;
    const x = from.x + from.width / 2;
    expect(x).toBeGreaterThan(to.x);
    expect(x).toBeLessThan(to.x + to.width);
    const y0 = from.y + from.height / 2;
    const y1 = to.y + 10;
    await page.mouse.move(x, y0);
    await page.mouse.move(x, y1, { steps: Math.ceil(y1 - y0) });
    await expect(tip).toBeVisible();
  });

  test('the "?" takes a 24px tap', async ({ page }) => {
    await page.goto("/");
    await waitForEditor(page);
    const button = page.getByRole("button", { name: "身体/精神/社交リミット の説明" });
    const b = (await button.boundingBox())!;
    expect(b.width).toBeLessThan(24); // the circle itself stays small
    const cx = b.x + b.width / 2;
    const cy = b.y + b.height / 2;
    const hits = await button.evaluate(
      (el, points) => points.map(([x, y]) => el.contains(document.elementFromPoint(x, y))),
      [
        [cx - 11, cy],
        [cx + 11, cy],
        [cx, cy - 11],
        [cx, cy + 11],
      ],
    );
    expect(hits).toEqual([true, true, true, true]);
  });

  test("opens upward at the bottom of the sidebar instead of being clipped", async ({ page }) => {
    await page.goto("/");
    await waitForEditor(page);
    const side = page.locator("aside.side");
    const button = side.locator(".help-tip-button").last();
    await button.evaluate((el) => el.scrollIntoView({ block: "end" }));
    await button.hover();
    const tip = page.locator(`[id="${await button.getAttribute("aria-describedby")}"]`);
    await expect(tip).toBeVisible();
    const box = (await tip.boundingBox())!;
    const s = (await side.boundingBox())!;
    const b = (await button.boundingBox())!;
    expect(box.y + box.height).toBeLessThanOrEqual(s.y + s.height);
    expect(box.y + box.height).toBeLessThanOrEqual(b.y);
  });

  // The skills list truncates long names, and the cell that did it clipped
  // the box too: every "?" there opened onto nothing. A category is also a
  // `content-visibility` block, which clips its last rows' boxes the same way.
  // Visibility alone does not catch either — the clipped box is "visible" —
  // so ask what is actually drawn at its corners.
  test("are drawn, not clipped, on the skills tab", async ({ page }) => {
    await page.goto("/");
    await waitForEditor(page);
    await page.getByRole("button", { name: "技能", exact: true }).click();
    const row = page.locator(".skill-cat-block .skill-row");
    for (const target of [row.first(), row.last()]) {
      const button = target.locator(".help-tip-button").first();
      // Focus, not hover: the categories above settle from their estimated
      // height as they render, which shifts the page under a parked mouse.
      // A focused tip stays open while the box itself is scrolled into view
      // — `elementFromPoint` sees nothing past the viewport.
      await button.focus();
      const tip = page.locator(`[id="${await button.getAttribute("aria-describedby")}"]`);
      await expect(tip).toBeVisible();
      await tip.evaluate((el) => el.scrollIntoView({ block: "center" }));
      const drawn = await tip.evaluate((el) => {
        const r = el.getBoundingClientRect();
        return [
          [r.left + 4, r.top + 4],
          [r.right - 4, r.bottom - 4],
        ].every(([x, y]) => el.contains(document.elementFromPoint(x, y)));
      });
      expect(drawn).toBe(true);
    }
  });

  test("a skill's box wraps inside a phone-width screen", async ({ page }) => {
    // the name cell is `nowrap`, and the box used to inherit it
    await page.setViewportSize({ width: 390, height: 780 });
    await page.goto("/");
    await waitForEditor(page);
    await page.getByRole("button", { name: "技能", exact: true }).click();
    const button = page.locator(".skill-cat-block .skill-row .help-tip-button").first();
    // focus, not click: at this width the sticky tab bar can sit over the
    // first row, and the click lands on the bar instead
    await button.focus();
    const tip = page.locator(`[id="${await button.getAttribute("aria-describedby")}"]`);
    await expect(tip).toBeVisible();
    const overflow = await tip.evaluate((el) => el.scrollWidth - el.clientWidth);
    expect(overflow).toBeLessThanOrEqual(0);
    const box = (await tip.boundingBox())!;
    expect(box.x + box.width).toBeLessThanOrEqual(390);
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
