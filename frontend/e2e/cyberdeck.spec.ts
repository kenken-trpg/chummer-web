import { expect, test } from "@playwright/test";
import { freshCharacter, storedCharacters, waitForEditor } from "./helpers";

/** Both the engine and IndexedDB participate: purchase -> run -> save -> reload. */
test("deck programs and parts consumption survive real browser saves", async ({
  page,
  request,
}) => {
  const state = await freshCharacter(request, "Cyberdeck regression");
  state.cyberdecks = [{ id: "deck", gear_id: "b6d1476d-a08c-43fc-be0e-68ca9330a43e", rating: 1 }];
  state.gear = [
    { id: "parts", gear_id: "ec53ae4e-086f-4817-8cc2-ec574aa7cd51", qty: 1, rating: 1 },
  ];
  await page.goto("/");
  await waitForEditor(page);
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)").setInputFiles({
    name: "cyberdeck.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(state)),
  });
  await expect(page.getByRole("textbox", { name: "キャラクター名" })).toHaveValue(
    "Cyberdeck regression",
  );
  await page.getByRole("button", { name: "ギア", exact: true }).click();
  await page.getByRole("button", { name: "サイバーデッキ", exact: true }).click();
  const deck = page
    .locator(".cyber-item")
    .filter({ has: page.locator(".matrix-array") })
    .first();
  const programSelect = deck.getByRole("combobox", { name: /プログラムを追加/ });
  for (const id of [
    "a1e4b783-0751-43eb-b5bd-ee00f84b7bb3",
    "b3c0a6bd-e086-4971-be77-dc9a9cb2e174",
  ]) {
    await programSelect.selectOption(id);
    await deck.getByRole("button", { name: /装着$/ }).first().click();
    await expect
      .poll(async () => {
        const saved = (await storedCharacters(page)).find(
          (s) => s.name === "Cyberdeck regression",
        ) as unknown as { programs?: { gear_id: string }[] };
        return saved?.programs?.some((p) => p.gear_id === id);
      })
      .toBe(true);
  }
  await expect(deck).toContainText("搭載 2本 / 作動中 0/1");
  const running = deck.getByRole("checkbox", { name: /作動中/ });
  await running.nth(0).click();
  await expect(running.nth(0)).toBeChecked();
  await expect(deck).toContainText("作動中 1/1");
  await running.nth(1).click();
  await expect(running.nth(1)).toBeChecked();
  await expect(deck).toContainText("作動中 2/1");
  await expect(page.getByText(/プログラム同時実行数が上限超過/)).toBeVisible();
  await running.nth(0).click();
  await expect(running.nth(0)).not.toBeChecked();
  await expect(deck).toContainText("作動中 1/1");
  const modSelect = deck.getByRole("combobox", { name: /改造を追加/ });
  await modSelect.selectOption("821d8a12-b883-49de-9ccf-f39c42fba860");
  await deck.getByRole("button", { name: /装着$/ }).last().click();
  await expect(deck.getByText("準備中（効果なし）", { exact: true })).toBeVisible();
  const allocation = deck.getByRole("spinbutton", {
    name: /Modify Matrix Attribute.*Electronic Parts|マトリックス.*電子部品/,
  });
  // English catalog names may be untranslated; select the material allocation
  // by its stable input range if the translation differs between data sets.
  const input = (await allocation.count())
    ? allocation
    : deck.locator('input[type="number"][step="0.25"][max="5"]');
  await input.fill("4");
  await deck.getByRole("button", { name: "施工済みにする", exact: true }).click();
  await expect(deck.getByText("施工済み", { exact: true })).toBeVisible();
  await expect
    .poll(async () => {
      const saved = (await storedCharacters(page)).find(
        (s) => s.name === "Cyberdeck regression",
      ) as unknown as {
        derived: { nuyen_spent: number; gear: { id: string; parts_remaining_units?: number }[] };
      };
      return {
        left: saved?.derived.gear.find((g) => g.id === "parts")?.parts_remaining_units,
        spent: saved?.derived.nuyen_spent,
      };
    })
    .toEqual({ left: 4, spent: 50830 });
  await page.reload();
  await waitForEditor(page);
  await page.getByRole("button", { name: "ギア", exact: true }).click();
  await page.getByRole("button", { name: "サイバーデッキ", exact: true }).click();
  await expect(page.getByRole("checkbox", { name: /作動中/ }).nth(0)).not.toBeChecked();
  await expect(page.getByRole("checkbox", { name: /作動中/ }).nth(1)).toBeChecked();
  await expect(page.getByText("施工済み", { exact: true })).toBeVisible();
});

test("one spare module can be fitted and detached without changing ownership or spending", async ({
  page,
  request,
}) => {
  const state = await freshCharacter(request, "Module regression");
  state.cyberdecks = [{ id: "deck", gear_id: "b6d1476d-a08c-43fc-be0e-68ca9330a43e", rating: 1 }];
  state.gear = [
    {
      id: "spare",
      gear_id: "8706c98d-b53b-4a29-b21b-a921030ae801",
      rating: 1,
      qty: 2,
      equipped: false,
    },
  ];
  await page.goto("/");
  await waitForEditor(page);
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)").setInputFiles({
    name: "module.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(state)),
  });
  await expect(page.getByRole("textbox", { name: "キャラクター名" })).toHaveValue(
    "Module regression",
  );
  await page.getByRole("button", { name: "ギア", exact: true }).click();
  await page.getByRole("button", { name: "サイバーデッキ", exact: true }).click();
  const deck = page
    .locator(".cyber-item")
    .filter({ has: page.locator(".matrix-array") })
    .first();
  const read = async () =>
    (await storedCharacters(page)).find((s) => s.name === "Module regression") as unknown as {
      gear: { id: string; qty: number; parent_id?: string | null }[];
      derived: { nuyen_spent: number; matrix_initiative: { cold_dice: number } };
    };
  const spent = (await read()).derived.nuyen_spent;
  await deck
    .getByRole("combobox", { name: "購入済みの予備モジュールを搭載" })
    .selectOption("spare");
  await expect(deck).toContainText("モジュール 1/1");
  const enabled = deck.getByRole("checkbox", { name: /モジュール効果を有効化/ });
  await expect(enabled).not.toBeChecked();
  await expect
    .poll(async () => (await read()).gear.filter((g) => g.parent_id === "deck").map((g) => g.qty))
    .toEqual([1]);
  expect((await read()).derived.matrix_initiative.cold_dice).toBe(3);
  await enabled.click();
  await expect.poll(async () => (await read()).derived.matrix_initiative.cold_dice).toBe(4);
  await deck.getByRole("button", { name: /：取り外す$/ }).click();
  await expect(deck).toContainText("モジュール 0/1");
  await expect.poll(async () => (await read()).derived.matrix_initiative.cold_dice).toBe(3);
  const saved = await read();
  expect(saved.derived.nuyen_spent).toBe(spent);
  expect(saved.gear.reduce((n, g) => n + g.qty, 0)).toBe(2);
  expect(saved.gear.every((g) => !g.parent_id)).toBe(true);
});
