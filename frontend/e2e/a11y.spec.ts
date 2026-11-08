import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { chummerFixture, freshCharacter, waitForEditor } from "./helpers";

/**
 * axe on every tab a character can open, in a real browser — what
 * `eslint-plugin-jsx-a11y` cannot see from the source: a control's computed
 * name, the colours it is actually drawn in, a label that no longer matches
 * its text. WCAG 2.1 A and AA.
 *
 * A fresh character shows the empty tabs and their pickers; the Chummer save
 * shows the rows, with their inputs and selects. Each scan reports what it
 * found with where it was, so a failure names the control.
 */

const TAGS = ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"];

const GEAR_KINDS = [
  "防具",
  "武器",
  "コムリンク",
  "サイバーデッキ",
  "RCC",
  "視覚／聴覚",
  "センサー",
  "ヴィークル",
  "ドローン",
  "一般装備",
  "ドラッグ",
  "ライフスタイル",
  "保管場所",
];

async function violations(page: Page, where: string): Promise<string[]> {
  const result = await new AxeBuilder({ page }).withTags(TAGS).analyze();
  return result.violations.flatMap((v) =>
    v.nodes.map((n) => `${where}: ${v.id} — ${n.target.join(" ")} — ${n.html.slice(0, 120)}`),
  );
}

/** Open each tab in the section bar and scan it; the gear tab once per kind. */
async function scanTabs(page: Page, gearKinds: boolean): Promise<string[]> {
  const nav = page.getByRole("navigation", { name: "セクション" });
  const found: string[] = [];
  for (const name of await nav.getByRole("button").allInnerTexts()) {
    await nav.getByRole("button", { name, exact: true }).click();
    await expect(nav.getByRole("button", { name, exact: true })).toHaveClass(/active/);
    found.push(...(await violations(page, name)));
    if (name === "装備" && gearKinds) {
      for (const kind of GEAR_KINDS) {
        await page.getByRole("button", { name: kind, exact: true }).click();
        found.push(...(await violations(page, `装備/${kind}`)));
      }
    }
  }
  return found;
}

async function importJson(page: Page, state: Record<string, unknown>) {
  await page.goto("/");
  await waitForEditor(page);
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)", { exact: true }).setInputFiles({
    name: "a11y.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(state)),
  });
  await expect(page.getByRole("textbox", { name: "キャラクター名" })).toHaveValue(
    String(state.name),
  );
}

for (const [label, talent] of [
  ["Mystic Adept", "Mystic Adept"],
  ["Technomancer", "Technomancer"],
] as const) {
  test(`a fresh ${label}: every tab passes axe`, async ({ page, request }) => {
    test.setTimeout(120_000);
    const state = await freshCharacter(request, `a11y ${label}`);
    Object.assign(state, {
      priorities: { Heritage: "E", Attributes: "B", Talent: "A", Skills: "C", Resources: "D" },
      talent,
    });
    await importJson(page, state);
    expect(await scanTabs(page, label === "Mystic Adept")).toEqual([]);
  });
}

test("a Chummer save's rows, open panels and the export menu pass axe", async ({ page }) => {
  test.setTimeout(180_000);
  const file = await chummerFixture();
  await page.goto("/");
  await waitForEditor(page);
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)", { exact: true }).setInputFiles(file);
  await expect(page.getByRole("textbox", { name: "キャラクター名" })).toHaveValue("Ghile Mear");

  const found = await scanTabs(page, true);

  // the roster, the editing history and the sheet search are disclosures
  await page.evaluate(() =>
    document.querySelectorAll("details").forEach((d) => {
      d.open = true;
    }),
  );
  found.push(...(await violations(page, "open panels")));

  await page.getByRole("button", { name: "書き出し ▾" }).click();
  found.push(...(await violations(page, "export menu")));
  await page.keyboard.press("Escape");

  expect(found).toEqual([]);
});

test("the creation review passes axe", async ({ page, request }) => {
  const state = await freshCharacter(request, "a11y review");
  await importJson(page, state);
  await page.getByRole("button", { name: "作成完了（キャリア）", exact: true }).click();
  await expect(page.getByRole("region", { name: "作成完了前の確認" })).toBeVisible();
  expect(await violations(page, "creation review")).toEqual([]);
});
