import { readFileSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";
import type { Character } from "../lib/types";
import { encodeFragment, waitForEditor } from "./helpers";

/** Imported development character: this does not expose Centaur in chargen. */
const payload = {
  name: "Centaur persistence",
  metatype: "Centaur",
  talent: "Mundane",
  priorities: { Heritage: "B", Attributes: "A", Talent: "E", Skills: "C", Resources: "D" },
  attributes: { BOD: 3, AGI: 3, REA: 3, STR: 3, CHA: 3, INT: 3, LOG: 3, WIL: 3, EDG: 1, MAG: 3 },
  settings: { name: "Centaur development", books: ["SR5", "RF"] },
};

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

function summary(ch: Character) {
  const kick = ch.derived.weapons?.filter((row) => row.name === "Kick (Centaur)") ?? [];
  return {
    metatype: ch.metatype,
    magic: ch.derived.totals.MAG,
    strength: ch.derived.totals.STR,
    specialUsed: ch.derived.points.special.used,
    powers: ch.derived.metatype_info.powers?.map((row) => row.name),
    qualityCount: ch.derived.qualities.length,
    purchasedQualities: ch.quality_ids,
    purchasedWeapons: ch.weapons,
    kick: kick.map((row) => ({ damage: row.damage, ap: row.ap, reach: row.reach })),
  };
}

const expected = (strength: number) => ({
  metatype: "Centaur",
  magic: 3,
  strength,
  specialUsed: 2,
  powers: ["Search", "Natural Weapon"],
  qualityCount: 4,
  purchasedQualities: [],
  purchasedWeapons: [],
  kick: [{ damage: `${strength + 2}P`, ap: "+1", reach: "1" }],
});

test("Centaur grants and purchased MAG survive share adoption, reload, undo/redo and JSON import", async ({
  page,
}) => {
  await page.goto(`/share#c=${encodeFragment({ v: 1, s: payload })}`);
  await expect(page.getByText("共有ビュー（読み取り専用）")).toBeVisible();
  await expect(
    page.getByText("Kick: DV ({STR} + 2)P, AP +1, +1 Reach", { exact: false }).first(),
  ).toBeVisible();
  await page.getByRole("button", { name: "自分のロースターに取り込む" }).click();
  await expect(page).toHaveURL(/\/$/);
  await waitForEditor(page);
  await expect.poll(async () => summary(await currentCharacter(page))).toEqual(expected(3));
  const sourceId = (await currentCharacter(page)).id;

  await page.reload();
  await waitForEditor(page);
  await expect.poll(async () => summary(await currentCharacter(page))).toEqual(expected(3));

  await page.getByRole("button", { name: "能力値", exact: true }).click();
  // ATTRS order: BOD, AGI, REA, STR. The native MAG slider must also exist.
  await expect(page.getByRole("slider")).toHaveCount(10);
  const strength = page.getByRole("slider").nth(3);
  await strength.focus();
  await page.keyboard.press("ArrowRight");
  await expect.poll(async () => summary(await currentCharacter(page))).toEqual(expected(4));
  await page.getByRole("button", { name: /元に戻す/ }).click();
  await expect.poll(async () => summary(await currentCharacter(page))).toEqual(expected(3));
  await page.getByRole("button", { name: /やり直し/ }).click();
  await expect.poll(async () => summary(await currentCharacter(page))).toEqual(expected(4));

  const download = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "JSON保存", exact: true }).click(),
  ]).then(([file]) => file);
  const path = test.info().outputPath("centaur.json");
  await download.saveAs(path);
  const saved = JSON.parse(readFileSync(path, "utf8")) as Character;
  expect(summary(saved)).toEqual(expected(4));
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)").setInputFiles(path);
  await expect.poll(async () => (await currentCharacter(page)).id).not.toBe(sourceId);
  await expect.poll(async () => summary(await currentCharacter(page))).toEqual(expected(4));
  await page.reload();
  await waitForEditor(page);
  await expect.poll(async () => summary(await currentCharacter(page))).toEqual(expected(4));
});

test("Centaur career keeps purchased MAG as its baseline across growth, undo and JSON import", async ({
  page,
}) => {
  await page.goto(`/share#c=${encodeFragment({ v: 1, s: payload })}`);
  await page.getByRole("button", { name: "自分のロースターに取り込む" }).click();
  await waitForEditor(page);
  await expect.poll(async () => summary(await currentCharacter(page))).toEqual(expected(3));

  // This development import has unfinished chargen budgets. Accept the existing
  // warning; this test verifies persistence and prices, not chargen legality.
  page.once("dialog", (dialog) => void dialog.accept());
  await page.getByRole("button", { name: "作成完了（キャリア）" }).click();
  await expect(page.getByRole("button", { name: "キャリア中" })).toBeVisible();
  await expect.poll(async () => (await currentCharacter(page)).career).toBe(true);
  const baseline = (await currentCharacter(page)).career_baseline;
  expect(baseline?.attributes?.MAG).toBe(3);
  expect(baseline?.attributes?.STR).toBe(3);
  expect((await currentCharacter(page)).derived.career_advancement_karma).toBe(0);

  await page.getByRole("spinbutton", { name: "カルマ" }).fill("60");
  await page.getByRole("button", { name: "報酬を追加" }).click();
  await expect.poll(async () => (await currentCharacter(page)).derived.karma_earned).toBe(60);

  async function expectCareer(magic: number, strength: number, cost: number) {
    await expect
      .poll(async () => {
        const ch = await currentCharacter(page);
        return {
          career: ch.career,
          baseline: ch.career_baseline,
          advancement: ch.derived.career_advancement_karma,
          earned: ch.derived.karma_earned,
          grants: summary(ch),
        };
      })
      .toMatchObject({
        career: true,
        baseline,
        advancement: cost,
        earned: 60,
        grants: {
          metatype: "Centaur",
          magic,
          strength,
          powers: ["Search", "Natural Weapon"],
          qualityCount: 4,
          purchasedQualities: [],
          purchasedWeapons: [],
          kick: [{ damage: `${strength + 2}P`, ap: "+1", reach: "1" }],
        },
      });
  }

  // Reload before growth: do not let an in-memory baseline hide a storage bug.
  await page.reload();
  await waitForEditor(page);
  await expectCareer(3, 3, 0);
  await page.getByRole("button", { name: "能力値", exact: true }).click();
  await expect(page.getByRole("slider")).toHaveCount(10);
  // ATTRS order ends with EDG, MAG; Mundane Centaur must retain its native MAG.
  await page.getByRole("slider").nth(9).focus();
  await page.keyboard.press("ArrowRight");
  await expectCareer(4, 3, 20);
  await page.getByRole("slider").nth(3).focus();
  await page.keyboard.press("ArrowRight");
  await expectCareer(4, 4, 40);
  await page.getByRole("button", { name: /元に戻す/ }).click();
  await expectCareer(4, 3, 20);
  await page.getByRole("button", { name: /やり直し/ }).click();
  await expectCareer(4, 4, 40);

  await page.getByRole("button", { name: "成長／買い物の内訳" }).click();
  const spend = page.locator(".career-breakdown .stat");
  // The spend panel also retains the 25K heritage cost from creation. It is
  // distinct from the 40K career-advancement total checked above.
  await expect(spend).toHaveCount(3);
  await expect(spend.filter({ hasText: "MAG" }).locator("b")).toHaveText("20K");
  await expect(spend.filter({ hasText: "STR" }).locator("b")).toHaveText("20K");
  await expect(spend.filter({ hasText: "メタ" }).locator("b")).toHaveText("25K");

  const sourceId = (await currentCharacter(page)).id;
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: "JSON保存", exact: true }).click(),
  ]);
  const path = test.info().outputPath("centaur-career.json");
  await download.saveAs(path);
  const saved = JSON.parse(readFileSync(path, "utf8")) as Character;
  expect(saved.career_baseline).toEqual(baseline);
  expect(saved.derived.career_advancement_karma).toBe(40);
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)").setInputFiles(path);
  await expect.poll(async () => (await currentCharacter(page)).id).not.toBe(sourceId);
  await expectCareer(4, 4, 40);
  await page.reload();
  await waitForEditor(page);
  await expectCareer(4, 4, 40);
  await expect(page.getByRole("button", { name: "キャリア中" })).toBeVisible();
});
