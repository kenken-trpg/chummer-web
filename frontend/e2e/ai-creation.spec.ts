import { expect, test, type Page } from "@playwright/test";
import type { Character } from "../lib/types";
import { waitForEditor } from "./helpers";

/** An A.I. from the creation screen (DT p.135): offered once DT is on, its
 *  talent picked for it, its Depth started at that talent's, and half the
 *  Attributes priority's points to spend. The defaults put it at Heritage C,
 *  Attributes A (24, so 12) and Talent E (Depth 1). */
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
  return {
    metatype: ch.metatype,
    metavariant: ch.metavariant,
    talent: ch.talent,
    depth: ch.derived.totals.DEP,
    body: ch.derived.totals.BOD,
    attributePoints: ch.derived.points.attributes.max,
    innate: ch.derived.qualities.filter((q) => q.origin === "Metatype").map((q) => q.name),
    spent: ch.derived.karma.spent,
  };
}

for (const method of ["Priority", "SumToTen", "Karma"]) {
  test(`a new ${method} character can become an A.I. and pick its kind`, async ({ page }) => {
    await page.goto("/");
    await waitForEditor(page);
    if (method !== "Priority") {
      await page
        .getByRole("button", { name: method === "SumToTen" ? "Sum to Ten" : "Karma", exact: true })
        .click();
      await expect.poll(async () => (await currentCharacter(page)).build_method).toBe(method);
    }
    await page.getByRole("button", { name: "ルールブックを選ぶ", exact: true }).click();
    const dt = page.getByRole("checkbox", { name: /\(DT\)/ });
    if (!(await dt.isChecked())) await dt.click();
    await expect
      .poll(async () => (await currentCharacter(page)).settings?.books?.includes("DT"))
      .toBe(true);
    await page.getByRole("button", { name: "メタタイプ", exact: true }).click();
    const candidate = page.getByRole("button", { name: /^A\.I\./ });
    await expect(candidate).toContainText(method === "Karma" ? "180カルマ" : "特殊点 0");
    await candidate.click();
    await expect.poll(async () => (await currentCharacter(page)).metatype).toBe("A.I.");

    const bare = summary(await currentCharacter(page));
    expect(bare.metavariant).toBeNull();
    expect(bare.depth).toBe(1);
    expect(bare.body).toBe(0);
    expect(bare.innate).toEqual([
      "Codeslinger",
      "Photographic Memory",
      "Speed Reading",
      "Real World Naiveté",
    ]);
    // Attributes A is 24, of which an A.I. gets half; a Karma build has none
    if (method === "Karma") expect(bare.spent).toBe(180);
    else expect(bare.attributePoints).toBe(12);
    expect(bare.talent).toBe("A.I.");
    // the pulldown offers nothing an A.I. may not take
    const talent = page.getByRole("combobox", { name: "タレント" });
    await expect(talent).toHaveValue("A.I.");
    await expect(talent.locator("option")).toHaveCount(1);

    await page.getByRole("combobox", { name: "メタバリアント" }).selectOption("E-Ghost");
    await expect.poll(async () => (await currentCharacter(page)).metavariant).toBe("E-Ghost");
    const ghost = summary(await currentCharacter(page));
    expect(ghost.innate.filter((name) => name === "Hello World!")).toHaveLength(3);
    expect(ghost.depth).toBe(1);

    await page.getByRole("button", { name: "能力値", exact: true }).click();
    await expect(page.getByRole("slider", { name: /^DEP / })).toBeVisible();
    await expect(page.getByRole("slider", { name: /^BOD / })).toHaveCount(0);

    await page.reload();
    await waitForEditor(page);
    await expect.poll(async () => summary(await currentCharacter(page))).toEqual(ghost);
  });
}
