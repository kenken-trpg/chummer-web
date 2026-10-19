import { expect, test } from "@playwright/test";
import { openExportMenu, waitForEditor } from "./helpers";

/**
 * The three things this app hands over by copying rather than by downloading:
 * a share link, a Cocofolia piece and a chat palette.
 *
 * The builders behind them are unit-tested, and the toolbar's wiring is too —
 * with `navigator.clipboard` mocked in both. What neither can answer is
 * whether anything reached the clipboard: that depends on the page being a
 * secure context, on the permission, and on `copyText`'s own fallback
 * (`lib/character/useCharacterExport.ts` drops to `execCommand("copy")` when
 * the API refuses). A browser is the only place that question exists.
 */
test("the share link, the Cocofolia piece and the palette reach the clipboard", async ({
  page,
  context,
}) => {
  await context.grantPermissions(["clipboard-read", "clipboard-write"], {
    origin: "http://127.0.0.1:3100",
  });
  await page.goto("/");
  await waitForEditor(page);

  const name = page.getByRole("textbox", { name: "キャラクター名" });
  await name.fill("Clipboard Runner");
  await name.blur();
  const read = () => page.evaluate(() => navigator.clipboard.readText());

  // 1. the share link: the character travels in the fragment, so the copied
  // text has to carry one — an empty `#c=` would look fine on the button
  await page.getByRole("button", { name: "共有リンク" }).click();
  await expect(page.getByRole("button", { name: "コピー ✓" })).toBeVisible();
  const link = await read();
  expect(link).toContain("/share#c=");
  expect(link.split("#c=")[1].length).toBeGreaterThan(20);

  // 2. the Cocofolia piece: pasted into Cocofolia as JSON, so it has to parse
  await openExportMenu(page);
  await page.getByRole("button", { name: "ココフォリア" }).click();
  const piece = JSON.parse(await read()) as {
    kind: string;
    data: { name: string; commands: string };
  };
  expect(piece.kind).toBe("character");
  expect(piece.data.name).toBe("Clipboard Runner");
  // the piece carries the palette with it
  expect(piece.data.commands).toContain("B6");

  // 3. the palette on its own: BCDice ShadowRun5 commands, one per line
  await openExportMenu(page);
  await page.getByRole("button", { name: "チャットパレット" }).click();
  const palette = await read();
  expect(palette.split("\n").length).toBeGreaterThan(3);
  expect(palette).toMatch(/^\dD6\+\d+ /m); // the initiative line
  expect(palette).toContain(piece.data.commands);
});
