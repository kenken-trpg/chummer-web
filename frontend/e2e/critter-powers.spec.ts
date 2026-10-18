import { expect, test, type Page } from "@playwright/test";
import type { Character } from "../lib/types";
import { waitForEditor } from "./helpers";

/** The Critter Powers tab from the creation screen: an Infected quality
 *  a human can take (Loup-Garou, RF) opens the tab and names the category it
 *  sells, and a power bought there (Digitigrade Legs, DTR) costs its own karma. */
async function currentCharacter(page: Page): Promise<Character> {
  return page.evaluate(
    () =>
      new Promise((resolve, reject) => {
        const open = indexedDB.open("chummer-web");
        open.onerror = () => reject(open.error);
        open.onsuccess = () => {
          const db = open.result;
          const request = db
            .transaction("characters")
            .objectStore("characters")
            .get(localStorage.getItem("lastCharacterId")!);
          request.onsuccess = () => {
            db.close();
            resolve(request.result?.character);
          };
          request.onerror = () => {
            db.close();
            reject(request.error);
          };
        };
      }),
  );
}

function powers(ch: Character) {
  return {
    rows: (ch.derived.critter_powers || []).map((row) => [row.name, row.karma]),
    karma: (ch.derived.karma_spend_breakdown || []).find(
      (row) => row.notice.key === "engine.spend.critterPowers",
    )?.amount,
  };
}

test("an Infected opens the critter powers tab and buys a power with karma", async ({ page }) => {
  await page.goto("/");
  await waitForEditor(page);
  await page.getByRole("button", { name: "ルールブックを選ぶ", exact: true }).click();
  for (const book of ["RF", "DTR"]) {
    const box = page.getByRole("checkbox", { name: new RegExp(`\\(${book}\\)`) });
    if (!(await box.isChecked())) await box.click();
  }
  await expect
    .poll(async () => {
      const books = (await currentCharacter(page)).settings?.books || [];
      return books.includes("RF") && books.includes("DTR");
    })
    .toBe(true);

  const tab = page.getByRole("button", { name: "クリッター・パワー", exact: true });
  await expect(tab).toHaveCount(0);
  await page.getByRole("button", { name: "資質", exact: true }).click();
  await page.getByPlaceholder("資質を検索").fill("Loup-Garou");
  await page
    .locator(".quality-list .quality-item")
    .filter({ hasText: "Infected: Loup-Garou" })
    .getByRole("button", { name: "追加", exact: true })
    .click();
  await expect
    .poll(async () => (await currentCharacter(page)).derived.critter_power_categories)
    .toEqual(["Infected"]);
  const before = (await currentCharacter(page)).derived.karma.remaining;

  await tab.click();
  const legs = page.locator(".quality-list .quality-item").filter({ hasText: "Digitigrade Legs" });
  await expect(legs).toContainText("6カルマ");
  await legs.getByRole("button", { name: "追加", exact: true }).click();
  const bought = { rows: [["Digitigrade Legs", 6]], karma: 6 };
  await expect.poll(async () => powers(await currentCharacter(page))).toEqual(bought);
  const after = await currentCharacter(page);
  expect(after.derived.karma.remaining).toBe(before - 6);
  // the quality's own pick is still open; only this tab's checks are asserted
  expect(after.derived.errors.filter((e) => e.key.startsWith("engine.critterPowers"))).toEqual([]);
  await expect(
    page.locator(".card > .cyber-item").filter({ hasText: "Digitigrade Legs" }),
  ).toBeVisible();

  await page.reload();
  await waitForEditor(page);
  await expect.poll(async () => powers(await currentCharacter(page))).toEqual(bought);
});
