import { readFileSync } from "node:fs";
import { expect, test } from "@playwright/test";
import { chummerFixture, storedCharacters, waitForEditor } from "./helpers";

test("a multi-MB save written by Chummer imports, edits, persists and exports", async ({
  page,
}) => {
  const file = await chummerFixture();

  await page.goto("/");
  await waitForEditor(page);
  await page.getByLabel("読込 (JSON/.chum5)").setInputFiles(file);

  const name = page.getByRole("textbox", { name: "キャラクター名" });
  await expect(name).toHaveValue("Ghile Mear");

  // the mugshot made it through the import and into state
  await page.getByRole("button", { name: "シート", exact: true }).click();
  // the rendered sheet, not the thumbnail in the editor above it
  // this save carries three mugshots, and every one of them is shown
  const portraits = page.getByRole("article").getByRole("img", { name: "ポートレート" });
  await expect(portraits).toHaveCount(3);
  const portrait = portraits.first();
  await expect(portrait).toBeVisible();
  expect(await portrait.evaluate((img: HTMLImageElement) => img.naturalWidth)).toBeGreaterThan(0);

  // an edit leaves the multi-MB portrait behind: it once rode along on every
  // patch, and a reload during that round trip lost the edit
  const sizes: number[] = [];
  page.on("request", (req) => {
    if (req.url().endsWith("/api/characters/patch")) sizes.push(req.postDataBuffer()?.length ?? 0);
  });
  await name.fill("Ghile Edited");
  await name.blur();
  // the editor does not announce when the save has committed; wait for that
  // rather than race it (a real user gets a leave-page prompt instead)
  await expect
    .poll(async () => (await storedCharacters(page)).map((c) => c.name), { timeout: 15_000 })
    .toContain("Ghile Edited");
  expect(sizes.length).toBeGreaterThan(0);
  expect(Math.max(...sizes)).toBeLessThan(200_000);
  await page.reload();
  await waitForEditor(page);
  await expect(name).toHaveValue("Ghile Edited");

  // and the export carries the portrait back out as a mugshot
  const download = await Promise.all([
    page.waitForEvent("download"),
    page.getByRole("button", { name: ".chum5書出" }).click(),
  ]).then(([d]) => d);
  const out = test.info().outputPath("export.chum5");
  await download.saveAs(out);
  const xml = readFileSync(out, "utf8");
  // the exporter writes the character name as Chummer's <alias> (the street name)
  expect(xml).toContain("<alias>Ghile Edited</alias>");
  expect(xml).toMatch(/<mugshot>[A-Za-z0-9+/=\s]{1000,}<\/mugshot>/);
});
