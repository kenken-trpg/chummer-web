import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { expect, test } from "@playwright/test";
import { storedCharacters, waitForEditor } from "./helpers";

/**
 * The custom-data handshake: the browser keeps the `customdata/` files in
 * IndexedDB and sends only their hash; a server that no longer has the merge
 * answers 409, and `req` re-uploads from IndexedDB and retries. In vitest the
 * fetch is mocked and IndexedDB is fake, so nothing checks that the two real
 * halves agree on the 409 body, the hash, and the stored files.
 *
 * The server's cache is an 8-entry LRU, so the test evicts the table's merge
 * by uploading eight others — the same thing a busy server does — rather than
 * adding a test-only way in. That is 10 of the 20/minute the upload endpoint
 * allows from one address.
 */

const GUID = "e2e-table";
const EVICTIONS = 8; // dataset_store.MAX_SETS

// a ruleset folder as Chummer lays one out: `settings/` and `customdata/` siblings
const SETTINGS = `<?xml version="1.0" encoding="utf-8"?>
<settings>
  <name>E2E Table</name>
  <books><book>SR5</book></books>
  <customdatadirectorynames>
    <customdatadirectoryname>
      <directoryname>${GUID}&gt;1</directoryname>
      <enabled>True</enabled>
    </customdatadirectoryname>
  </customdatadirectorynames>
</settings>`;

function pack(guid: string, dir: string) {
  return {
    [`${dir}/manifest.xml`]: `<manifest><guid>${guid}</guid><version>1</version></manifest>`,
    [`${dir}/custom_qualities.xml`]:
      `<chummer><qualities><quality><id>${guid}-q</id><name>${guid} quality</name>` +
      `<karma>5</karma><category>Positive</category><source>SR5</source><page>1</page>` +
      `</quality></qualities></chummer>`,
  };
}

test("custom data the server forgot is re-uploaded from IndexedDB", async ({ page, request }) => {
  // a directory input only takes a real directory
  const table = test.info().outputPath("table");
  const files: Record<string, string> = {
    "settings/e2e.xml": SETTINGS,
    ...Object.fromEntries(
      Object.entries(pack(GUID, "e2e")).map(([path, text]) => [`customdata/${path}`, text]),
    ),
  };
  for (const [path, text] of Object.entries(files)) {
    mkdirSync(dirname(join(table, path)), { recursive: true });
    writeFileSync(join(table, path), text);
  }

  await page.goto("/");
  await waitForEditor(page);
  await page.getByLabel("スタイル一式を読み込む").setInputFiles(table);
  await expect(page.getByText("カスタムデータを 1 件適用しました")).toBeVisible();
  // the report shows before the patch carrying the hash lands; evicting any
  // sooner races that patch rather than the reload below
  await expect
    .poll(async () => (await storedCharacters(page))[0]?.settings?.dataset, { timeout: 15_000 })
    .toBeTruthy();

  // push the table's merge out of the server's cache
  for (let i = 0; i < EVICTIONS; i++) {
    const guid = `e2e-evict-${i}-${test.info().workerIndex}-${Date.now()}`;
    const res = await request.post("/api/customdata", {
      data: { files: pack(guid, "x"), customdata: [`${guid}>1`] },
    });
    expect(res.ok()).toBe(true);
  }

  const seen: string[] = [];
  page.on("response", (res) => {
    const path = new URL(res.url()).pathname;
    if (path.startsWith("/api/characters/") || path === "/api/customdata") {
      seen.push(`${res.request().method()} ${path} ${res.status()}`);
    }
  });

  // a reload drops the page's memory, so the files can only come from IndexedDB
  await page.reload();
  await waitForEditor(page);
  const name = page.getByRole("textbox", { name: "キャラクター名" });
  await name.fill("After eviction");
  await name.blur();

  await expect
    .poll(() => seen)
    .toEqual(
      expect.arrayContaining([
        "POST /api/characters/patch 409",
        "POST /api/customdata 200",
        "POST /api/characters/patch 200",
      ]),
    );
  // the 409 comes first, the upload answers it, and the retry succeeds
  const conflict = seen.indexOf("POST /api/characters/patch 409");
  expect(seen.indexOf("POST /api/customdata 200")).toBeGreaterThan(conflict);
  expect(seen.lastIndexOf("POST /api/characters/patch 200")).toBeGreaterThan(conflict);

  await expect(page.getByText("カスタムデータを読み込めませんでした。")).toHaveCount(0);
  await expect(name).toHaveValue("After eviction");
});
