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
  // The stage name is Run Faster data, so it reads in English in the Japanese UI.
  const picker = page.getByRole("group", { name: "Real Life: Choose a module" });
  await page.getByRole("searchbox", { name: /Search modules/ }).fill("bounty hunter");
  await expect(picker.getByRole("radio")).toHaveCount(1);
  const candidate = picker.getByRole("radio", { name: /Bounty Hunter/ });
  await candidate.focus();
  await candidate.press("Space");
  await expect(candidate).toBeChecked();
  await expect(page.getByRole("button", { name: "Bounty Hunter: Remove this module" })).toHaveCount(
    0,
  );
  await expect(picker.locator(".life-preview")).toContainText("100 Karma");
  await picker.getByRole("button", { name: "Add this module" }).click();
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
  await expect(
    page.getByRole("button", { name: "Bounty Hunter: Remove this module" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Bounty Hunter: Remove this module" }).click();
  await expect.poll(async () => (await saved())?.life_modules).toEqual([]);
  await expect.poll(async () => (await saved())?.derived?.totals?.BOD).toBe(1);
  expect((await saved()).derived.karma.spent).toBe(0);
});

test("life module layout keeps choices and actions inside desktop and mobile viewports", async ({
  page,
  request,
}, testInfo) => {
  const seed = {
    ...(await freshCharacter(request, "Life module layout")),
    build_method: "LifeModule",
    settings: { books: ["SR5", "RF", "TCG"] },
    life_modules: [
      "4fe5e4fd-0275-48bd-9fec-678b86c5f024",
      "47bf63cf-9a2a-4008-b455-c8ab68add581",
      "47bf63cf-9a2a-4008-b455-c8ab68add581",
    ],
  };
  await page.goto("/");
  await waitForEditor(page);
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)").setInputFiles({
    name: "layout.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(seed)),
  });
  const panel = page.locator(".life-modules");
  await expect(panel.getByRole("heading", { name: "SINless" })).toBeVisible();
  await expect(panel.getByRole("heading", { name: "Bounty Hunter" })).toHaveCount(2);
  await expect(panel.locator(".life-status")).toHaveCount(2);
  const method = await page.getByRole("button", { name: "Life Module", exact: true }).boundingBox();
  const heading = await panel.getByRole("heading", { name: "Life Module" }).boundingBox();
  expect(method!.y).toBeLessThan(heading!.y);

  for (const width of [1440, 390, 320]) {
    await page.setViewportSize({ width, height: 900 });
    const fields = panel.locator(".life-choices").first().locator("select, input");
    await expect(fields).toHaveCount(2);
    const first = await fields.nth(0).boundingBox();
    const second = await fields.nth(1).boundingBox();
    if (width <= 390) expect(second!.y).toBeGreaterThan(first!.y);
    else expect(Math.abs(second!.y - first!.y)).toBeLessThan(2);

    const candidates = panel.getByRole("group", { name: "Real Life: Choose a module" });
    await candidates.getByRole("radio", { name: /Trog Professional/ }).check();
    await expect(candidates.locator(".life-preview")).toContainText("Requirements are not met");
    await expect(candidates.getByRole("button", { name: "Add this module" })).toBeDisabled();
    const summary = panel.locator("summary").first();
    await summary.click();
    await expect(panel.locator("details").first()).toHaveAttribute("open", "");
    for (const control of await panel.locator("input, select, button").all()) {
      const box = await control.boundingBox();
      expect(box!.x).toBeGreaterThanOrEqual(0);
      expect(box!.x + box!.width).toBeLessThanOrEqual(width);
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(
      width,
    );
    await panel.screenshot({ path: testInfo.outputPath(`life-modules-${width}.png`) });
    await candidates.screenshot({
      path: testInfo.outputPath(`life-candidates-${width}.png`),
      style: ".tabs { visibility: hidden; }",
    });
    await summary.click();
  }
});

test("skill overflow survives reload, career growth and undo", async ({ page, request }) => {
  const seed = {
    ...(await freshCharacter(request, "RF skill overflow")),
    build_method: "LifeModule",
    settings: { books: ["SR5", "RF"] },
    life_modules: [
      "b332fa10-e0f5-43aa-bb38-52cdb0060da1",
      "06b4cc0f-3008-4209-ac32-04614a3dc354",
      "737d188a-85b5-47d8-91f2-39863983b464",
      "864c49cf-b44d-4c12-b70a-22228c282f2c",
      "3fb24f67-9d15-49d8-a598-5abbea335e8b",
    ],
    life_module_choices: { "0:4": "Spanish", "1:5": "Seattle Streets" },
  };
  await page.goto("/");
  await waitForEditor(page);
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)").setInputFiles({
    name: "overflow.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(seed)),
  });
  const saved = async () =>
    (await storedCharacters(page)).find((row) => row.name === "RF skill overflow") as unknown as {
      career: boolean;
      life_module_transfers: { ranks: number }[];
      life_module_skill_advancements: unknown[];
      derived: {
        skill_totals: Record<string, number>;
        karma: { spent: number };
        life_module_skills: {
          pools: { source_skill_id: string; candidates: { name: string; skill_id: string }[] }[];
        };
      };
    };
  const pool = page.locator(".life-overflow");
  await expect(pool).toBeVisible();
  const source = (await saved()).derived.life_module_skills.pools[0];
  const navigation = source.candidates.find((c) => c.name === "Navigation")!;
  await pool.getByLabel("移し替え先の技能").selectOption(navigation.skill_id);
  await pool.getByLabel("移すレベル数").fill("2");
  await pool.getByRole("button", { name: "この配分を追加" }).click();
  await expect.poll(async () => (await saved())?.derived.skill_totals.Navigation).toBe(2);
  expect((await saved()).derived.skill_totals.Perception).toBe(7);
  expect((await saved()).derived.karma.spent).toBe(245);
  await page.reload();
  await waitForEditor(page);
  await expect(page.locator(".life-overflow")).toContainText("+2");
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "作成完了（キャリア）", exact: true }).click();
  await expect.poll(async () => (await saved())?.career).toBe(true);
  const spent = (await saved()).derived.karma.spent;
  await page.getByRole("button", { name: "技能", exact: true }).click();
  const growth = page.getByRole("group", { name: "Career skill advancement" });
  await growth.getByLabel("Skill or group to advance").selectOption(source.source_skill_id);
  await growth.getByRole("button", { name: "Buy advancement" }).click();
  await expect.poll(async () => (await saved())?.derived.skill_totals.Perception).toBe(8);
  expect((await saved()).derived.skill_totals.Navigation).toBe(2);
  expect((await saved()).derived.karma.spent).toBe(spent + 16);
  await page.reload();
  await waitForEditor(page);
  await page.getByRole("button", { name: "技能", exact: true }).click();
  await page.getByRole("button", { name: "最後の技能成長を取り消す" }).click();
  await expect.poll(async () => (await saved())?.derived.skill_totals.Perception).toBe(7);
  expect((await saved()).derived.karma.spent).toBe(spent);
  expect((await saved()).life_module_transfers[0].ranks).toBe(2);
});
