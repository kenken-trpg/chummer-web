import { expect, test } from "@playwright/test";
import { openExportMenu, waitForEditor } from "./helpers";

test("detailed Matrix actions can be copied without a deck and switched off", async ({
  page,
  context,
}, testInfo) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"], {
    origin: String(testInfo.project.use.baseURL),
  });
  await page.goto("/");
  await waitForEditor(page);
  const read = () => page.evaluate(() => navigator.clipboard.readText());
  const checkbox = page.getByRole("checkbox", { name: "マトリックス系詳細チャットパレット" });
  await openExportMenu(page);
  await expect(checkbox).not.toBeChecked();
  await checkbox.check();
  await page.getByRole("button", { name: "チャットパレット", exact: true }).click();
  await expect.poll(read).toContain("アイコンを追跡する");
  const palette = await read();
  expect(palette.split("\n").filter((line) => line.includes("日本語版 p."))).toHaveLength(21);
  expect(palette).toMatch(/強制介入する.*［.*＋.*＝\d+］/);
  await openExportMenu(page);
  await page.getByRole("button", { name: "ココフォリア", exact: true }).click();
  await expect.poll(read).toContain('"kind":"character"');
  expect(JSON.parse(await read()).data.commands).toBe(palette);
  await page.reload();
  await waitForEditor(page);
  await openExportMenu(page);
  await expect(checkbox).toBeChecked();
  await checkbox.uncheck();
  await page.getByRole("button", { name: "チャットパレット", exact: true }).click();
  await expect.poll(read).not.toContain("日本語版 p.");
});
