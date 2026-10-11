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
  const picker = page.getByRole("combobox", { name: "実生活: 経歴を選択" });
  await picker.selectOption("47bf63cf-9a2a-4008-b455-c8ab68add581");
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
