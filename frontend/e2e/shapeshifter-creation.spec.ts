import { expect, test, type Page } from "@playwright/test";
import type { Character } from "../lib/types";
import { waitForEditor } from "./helpers";

/** A shapeshifter from the creation screen: the animal is the metatype, the
 *  metahuman form is a metavariant picked under it, and the form sets the
 *  price (Heritage C: Human 5 / Elf 10 karma; Karma build: 100 / 105). */
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
    magic: ch.derived.totals.MAG,
    agility: ch.derived.metatype_info.attributes.AGI,
    powers: ch.derived.metatype_info.powers?.map((row) => row.name),
    innate: ch.derived.qualities.filter((q) => q.origin === "Metatype").map((q) => q.name),
    bite: ch.derived.weapons?.filter((row) => row.natural).map((row) => row.name),
    spent: ch.derived.karma.spent,
  };
}

for (const method of ["Priority", "SumToTen", "Karma"]) {
  test(`a new ${method} character can become a shapeshifter and pick its form`, async ({
    page,
  }) => {
    const karma = method === "Karma" ? { Human: 100, Elf: 105 } : { Human: 5, Elf: 10 };
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
    const candidate = page.getByRole("button", { name: /Shapeshifter: Vulpine/ });
    await expect(candidate).toContainText(method === "Karma" ? "100カルマ" : "5カルマ");
    await candidate.click();
    await expect
      .poll(async () => (await currentCharacter(page)).metatype)
      .toBe("Shapeshifter: Vulpine");

    const human = summary(await currentCharacter(page));
    expect(human.metavariant).toBe("Human");
    expect(human.magic).toBe(1);
    expect(human.agility).toMatchObject({ min: 2, max: 7 });
    expect(human.powers).toEqual(["Shift (Metahuman Form)"]);
    expect(human.innate).toHaveLength(5);
    expect(human.bite).toEqual(["Bite (Vulpine Form)"]);
    expect(human.spent).toBe(karma.Human);

    const form = page.getByRole("combobox", { name: "人間形態" });
    await expect(form).toHaveValue("Human");
    await form.selectOption("Elf");
    await expect.poll(async () => (await currentCharacter(page)).metavariant).toBe("Elf");
    const elf = summary(await currentCharacter(page));
    expect(elf.spent).toBe(karma.Elf);
    // still the fox's attributes: the form does not set them
    expect(elf.agility).toMatchObject({ min: 2, max: 7 });

    await page.reload();
    await waitForEditor(page);
    await expect.poll(async () => summary(await currentCharacter(page))).toEqual(elf);
    await page.getByRole("button", { name: "メタタイプ", exact: true }).click();
    await expect(page.getByRole("combobox", { name: "人間形態" })).toHaveValue("Elf");
  });
}
