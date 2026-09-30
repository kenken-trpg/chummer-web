import { expect, test } from "@playwright/test";
import { storedCharacters, waitForEditor } from "./helpers";

/**
 * Career mode end to end. What nothing else reaches: the karma a raise costs is
 * computed by the Python engine against a *baseline* that was snapshotted when
 * the character left creation, and that baseline lives in the character record
 * in IndexedDB. The unit suite mocks `lib/api`, so it never sees the engine
 * price anything; pytest prices everything but never through a browser that has
 * to carry the baseline across a reload.
 *
 * A wrong price here is a player being overcharged karma, which is why it is
 * worth a browser.
 */

/** Creation errors are expected on a bare character; the switch asks first. */
async function intoCareer(page: import("@playwright/test").Page) {
  page.once("dialog", (dialog) => void dialog.accept());
  await page.getByRole("button", { name: "作成完了（キャリア）" }).click();
  await expect(page.getByRole("button", { name: "キャリア中" })).toBeVisible();
}

test("a reward is logged, a raise is priced against the chargen baseline, and both survive a reload", async ({
  page,
}) => {
  await page.goto("/");
  await waitForEditor(page);

  const name = page.getByRole("textbox", { name: "キャラクター名" });
  await name.fill("Careerist");
  await name.blur();

  await intoCareer(page);

  // The reward log is the career sidebar's own panel: it is what gives the
  // character karma to spend, so it comes before the raise.
  await page.getByRole("spinbutton", { name: "カルマ" }).fill("20");
  await page.getByRole("button", { name: "報酬を追加" }).click();
  await expect(page.getByText("20K /").first()).toBeVisible();

  // Raise BOD by one. In creation this is priority points; in career it is
  // karma, priced by the engine at new rating × 5 (SR5 p.107).
  await page.getByRole("button", { name: "能力値", exact: true }).click();
  const bod = page.getByRole("slider").first();
  const before = Number(await bod.inputValue());
  await bod.focus();
  await page.keyboard.press("ArrowRight");
  await expect(bod).toHaveValue(String(before + 1));

  // The breakdown is the engine's own itemisation, not a number the client
  // adds up — if the baseline did not reach the backend, the raise is free and
  // this panel stays empty. BOD 3 → 4 is new rating × 5 (SR5 p.107).
  await page.getByRole("button", { name: "成長／買い物の内訳" }).click();
  const spend = page.locator(".career-breakdown .stat").first();
  await expect(spend).toContainText("BOD");
  await expect(spend.locator("b")).toHaveText(`${(before + 1) * 5}K`);

  // The baseline is part of the stored record, so a reload must not re-price
  // the same raise — nor make it free by snapshotting the raised rating.
  await page.reload();
  await waitForEditor(page);
  await expect(page.getByRole("button", { name: "キャリア中" })).toBeVisible();
  await page.getByRole("button", { name: "成長／買い物の内訳" }).click();
  const again = page.locator(".career-breakdown .stat").first();
  await expect(again).toContainText("BOD");
  await expect(again.locator("b")).toHaveText(`${(before + 1) * 5}K`);

  const [stored] = await storedCharacters(page);
  expect(stored.name).toBe("Careerist");
});
