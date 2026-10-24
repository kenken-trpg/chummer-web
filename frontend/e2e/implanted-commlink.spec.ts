import { expect, test, type Page } from "@playwright/test";
import { freshCharacter, storedCharacters, waitForEditor } from "./helpers";

/** A commlink implanted in the headware Commlink (SR5 p.451): put in from the
 *  ware row, named as implanted on the gear tab, kept across a reload, and
 *  carried again once taken out. */
const NAME = "Implant regression";
const HOUSING = "6b219dfa-310a-45ab-98af-40a62e2431cf"; // headware Commlink
const IKON = "6de5a1b0-30e2-4c74-8646-971f698cb231"; // Hermes Ikon

async function commlinks(page: Page) {
  const ch = (await storedCharacters(page)).find((s) => s.name === NAME) as unknown as {
    commlinks?: { gear_id: string; parent_id?: string | null }[];
  };
  return (ch?.commlinks || []).map((row) => [row.gear_id, row.parent_id ?? null]);
}

test("a commlink goes into the headware Commlink and back out", async ({ page, request }) => {
  const state = await freshCharacter(request, NAME);
  Object.assign(state, {
    priorities: { Heritage: "E", Attributes: "B", Talent: "C", Skills: "D", Resources: "A" },
    cyberware: [{ id: "head", ware_id: HOUSING, rating: 1, grade: "Standard" }],
  });
  await page.goto("/");
  await waitForEditor(page);
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)", { exact: true }).setInputFiles({
    name: "implant.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(state)),
  });
  await expect(page.getByRole("textbox", { name: "キャラクター名" })).toHaveValue(NAME);

  await page.getByRole("button", { name: "サイバー", exact: true }).click();
  await page.getByRole("combobox", { name: /中に入れるものを選ぶ$/ }).selectOption(IKON);
  await page.getByRole("button", { name: /: 入れる$/ }).click();
  await expect.poll(() => commlinks(page)).toEqual([[IKON, "head"]]);
  // one device to a housing: nothing more is offered
  await expect(page.getByRole("combobox", { name: /中に入れるものを選ぶ$/ })).toHaveCount(0);

  await page.getByRole("button", { name: "装備", exact: true }).click();
  await page.getByRole("button", { name: "コムリンク", exact: true }).click();
  await expect(page.getByText(/^(Commlink|コムリンク) に埋め込み$/)).toBeVisible();

  await page.reload();
  await waitForEditor(page);
  await page.getByRole("button", { name: "装備", exact: true }).click();
  await page.getByRole("button", { name: "コムリンク", exact: true }).click();
  await expect(page.getByText(/^(Commlink|コムリンク) に埋め込み$/)).toBeVisible();

  await page.getByRole("button", { name: "サイバー", exact: true }).click();
  await page.getByRole("button", { name: "取り出す" }).click();
  await expect.poll(() => commlinks(page)).toEqual([[IKON, null]]);
  await page.getByRole("button", { name: "装備", exact: true }).click();
  await page.getByRole("button", { name: "コムリンク", exact: true }).click();
  // the commlink row first, so "not implanted" is read off a drawn list
  await expect(page.getByText(/Hermes Ikon/).first()).toBeVisible();
  await expect(page.getByText(/に埋め込み/)).toHaveCount(0);
});
