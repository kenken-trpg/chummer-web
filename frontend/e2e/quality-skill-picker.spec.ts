import { expect, test } from "@playwright/test";
import { freshCharacter, waitForEditor } from "./helpers";

test("Confidence suppresses a specialization and can move to a learned exotic target", async ({
  page,
  request,
}) => {
  const quality = "c9cd05ad-cd3c-451e-8285-e0fb1d95ebc1";
  const exotic = "Exotic Ranged Weapon (Lasers)";
  const seed = await freshCharacter(request, "Confidence effects");
  Object.assign(seed, {
    skills: { Blades: 4 },
    skill_specializations: { Blades: "Swords" },
    quality_ids: [quality],
    skill_picks: { [`quality:${quality}:0`]: "Blades" },
    exotic_skills: [
      { id: "lasers", skill_name: "Exotic Ranged Weapon", extra: "Lasers", rating: 4 },
    ],
  });
  await page.goto("/");
  await waitForEditor(page);
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)").setInputFiles({
    name: "confidence.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(seed)),
  });
  await expect(page.getByRole("textbox", { name: "キャラクター名" })).toHaveValue(
    "Confidence effects",
  );
  const skillsTab = page.getByRole("button", { name: "技能", exact: true });
  const qualitiesTab = page.getByRole("button", { name: "資質", exact: true });
  await skillsTab.click();
  const bladeRow = page
    .locator(".skill-row")
    .filter({ has: page.getByRole("slider", { name: "刀剣", exact: true }) });
  await expect(bladeRow).toContainText("専門化の効果なし");
  await expect(bladeRow.locator("select").first()).toHaveValue("Swords");
  await expect(bladeRow.locator("b")).toContainText("4 -2");

  await qualitiesTab.click();
  const owned = page.locator(".card > .quality-item").filter({ hasText: "Loss of Confidence" });
  const choice = owned.getByRole("combobox", { name: "自信喪失 の技能 -2" });
  await expect(choice.locator(`option[value="${exotic}"]`)).toContainText("特殊射撃武器");
  await choice.selectOption(exotic);
  await skillsTab.click();
  await expect(bladeRow).toContainText("専門+2");
  await expect(bladeRow).not.toContainText("専門化の効果なし");
  const exoticRow = page
    .locator(".skill-row")
    .filter({ has: page.getByRole("slider", { name: "特殊射撃武器", exact: true }) });
  await expect(exoticRow.locator("b")).toHaveText("4 -2");

  await page.reload();
  await waitForEditor(page);
  await qualitiesTab.click();
  await expect(choice).toHaveValue(exotic);
  await owned.getByRole("button", { name: "削除", exact: true }).click();
  await skillsTab.click();
  await expect(bladeRow.locator("select").first()).toHaveValue("Swords");
  await expect(bladeRow).toContainText("専門+2");
  await expect(exoticRow.locator("b")).toHaveText("4");
});

for (const width of [1280, 390]) {
  test(`a quality explains its skill requirement and saves the chosen skill at ${width}px`, async ({
    page,
  }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    await waitForEditor(page);
    const qualitiesTab = page.getByRole("button", { name: "資質", exact: true });
    await qualitiesTab.click();
    await page.getByPlaceholder("資質を検索").fill("自信喪失");
    const catalogRow = page
      .locator(".quality-list .quality-item")
      .filter({ hasText: "Loss of Confidence" });
    await catalogRow.getByRole("button", { name: "追加", exact: true }).click();

    const ownedRow = page
      .locator(".card > .quality-item")
      .filter({ hasText: "Loss of Confidence" });
    const choice = ownedRow.getByRole("combobox", { name: "自信喪失 の技能 -2" });
    await expect(choice).toBeVisible();
    await expect(choice).toBeDisabled();
    await expect(ownedRow).toContainText("対象はレーティング4以上の技能です。");
    await expect(ownedRow).toContainText(
      "「技能」タブで対象にしたい技能をレーティング4以上にしてください。",
    );
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
      width + 1,
    );
    await ownedRow.screenshot({ path: test.info().outputPath("empty-skill-choice.png") });

    await page.getByRole("button", { name: "技能", exact: true }).click();
    const rating = page.getByRole("slider", { name: "体術", exact: true });
    await rating.focus();
    for (let value = 1; value <= 4; value++) {
      await Promise.all([
        page.waitForResponse((response) => {
          if (
            !response.url().endsWith("/api/characters/patch") ||
            response.request().method() !== "POST"
          )
            return false;
          return response.request().postDataJSON()?.patch?.skills?.Gymnastics === value;
        }),
        rating.press("ArrowRight"),
      ]);
      await expect(rating).toHaveValue(String(value));
    }
    await qualitiesTab.click();
    await expect(choice).toBeEnabled();
    await choice.selectOption("Gymnastics");
    await expect(choice).toHaveValue("Gymnastics");
    await expect(ownedRow).not.toContainText("「技能」タブで対象にしたい技能");

    await page.reload();
    await waitForEditor(page);
    await qualitiesTab.click();
    await expect(choice).toHaveValue("Gymnastics");
    await expect(ownedRow).toContainText("対象はレーティング4以上の技能です。");
    await ownedRow.screenshot({ path: test.info().outputPath("selected-skill-choice.png") });
  });
}
