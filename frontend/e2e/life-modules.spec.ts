import { expect, test } from "@playwright/test";
import { freshCharacter, storedCharacters, waitForEditor } from "./helpers";

test("life modules persist across reload and removing a module removes its grants", async ({
  page,
  request,
}) => {
  const seed = {
    ...(await freshCharacter(request, "Life module regression")),
    build_method: "LifeModule",
    settings: { books: ["SR5", "RF"] },
  };
  await page.goto("/");
  await waitForEditor(page);
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)").setInputFiles({
    name: "history.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(seed)),
  });
  await expect(page.getByRole("textbox", { name: "キャラクター名" })).toHaveValue(
    "Life module regression",
  );
  // The stage name is Run Faster data, so it reads in English in the Japanese UI.
  const picker = page.getByRole("group", { name: "Real Life: 経歴を選択" });
  await page.getByRole("searchbox", { name: /経歴を検索/ }).fill("bounty hunter");
  await expect(picker.getByRole("radio")).toHaveCount(1);
  const candidate = picker.getByRole("radio", { name: /Bounty Hunter/ });
  await candidate.focus();
  await candidate.press("Space");
  await expect(candidate).toBeChecked();
  await expect(page.getByRole("button", { name: "Bounty Hunter: この経歴を削除" })).toHaveCount(0);
  await expect(picker.locator(".life-preview")).toContainText("100 Karma");
  await picker.getByRole("button", { name: "この経歴を追加" }).click();
  const saved = async () =>
    (await storedCharacters(page)).find(
      (row) => row.name === "Life module regression",
    ) as unknown as {
      life_modules: string[];
      attributes: { BOD: number };
      derived: { totals: { BOD: number }; karma: { spent: number } };
    };
  await expect.poll(async () => (await saved())?.derived?.totals?.BOD).toBe(2);
  expect((await saved()).attributes.BOD).toBe(1);
  expect((await saved()).derived.karma.spent).toBe(100);
  await page.reload();
  await waitForEditor(page);
  await expect(page.getByRole("button", { name: "Bounty Hunter: この経歴を削除" })).toBeVisible();
  await page.getByRole("button", { name: "Bounty Hunter: この経歴を削除" }).click();
  await expect.poll(async () => (await saved())?.life_modules).toEqual([]);
  await expect.poll(async () => (await saved())?.derived?.totals?.BOD).toBe(1);
  expect((await saved()).derived.karma.spent).toBe(0);
});

test("life module layout keeps choices and actions inside desktop and mobile viewports", async ({
  page,
  request,
}, testInfo) => {
  const seed = {
    ...(await freshCharacter(request, "Life module layout")),
    build_method: "LifeModule",
    settings: { books: ["SR5", "RF", "TCG"] },
    life_modules: [
      "4fe5e4fd-0275-48bd-9fec-678b86c5f024",
      "47bf63cf-9a2a-4008-b455-c8ab68add581",
      "47bf63cf-9a2a-4008-b455-c8ab68add581",
    ],
  };
  await page.goto("/");
  await waitForEditor(page);
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)").setInputFiles({
    name: "layout.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(seed)),
  });
  const panel = page.locator(".life-modules");
  await expect(panel.getByRole("heading", { name: "SINless" })).toBeVisible();
  await expect(panel.getByRole("heading", { name: "Bounty Hunter" })).toHaveCount(2);
  await expect(panel.locator(".life-status")).toHaveCount(2);
  const method = await page
    .getByRole("button", { name: "ライフモジュール", exact: true })
    .boundingBox();
  const heading = await panel.getByRole("heading", { name: "ライフモジュール" }).boundingBox();
  expect(method!.y).toBeLessThan(heading!.y);

  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    const fields = panel.locator(".life-choices").first().locator("select, input");
    await expect(fields).toHaveCount(2);
    const first = await fields.nth(0).boundingBox();
    const second = await fields.nth(1).boundingBox();
    if (width <= 390) expect(second!.y).toBeGreaterThan(first!.y);
    else expect(Math.abs(second!.y - first!.y)).toBeLessThan(2);

    const candidates = panel.getByRole("group", { name: "Real Life: 経歴を選択" });
    await candidates.getByRole("radio", { name: /Trog Professional/ }).check();
    await expect(candidates.locator(".life-preview")).toContainText("前提条件を満たしていません");
    await expect(candidates.getByRole("button", { name: "この経歴を追加" })).toBeDisabled();
    const summary = panel.locator("summary").first();
    await summary.click();
    await expect(panel.locator("details").first()).toHaveAttribute("open", "");
    for (const control of await panel.locator("input, select, button").all()) {
      const box = await control.boundingBox();
      expect(box!.x).toBeGreaterThanOrEqual(0);
      expect(box!.x + box!.width).toBeLessThanOrEqual(width);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
      width,
    );
    await panel.screenshot({ path: testInfo.outputPath(`life-modules-${width}.png`) });
    await candidates.screenshot({
      path: testInfo.outputPath(`life-candidates-${width}.png`),
      style: ".tabs { visibility: hidden; }",
    });
    await summary.click();
  }
});
