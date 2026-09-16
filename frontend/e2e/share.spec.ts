import { expect, test } from "@playwright/test";
import { encodeFragment, freshCharacter, waitForEditor, watchCsp } from "./helpers";

/**
 * The share page renders a payload anyone can write. jsdom has neither a real
 * CSP nor a real HTML parser, so whether hostile text stays text is a question
 * only a browser answers.
 */

// Each one would run if React ever stopped escaping — and each one is also
// something the CSP must refuse, so a regression in either layer shows up.
const IMG = `<img src=x id=pwn-img onerror="window.__pwned='img'">`;
const SCRIPT = `</textarea></script><script id=pwn-script>window.__pwned='script'</script>`;
const SVG = `<svg id=pwn-svg onload="window.__pwned='svg'"></svg>`;

test("hostile text in a share link is rendered as text and never runs", async ({
  page,
  request,
}) => {
  const base = await freshCharacter(request, "x");
  const { id: _id, derived: _derived, ...state } = base;
  void _id;
  void _derived;
  const payload = {
    ...state,
    name: `Evil ${IMG}`,
    notes: SCRIPT,
    sex: SVG,
    // a user-named knowledge skill: a key, not a value, and printed on the sheet
    knowledge_skills: { [`Lore ${SVG}`]: 2 },
  };

  const violations = watchCsp(page);
  const dialogs: string[] = [];
  page.on("dialog", (d) => {
    dialogs.push(d.message());
    void d.dismiss();
  });

  await page.goto(`/share#c=${encodeFragment({ v: 1, s: payload })}`);
  await expect(page.getByText("共有ビュー（読み取り専用）")).toBeVisible();
  await expect(page.getByText(`Evil ${IMG}`).first()).toBeVisible();

  // every layout, since each renders the free text through its own path
  const layout = page.getByRole("combobox", { name: "レイアウト" });
  for (const value of ["standard", "compact", "text", "print"]) {
    await layout.selectOption(value);
    await expect(page.getByText(/Evil <img/).first()).toBeVisible();
    await expect(page.locator("#pwn-img, #pwn-script, #pwn-svg")).toHaveCount(0);
  }

  expect(await page.evaluate(() => (window as { __pwned?: string }).__pwned)).toBeUndefined();
  expect(dialogs).toEqual([]);
  expect(violations).toEqual([]);
});

test.describe("a share link that cannot be read fails with a message", () => {
  const cases = [
    // not base64url at all
    { name: "garbage", fragment: "!!!not-base64!!!", message: "共有リンクが壊れています。" },
    // valid base64url, not deflate
    { name: "not deflate", fragment: "AAAAAAAA", message: "共有リンクが壊れています。" },
    // a few hundred bytes that inflate past the 4 MB cap
    {
      name: "decompression bomb",
      fragment: encodeFragment({ v: 1, s: { name: "a".repeat(8_000_000) } }),
      message: "共有データが大きすぎます。",
    },
  ];
  for (const { name, fragment, message } of cases) {
    test(name, async ({ page }) => {
      await page.goto(`/share#c=${fragment}`);
      await expect(page.getByText(message)).toBeVisible();
      await expect(page.getByRole("link", { name: "自分のキャラクターへ" })).toBeVisible();
    });
  }

  test("a well-formed envelope the engine rejects", async ({ page }) => {
    // decodes fine; only the backend's model can say `attributes` is wrong
    await page.goto(`/share#c=${encodeFragment({ v: 1, s: { attributes: "nope" } })}`);
    await expect(page.locator(".errors")).toBeVisible();
    await expect(page.getByText("共有ビュー（読み取り専用）")).toHaveCount(0);
  });
});

test("adopting a shared character puts a copy in the visitor's roster", async ({
  page,
  request,
}) => {
  const base = await freshCharacter(request, "Adoptee");
  const { id: sourceId, derived: _derived, ...state } = base;
  void _derived;

  await page.goto(`/share#c=${encodeFragment({ v: 1, s: state })}`);
  await page.getByRole("button", { name: "自分のロースターに取り込む" }).click();

  // the share page hands off through `lastCharacterId`, so the editor must open
  // the adopted character rather than minting a fresh one
  await expect(page).toHaveURL(/\/$/);
  await waitForEditor(page);
  const name = page.getByRole("textbox", { name: "キャラクター名" });
  await expect(name).toHaveValue("Adoptee");

  const adoptedId = await page.evaluate(() => localStorage.getItem("lastCharacterId"));
  expect(adoptedId).toBeTruthy();
  expect(adoptedId).not.toBe(sourceId);

  // and it is in IndexedDB, not just in React state
  await page.reload();
  await waitForEditor(page);
  await expect(name).toHaveValue("Adoptee");
  await expect(
    page.getByRole("combobox", { name: "保存済みキャラクター" }).getByRole("option", {
      name: /Adoptee/,
    }),
  ).toHaveCount(1);
});
