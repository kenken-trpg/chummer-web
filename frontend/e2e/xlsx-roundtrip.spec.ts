import { expect, test } from "@playwright/test";
import { waitForEditor } from "./helpers";

/**
 * The キャラシテンプレート .xlsx, out of the browser and back in.
 *
 * The backend's pytest round-trips the same bytes in Python, and vitest mocks
 * the two calls — what neither reaches is the path a player actually takes: the
 * toolbar button, the review panel the check puts in front of the download, the
 * browser's own download, and the file going back through the hidden input by
 * its name. No fixture is needed and none is committed: the character is built
 * here and the workbook is the one this app just wrote.
 */
test("a character exports as the sheet's .xlsx and comes back in through the browser", async ({
  page,
}) => {
  await page.goto("/");
  await waitForEditor(page);

  // exact: the priority table's cells read 全てのメタタイプ as well
  await page.getByRole("button", { name: "メタタイプ", exact: true }).click();
  await page.getByRole("button", { name: /Ork/ }).first().click();

  const sidebar = page.locator("aside.side");
  await expect(sidebar).toContainText("オーク");

  // The sheet has no cell for the settings (which rulebooks are in play), so
  // the check always finds that one difference and the panel always appears —
  // this is the .xlsx path's normal flow, not an edge case.
  await page.getByRole("button", { name: ".xlsx書出" }).click();
  const review = page.getByRole("alertdialog");
  await expect(review).toContainText(".xlsx");

  const download = await Promise.all([
    page.waitForEvent("download"),
    review.getByRole("button", { name: "このまま書き出す" }).click(),
  ]).then(([d]) => d);
  // saveAs, not path(): Playwright's temp file has no extension, and the
  // editor picks its reader off the file name
  const xlsx = test.info().outputPath("roundtrip.xlsx");
  await download.saveAs(xlsx);

  await page.getByLabel("読込 (JSON/.chum5/.xlsx)").setInputFiles(xlsx);

  // The template carries no character name, so the import names the runner
  // itself — that the roster grew and the metatype survived is what says the
  // workbook was read rather than the original character reopened.
  const roster = page.getByRole("combobox", { name: "保存済みキャラクター" });
  await expect(roster.getByRole("option", { name: /Imported Runner/ })).toHaveCount(1);
  await expect(sidebar).toContainText("オーク");

  // and it survives a reload, so the imported character reached IndexedDB
  await page.reload();
  await waitForEditor(page);
  await expect(page.locator("aside.side")).toContainText("オーク");
});
