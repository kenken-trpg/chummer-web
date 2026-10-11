import { readFileSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";
import type { Character } from "../lib/types";
import { encodeFragment, waitForEditor } from "./helpers";

/** Imported character exercises persistence independently of the creation flow. */
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

for (const method of ["Priority", "SumToTen", "Karma"]) {
  test(`a new ${method} character can select Centaur and reload its innate grants`, async ({
    page,
  }) => {
    await page.goto("/");
    await waitForEditor(page);
    if (method !== "Priority") {
      await page
        .getByRole("button", { name: method === "SumToTen" ? "Sum to Ten" : "Karma", exact: true })
        .click();
      await expect.poll(async () => (await currentCharacter(page)).build_method).toBe(method);
    }
    await page.getByRole("button", { name: "ルールブックを選ぶ", exact: true }).click();
    const rf = page.getByRole("checkbox", { name: /\(RF\)/ });
    if (!(await rf.isChecked())) await rf.click();
    await expect
      .poll(async () => (await currentCharacter(page)).settings?.books?.includes("RF"))
      .toBe(true);
    await page.getByRole("button", { name: "メタタイプ", exact: true }).click();
    const candidate = page.getByRole("button", { name: /Centaur/ });
    await expect(candidate).toContainText(method === "Karma" ? "60カルマ" : "25カルマ");
    await candidate.click();
    await expect.poll(async () => (await currentCharacter(page)).metatype).toBe("Centaur");
    const state = await currentCharacter(page);
    const created = summary(state);
    expect(state.derived.karma_chargen?.metatype).toBe(method === "Karma" ? 60 : 0);
    expect(state.derived.karma.spent).toBe(method === "Karma" ? 60 : 25);
    expect(created.powers).toEqual(["Search", "Natural Weapon"]);
    expect(created.qualityCount).toBe(4);
    expect(created.kick).toHaveLength(1);
    expect(created.magic).toBe(1);
    await page.reload();
    await waitForEditor(page);
    await expect.poll(async () => summary(await currentCharacter(page))).toEqual(created);
  });
}

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

test("XLSX warns about Centaur's lost grants and does not import its kick as a purchase", async ({
  page,
}) => {
  await page.goto(`/share#c=${encodeFragment({ v: 1, s: payload })}`);
  await page.getByRole("button", { name: "自分のロースターに取り込む" }).click();
  await waitForEditor(page);
  await expect.poll(async () => summary(await currentCharacter(page))).toEqual(expected(3));
  const sourceId = (await currentCharacter(page)).id;
  const downloads: string[] = [];
  page.on("download", (file) => downloads.push(file.suggestedFilename()));

  await page.getByRole("button", { name: ".xlsx書出" }).click();
  const review = page.getByRole("alertdialog");
  await expect(review.locator("li").filter({ hasText: "生得付与" })).toHaveCount(7);
  await expect(review).toContainText("Centaur");
  await expect(review).toContainText("Human");
  await expect(review).toContainText("Kick: DV ({STR} + 2)P, AP +1, +1 Reach");
  await expect(review).toContainText("SR5 p.399");
  await review.getByRole("button", { name: "やめる", exact: true }).click();
  await expect(review).not.toBeVisible();
  expect(downloads).toEqual([]);
  await expect.poll(async () => summary(await currentCharacter(page))).toEqual(expected(3));

  await page.getByRole("button", { name: ".xlsx書出" }).click();
  await expect(review.locator("li").filter({ hasText: "生得付与" })).toHaveCount(7);
  const [download] = await Promise.all([
    page.waitForEvent("download"),
    review.getByRole("button", { name: "このまま書き出す" }).click(),
  ]);
  const path = test.info().outputPath("centaur-lossy.xlsx");
  await download.saveAs(path);
  // Exporting itself must leave the source Centaur untouched.
  await expect.poll(async () => summary(await currentCharacter(page))).toEqual(expected(3));
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)").setInputFiles(path);
  await expect.poll(async () => (await currentCharacter(page)).id).not.toBe(sourceId);
  await expect.poll(async () => (await currentCharacter(page)).metatype).toBe("Human");
  const imported = await currentCharacter(page);
  expect(imported.quality_ids).toEqual([]);
  expect(imported.weapons).toEqual([]);
  expect(imported.derived.weapons).toEqual([]);
  expect(imported.derived.metatype_info.powers ?? []).toEqual([]);
});

test("Centaur career chum5 reimport preserves balance and prices only subsequent growth", async ({
  page,
}) => {
  const career = {
    ...payload,
    career: true,
    attributes: { ...payload.attributes, MAG: 4, STR: 4 },
    career_baseline: {
      attributes: payload.attributes,
      quality_ids: [],
      item_ids: [],
      mystic_pp: 0,
    },
    reward_log: [{ label: "Run", karma: 100, nuyen: 0 }],
  };
  await page.goto(`/share#c=${encodeFragment({ v: 1, s: career })}`);
  await page.getByRole("button", { name: "自分のロースターに取り込む" }).click();
  await waitForEditor(page);
  await expect
    .poll(async () => (await currentCharacter(page)).derived.career_advancement_karma)
    .toBe(40);
  const balance = (await currentCharacter(page)).derived.karma.remaining;

  async function expectImported(magic: number, adjustment: number, remaining: number) {
    await expect
      .poll(async () => {
        const ch = await currentCharacter(page);
        return {
          grants: summary(ch),
          career: ch.career,
          baselineMAG: ch.career_baseline?.attributes?.MAG,
          baselineSTR: ch.career_baseline?.attributes?.STR,
          adjustment: ch.karma_adjust,
          advancement: ch.derived.career_advancement_karma,
          earned: ch.derived.karma_earned,
          remaining: ch.derived.karma.remaining,
        };
      })
      .toEqual({
        grants: { ...expected(4), magic, specialUsed: magic - 1 },
        career: true,
        baselineMAG: magic,
        baselineSTR: 4,
        adjustment,
        advancement: 0,
        earned: 100,
        remaining,
      });
  }

  for (const [magic, growth, adjustment] of [
    [4, 40, -40],
    [5, 25, -65],
  ]) {
    const sourceId = (await currentCharacter(page)).id;
    await page.getByRole("button", { name: ".chum5書出" }).click();
    const review = page.getByRole("alertdialog");
    await expect(review).toContainText(`成長費用${growth}Kは残高調整へ移り`);
    const [download] = await Promise.all([
      page.waitForEvent("download"),
      review.getByRole("button", { name: "このまま書き出す" }).click(),
    ]);
    const path = test.info().outputPath(`centaur-career-${magic}.chum5`);
    await download.saveAs(path);
    await page.getByLabel("読込 (JSON/.chum5/.xlsx)").setInputFiles(path);
    await expect.poll(async () => (await currentCharacter(page)).id).not.toBe(sourceId);
    await expectImported(magic, adjustment, balance - (magic === 5 ? 25 : 0));
    await page.reload();
    await waitForEditor(page);
    await expectImported(magic, adjustment, balance - (magic === 5 ? 25 : 0));
    if (magic === 4) {
      await page.getByRole("button", { name: "能力値", exact: true }).click();
      await page.getByRole("slider", { name: /^MAG / }).focus();
      await page.keyboard.press("ArrowRight");
      await expect
        .poll(async () => (await currentCharacter(page)).derived.career_advancement_karma)
        .toBe(25);
      await expect
        .poll(async () => (await currentCharacter(page)).derived.karma.remaining)
        .toBe(balance - 25);
    }
  }
});

test("disabling RF retains Centaur, warns about its source and survives reload and undo", async ({
  page,
}) => {
  await page.goto(`/share#c=${encodeFragment({ v: 1, s: payload })}`);
  await page.getByRole("button", { name: "自分のロースターに取り込む" }).click();
  await waitForEditor(page);
  await expect.poll(async () => summary(await currentCharacter(page))).toEqual(expected(3));
  await page.getByRole("button", { name: "メタタイプ", exact: true }).click();
  await expect(page.getByRole("button", { name: /Centaur/ })).toHaveCount(1);
  await expect(page.getByRole("status").filter({ hasText: "現在の種族" })).toHaveCount(0);

  async function expectRF(enabled: boolean) {
    await expect.poll(async () => summary(await currentCharacter(page))).toEqual(expected(3));
    await expect
      .poll(async () => (await currentCharacter(page)).settings?.books?.includes("RF"))
      .toBe(enabled);
    await expect
      .poll(async () =>
        (await currentCharacter(page)).derived.warnings?.some(
          (row) => row.key === "engine.settings.outOfBooks",
        ),
      )
      .toBe(!enabled);
    const warning = page.locator("aside.side").getByText(/使用ルールブック外の項目/);
    if (enabled) {
      await expect(warning).toHaveCount(0);
    } else {
      await expect(warning).toContainText("RF");
      await expect(warning).toContainText("Centaur");
    }
  }

  await page
    .getByRole("navigation", { name: "セクション" })
    .getByRole("button", { name: "優先度", exact: true })
    .click();
  await page.getByRole("button", { name: "ルールブックを選ぶ", exact: true }).click();
  // The controlled checkbox changes after the engine patch resolves.
  await page.getByRole("checkbox", { name: /\(RF\)/ }).click();
  await expectRF(false);
  await expect(page.getByRole("checkbox", { name: /\(RF\)/ })).not.toBeChecked();
  await page.getByRole("button", { name: "メタタイプ", exact: true }).click();
  await expect(page.getByRole("button", { name: /Centaur/ })).toHaveCount(0);
  await expect(page.getByRole("status").filter({ hasText: "現在の種族" })).toContainText("RF");
  await page.reload();
  await waitForEditor(page);
  await expectRF(false);
  // History is session-local: make a new edit after reload, then undo/redo it.
  await page
    .getByRole("navigation", { name: "セクション" })
    .getByRole("button", { name: "優先度", exact: true })
    .click();
  await page.getByRole("button", { name: "ルールブックを選ぶ", exact: true }).click();
  await page.getByRole("checkbox", { name: /\(RF\)/ }).click();
  await expectRF(true);
  await expect(page.getByRole("checkbox", { name: /\(RF\)/ })).toBeChecked();
  await page.getByRole("button", { name: /元に戻す/ }).click();
  await expectRF(false);
  await page.getByRole("button", { name: /やり直し/ }).click();
  await expectRF(true);
  await page.getByRole("button", { name: "メタタイプ", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "現在の種族" })).toHaveCount(0);
  await expect(page.getByRole("button", { name: /Centaur/ })).toHaveCount(1);
});
