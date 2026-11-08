import { expect, test } from "@playwright/test";
import { enterCareer, storedCharacters, waitForEditor } from "./helpers";

test("creation review can return to editing and only starts career after confirmation", async ({
  page,
}) => {
  await page.goto("/");
  await waitForEditor(page);
  const start = page.getByRole("button", { name: "作成完了（キャリア）", exact: true });
  await start.click();
  const review = page.getByRole("region", { name: "作成完了前の確認" });
  await expect(review).toBeVisible();
  await expect(review.getByRole("table", { name: "残りポイント・資金" })).toBeVisible();
  expect((await storedCharacters(page))[0].career).not.toBe(true);
  await review.getByRole("button", { name: "作成を続ける", exact: true }).click();
  await expect(review).toHaveCount(0);
  await expect(start).toBeVisible();

  await start.click();
  await review.getByRole("button", { name: "該当タブへ（カルマ）", exact: true }).click();
  await expect(review).toHaveCount(0);
  await expect(
    page
      .getByRole("navigation", { name: "セクション" })
      .getByRole("button", { name: "資質", exact: true }),
  ).toHaveAttribute("aria-current", "true");
  await enterCareer(page);
  await expect.poll(async () => (await storedCharacters(page))[0].career).toBe(true);
  await page.reload();
  await waitForEditor(page);
  await expect(page.getByRole("button", { name: "キャリア中", exact: true })).toBeVisible();
});
