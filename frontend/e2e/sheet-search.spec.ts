import { expect, test } from "@playwright/test";
import { waitForEditor } from "./helpers";

test("search finds nested equipment across tabs and opens the exact row and character notes", async ({
  page,
}) => {
  await page.goto("/");
  await waitForEditor(page);
  const catalogResponse = await page.request.get("/api/catalog");
  expect(catalogResponse.ok()).toBe(true);
  const catalog = await catalogResponse.json();
  const backpack = catalog.gear.find((row: { name: string }) => row.name === "Backpack (Good)");
  const medkit = catalog.gear.find((row: { name: string }) => row.name === "Medkit");
  expect(backpack).toBeTruthy();
  expect(medkit).toBeTruthy();
  const response = await page.request.post("/api/characters/new", {
    data: { name: "Search character" },
  });
  expect(response.ok()).toBe(true);
  const character = await response.json();
  character.background = "Retired courier from Seattle";
  character.gear_locations = [{ id: "clinic", name: "Hidden clinic" }];
  character.gear = [
    {
      id: "bag-install",
      gear_id: backpack.id,
      nickname: "Medical bag",
      location: "clinic",
      qty: 1,
    },
    {
      id: "kit-install",
      gear_id: medkit.id,
      rating: 3,
      parent_id: "bag-install",
      nickname: "Primary kit",
      notes: "卓で共有する医療用品",
      qty: 1,
    },
    { id: "spare-install", gear_id: medkit.id, rating: 1, nickname: "Spare kit", qty: 1 },
  ];
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)", { exact: true }).setInputFiles({
    name: "search-character.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(character)),
  });
  await expect(page.getByRole("textbox", { name: "キャラクター名" })).toHaveValue(
    "Search character",
  );
  const search = page.getByRole("searchbox", { name: "シート内容を検索" });
  const results = page.getByRole("region", { name: "シート内容を検索" });
  await search.fill("Hidden clinic 共有");
  await expect(results.getByRole("status")).toHaveText("1件見つかりました。");
  await expect(results).toContainText("Medical bag");
  await results.getByRole("button", { name: /^Primary kit/ }).click();
  const item = page.locator('[data-sheet-search="gear/kit-install"]').first();
  await expect(item).toHaveAttribute("data-search-highlight", "true");
  await expect(item).toBeFocused();
  await expect(item.locator("details.row-notes")).toHaveAttribute("open", "");
  await expect(page.getByRole("button", { name: "一般装備", exact: true })).toHaveClass(/active/);

  // A second result in the same tab must move to that copy rather than the first same-named item.
  await search.fill("Spare kit");
  await results.getByRole("button", { name: /^Spare kit/ }).click();
  await expect(page.locator('[data-sheet-search="gear/spare-install"]').first()).toHaveAttribute(
    "data-search-highlight",
    "true",
  );

  await search.fill("Retired courier");
  await results.getByRole("button", { name: "背景", exact: true }).click();
  const background = page.locator('[data-sheet-search="description/background"]');
  await expect(background).toHaveAttribute("data-search-highlight", "true");
  await expect(background.locator("textarea")).toHaveValue("Retired courier from Seattle");
});
