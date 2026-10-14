import { expect, test } from "@playwright/test";

/**
 * The manual is the one page here that is plain HTML in `public/`, and the one
 * whose assets are addressed relatively — `img/…`, so that the same directory
 * also works at the GitHub Pages prefix. Relative links are decided by the URL
 * the browser settles on, which no unit test and no header check can see: with
 * `/manual` rewritten rather than redirected, every screenshot resolved to
 * `/img/…` and 404'd while the page itself still returned 200.
 */
test("the manual loads every screenshot from the short URL", async ({ page }) => {
  const missing: string[] = [];
  page.on("response", (res) => {
    if (res.status() >= 400) missing.push(`${res.status()} ${res.url()}`);
  });

  await page.goto("/manual");
  // the redirect, not a rewrite: relative assets hang off this path
  await expect(page).toHaveURL(/\/manual\/index\.html$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(/利用マニュアル/);

  const images = page.locator("figure img");
  expect(await images.count()).toBeGreaterThan(10);
  const broken = await images.evaluateAll((all) =>
    all
      .filter((img) => !(img as HTMLImageElement).naturalWidth)
      .map((img) => img.getAttribute("src")),
  );
  expect(broken).toEqual([]);
  expect(missing).toEqual([]);
});
