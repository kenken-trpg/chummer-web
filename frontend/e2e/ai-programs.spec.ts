import { expect, test, type Page } from "@playwright/test";
import type { Character } from "../lib/types";
import { waitForEditor } from "./helpers";

/** An A.I.'s programs from the creation screen (DT p.158): a Protosapient
 *  picks its Inherent Program on the qualities tab, then buys an advanced
 *  program that builds on it, at 8 karma, from the programs tab. */
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

function programs(ch: Character) {
  return {
    rows: (ch.derived.ai_programs || []).map((row) => [row.name, row.free, row.karma]),
    karma: (ch.derived.karma_spend_breakdown || []).find(
      (row) => row.notice.key === "engine.spend.aiPrograms",
    )?.amount,
  };
}

test("a Protosapient picks its Inherent Program and buys on top of it", async ({ page }) => {
  await page.goto("/");
  await waitForEditor(page);
  await page.getByRole("button", { name: "ルールブックを選ぶ", exact: true }).click();
  const dt = page.getByRole("checkbox", { name: /\(DT\)/ });
  if (!(await dt.isChecked())) await dt.click();
  await expect
    .poll(async () => (await currentCharacter(page)).settings?.books?.includes("DT"))
    .toBe(true);
  await page.getByRole("button", { name: "メタタイプ", exact: true }).click();
  await page.getByRole("button", { name: /^A\.I\./ }).click();
  await expect.poll(async () => (await currentCharacter(page)).metatype).toBe("A.I.");
  await page.getByRole("combobox", { name: "メタバリアント" }).selectOption("Protosapient");
  await expect.poll(async () => (await currentCharacter(page)).metavariant).toBe("Protosapient");

  await page.getByRole("button", { name: "資質", exact: true }).click();
  const inherent = page
    .locator(".cyber-item, .quality-item")
    .filter({ hasText: "Inherent Program" });
  await inherent.getByRole("combobox").first().selectOption("Exploit");
  await expect
    .poll(async () => programs(await currentCharacter(page)).rows)
    .toEqual([["Exploit", true, 0]]);

  await page.getByRole("button", { name: "プログラム", exact: true }).click();
  await page.getByRole("combobox", { name: "カテゴリー" }).selectOption("Advanced Programs");
  const authority = page.locator(".quality-list .quality-item").filter({ hasText: "Authority" });
  await expect(authority).toContainText("8カルマ");
  await authority.getByRole("button", { name: "追加" }).click();
  const bought = {
    rows: [
      ["Exploit", true, 0],
      ["Authority", false, 8],
    ],
    karma: 8,
  };
  await expect.poll(async () => programs(await currentCharacter(page))).toEqual(bought);
  expect((await currentCharacter(page)).derived.errors).toEqual([]);

  await page.reload();
  await waitForEditor(page);
  await expect.poll(async () => programs(await currentCharacter(page))).toEqual(bought);
});
