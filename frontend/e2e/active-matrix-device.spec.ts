import { expect, test, type Page } from "@playwright/test";
import { freshCharacter, storedCharacters, waitForEditor } from "./helpers";

/** The device a character runs in the Matrix (Chummer's active commlink):
 *  automatic is the one with the highest Data Processing, a pick moves the
 *  sheet's Matrix row to the other one, and the pick is kept across a reload. */
const NAME = "Active device regression";
const META_LINK = "89a0f3c9-5ef6-41cd-981f-4ac690ee2ab3";
const IKON = "6de5a1b0-30e2-4c74-8646-971f698cb231"; // Hermes Ikon
// the sheet and the picker show the Japanese names
const META_NAME = /メタリンク|Meta Link/;
const IKON_NAME = /ヘルメス・アイコン|Hermes Ikon/;

async function picked(page: Page) {
  const ch = (await storedCharacters(page)).find((s) => s.name === NAME) as unknown as {
    active_matrix_device?: string;
    commlinks?: { id: string; gear_id: string }[];
  };
  const row = (ch?.commlinks || []).find((c) => c.id === ch?.active_matrix_device);
  return row?.gear_id ?? ch?.active_matrix_device ?? "";
}

test("the picked commlink is the one the sheet runs, and stays picked", async ({
  page,
  request,
}) => {
  const state = await freshCharacter(request, NAME);
  Object.assign(state, {
    priorities: { Heritage: "E", Attributes: "B", Talent: "C", Skills: "D", Resources: "A" },
    commlinks: [
      { id: "meta", gear_id: META_LINK },
      { id: "ikon", gear_id: IKON },
    ],
  });
  await page.goto("/");
  await waitForEditor(page);
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)", { exact: true }).setInputFiles({
    name: "active-device.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(state)),
  });
  await expect(page.getByRole("textbox", { name: "キャラクター名" })).toHaveValue(NAME);

  const sheetRow = (name: RegExp) =>
    page.locator("tr", { hasText: name }).filter({ hasText: /冷\d+\+\dd6/ });

  await page.getByRole("button", { name: "シート", exact: true }).click();
  await expect(sheetRow(IKON_NAME)).toBeVisible();

  await page.getByRole("button", { name: "装備", exact: true }).click();
  const picker = page.getByRole("combobox", { name: /マトリックスで使う機器/ });
  await expect(picker).toHaveValue("");
  const meta = await picker.locator("option", { hasText: META_NAME }).getAttribute("value");
  await picker.selectOption(meta ?? "");
  await expect.poll(() => picked(page)).toBe(META_LINK);

  await page.reload();
  await waitForEditor(page);
  await page.getByRole("button", { name: "装備", exact: true }).click();
  await expect(page.getByRole("combobox", { name: /マトリックスで使う機器/ })).not.toHaveValue("");
  await page.getByRole("button", { name: "シート", exact: true }).click();
  await expect(sheetRow(META_NAME)).toBeVisible();
  await expect(sheetRow(IKON_NAME)).toHaveCount(0);
});
