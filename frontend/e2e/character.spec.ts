import { expect, test, type Page } from "@playwright/test";

/**
 * The one flow the unit suite structurally cannot cover: a character is created
 * by the Python engine, stored in the browser's IndexedDB, survives a reload,
 * and comes back out as a Chummer-compatible `.chum5`.
 *
 * Every step here crosses a boundary that is mocked in vitest — `lib/api` is
 * `vi.mock`ed, `local-store` is a Map, and jsdom has no IndexedDB at all. If
 * this passes, the app actually works end to end.
 */

/** The editor mints a character on first load; wait for the toolbar it fills. */
async function waitForEditor(page: Page) {
  await expect(page.getByRole("textbox", { name: "キャラクター名" })).toBeVisible();
}

test("a character survives a reload and exports to .chum5", async ({ page }) => {
  await page.goto("/");
  await waitForEditor(page);

  const name = page.getByRole("textbox", { name: "キャラクター名" });
  await name.fill("Testrunner");
  // the editor patches on blur, so move focus before asserting anything
  await name.blur();

  // Edit through the engine: pick a metatype and let the sidebar totals move.
  await page.getByRole("button", { name: "メタ" }).click();
  await page.getByRole("button", { name: /Ork/ }).first().click();

  await page.getByRole("button", { name: "能力値" }).click();
  const body = page.getByRole("slider").first();
  await body.focus();
  await page.keyboard.press("ArrowRight");

  // A reload proves IndexedDB, not React state: the roster picker is populated
  // from storage on boot and `lastCharacterId` decides which one opens.
  await page.reload();
  await waitForEditor(page);
  await expect(page.getByRole("textbox", { name: "キャラクター名" })).toHaveValue("Testrunner");
  await expect(page.getByRole("combobox", { name: "保存済みキャラクター" })).toContainText(
    "Testrunner",
  );

  // The export round-trips the stored state through the backend's XML writer.
  const download = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: ".chum5書出" }).click(),
  ]).then(([d]) => d);

  expect(download.suggestedFilename()).toBe("Testrunner.chum5");
});

test("the sheet renders and a share link round-trips through the URL fragment", async ({
  page,
  context,
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.goto("/");
  await waitForEditor(page);
  await page.getByRole("textbox", { name: "キャラクター名" }).fill("Sharetest");
  await page.getByRole("textbox", { name: "キャラクター名" }).blur();

  // exact: the toolbar also has a "シート表示" button
  await page.getByRole("button", { name: "シート", exact: true }).click();
  await expect(page.getByRole("combobox", { name: "レイアウト" })).toBeVisible();

  await page.getByRole("button", { name: /共有リンク|コピー ✓/ }).click();
  const url = await page.evaluate(() => navigator.clipboard.readText());
  expect(url).toContain("/share#c=");

  // The whole character rides in the fragment, which never reaches the server —
  // so this must render with no roster and no backend character lookup.
  const visitor = await context.newPage();
  await visitor.goto(url);
  await expect(visitor.getByText("Sharetest").first()).toBeVisible();
});
