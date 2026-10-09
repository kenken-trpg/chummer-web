import { expect, test } from "@playwright/test";
import { waitForEditor } from "./helpers";

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
