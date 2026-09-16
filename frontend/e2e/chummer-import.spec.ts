import { createHash } from "node:crypto";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test } from "@playwright/test";
import { storedCharacters, waitForEditor } from "./helpers";

/**
 * A save written by Chummer itself, not by this app. The round trip in
 * `character.spec.ts` reads our own writer's output, so both halves can share
 * a misunderstanding; the backend's pytest reads real saves but never through
 * the browser → Next rewrite → body-size guard → IndexedDB path, where a save
 * of several MB (three base64 mugshots) is what actually arrives.
 *
 * Fetched, not committed: it is 5.7 MB of someone else's GPL data. Pinned to a
 * commit and checked by hash, so what runs is exactly what was reviewed.
 */
const FIXTURE = {
  name: "Ghile Mear.chum5",
  commit: "88517555a99e5422e9a215ac88f7e25ecdb69146",
  sha256: "db8f89929b92e2f3a4e6e64e3dcdc905b564f6a640b39ea6b516dc8958dfa853",
};
// gitignored; CI caches it
const CACHE_DIR = join(__dirname, ".fixtures");

async function fixture(): Promise<string> {
  const path = join(CACHE_DIR, FIXTURE.name);
  const matches = (bytes: Buffer) =>
    createHash("sha256").update(bytes).digest("hex") === FIXTURE.sha256;
  try {
    if (matches(readFileSync(path))) return path;
  } catch {}

  const url =
    `https://raw.githubusercontent.com/chummer5a/chummer5a/${FIXTURE.commit}` +
    `/Chummer.Tests/TestFiles/${encodeURIComponent(FIXTURE.name)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`fetching ${url}: HTTP ${res.status}`);
  const bytes = Buffer.from(await res.arrayBuffer());
  if (!matches(bytes)) throw new Error(`${FIXTURE.name} does not match its pinned sha256`);
  mkdirSync(CACHE_DIR, { recursive: true });
  writeFileSync(path, bytes);
  return path;
}

test("a multi-MB save written by Chummer imports, edits, persists and exports", async ({
  page,
}) => {
  const file = await fixture();

  await page.goto("/");
  await waitForEditor(page);
  await page.getByLabel("読込 (JSON/.chum5)").setInputFiles(file);

  const name = page.getByRole("textbox", { name: "キャラクター名" });
  await expect(name).toHaveValue("Ghile Mear");

  // the mugshot made it through the import and into state
  await page.getByRole("button", { name: "シート", exact: true }).click();
  // the rendered sheet, not the thumbnail in the editor above it
  const portrait = page.getByRole("article").getByRole("img", { name: "ポートレート" });
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
