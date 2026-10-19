// Run from the repository root: node scripts/capture-manual.mjs
// Requires the backend, the frontend, and Playwright Chromium to be running/installed.
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const require = createRequire(
  new URL("../frontend/package.json", import.meta.url),
);
const { chromium, expect } = require("@playwright/test");
const sharp = require("sharp");

const origin = process.env.MANUAL_ORIGIN || "http://127.0.0.1:3100";
const output = fileURLToPath(
  new URL("../frontend/public/manual/img/", import.meta.url),
);
const browser = await chromium.launch();
try {
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1000 },
    locale: "ja-JP",
  });
  const api = async (path, data) => {
    const response = data
      ? await page.request.post(`${origin}/api/${path}`, { data })
      : await page.request.get(`${origin}/api/${path}`);
    if (!response.ok())
      throw new Error(`${path}: ${response.status()} ${await response.text()}`);
    return response.json();
  };
  const catalog = await api("catalog");
  const item = (kind, name) => {
    const rows = Array.isArray(catalog[kind])
      ? catalog[kind]
      : catalog[kind].items;
    const found = rows.find((row) => row.name === name);
    if (!found) throw new Error(`Missing sample item: ${kind}/${name}`);
    return found.id;
  };
  const fresh = await api("characters/new", {
    name: "カイト",
    metatype: "Ork",
  });
  const character = await api("characters/patch", {
    state: fresh,
    patch: {
      attributes: {
        BOD: 7,
        AGI: 4,
        REA: 3,
        STR: 5,
        WIL: 3,
        LOG: 3,
        INT: 3,
        CHA: 3,
        EDG: 1,
      },
      skill_groups: { Acting: 2, "Close Combat": 2 },
      native_languages: ["Japanese"],
      quality_ids: [
        item("qualities", "Ambidextrous"),
        item("qualities", "Analytical Mind"),
      ],
      armor: [{ armor_id: item("armor", "Armor Jacket") }],
      weapons: [{ weapon_id: item("weapons", "Ares Predator V") }],
      cyberware: [{ ware_id: item("cyberware", "Datajack") }],
      lifestyles: [{ lifestyle_id: item("lifestyles", "Low"), months: 1 }],
      contacts: [
        {
          name: "ミスター・ジョンソン",
          role: "仕事の仲介人",
          connection: 2,
          loyalty: 2,
        },
      ],
      age: "24",
      sex: "男性",
      height: "190 cm",
      weight: "110 kg",
      concept: "街で生きる用心棒",
      player_name: "サンプル",
      appearance: "黒いジャケットを着たオーク。",
      background: "地元の人脈を頼りにランナーになった。",
      notes: "マニュアル用の操作サンプルです。",
    },
  });
  await page.goto(origin);
  await expect(
    page.getByRole("textbox", { name: "キャラクター名" }),
  ).toBeVisible();
  await page.evaluate(async (ch) => {
    const db = await new Promise((resolve, reject) => {
      const request = indexedDB.open("chummer-web", 1);
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
    await new Promise((resolve, reject) => {
      const tx = db.transaction("characters", "readwrite");
      const store = tx.objectStore("characters");
      store.clear();
      store.put({
        id: ch.id,
        savedAt: Date.now(),
        schemaVersion: 2,
        character: ch,
      });
      tx.oncomplete = resolve;
      tx.onerror = () => reject(tx.error);
    });
    db.close();
    localStorage.setItem("lastCharacterId", ch.id);
  }, character);
  await page.reload();
  await expect(
    page.getByRole("textbox", { name: "キャラクター名" }),
  ).toHaveValue("カイト");
  await page.evaluate(() => document.fonts.ready);
  const shot = async (name, locator) => {
    await page.mouse.move(0, 0);
    const png = locator
      ? await locator.screenshot({ animations: "disabled" })
      : await page.screenshot({ animations: "disabled" });
    await sharp(png).webp({ quality: 90 }).toFile(`${output}${name}.webp`);
    console.log(`Captured ${name}`);
  };
  const tab = async (name) => {
    await page
      .locator("nav.tabs")
      .getByRole("button", { name, exact: true })
      .click();
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.evaluate(() => document.fonts.ready);
    await expect(page.getByText("読み込み中…", { exact: true })).toHaveCount(0);
  };
  await shot("ui-toolbar", page.locator(".toolbar"));
  await shot("ui-sidebar", page.locator("aside.side"));
  for (const [key, label] of Object.entries({
    priority: "優先度",
    meta: "メタタイプ",
    attrs: "能力値",
    skills: "技能",
    qualities: "資質",
    cyber: "サイバー",
    bio: "バイオ",
    gear: "装備",
    contacts: "コンタクト",
    martial: "格闘技",
    check: "チェック",
    sheet: "シート",
  })) {
    await tab(label);
    await shot(`tab-${key}`);
    if (key === "gear") {
      await page
        .getByRole("button", { name: "ライフスタイル", exact: true })
        .click();
      await shot("tab-gear-lifestyle");
    }
  }
  await page.locator(".character-sheet").scrollIntoViewIfNeeded();
  await page.evaluate(() => {
    window.scrollTo(
      0,
      document.querySelector(".character-sheet").getBoundingClientRect().top +
        window.scrollY -
        65,
    );
  });
  await shot("tab-sheet-body");
  await page.evaluate(() => window.scrollBy(0, 850));
  await shot("tab-sheet-body2");
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.getByRole("button", { name: "書き出し ▾" }).click();
  await shot("ui-export-menu");
} finally {
  await browser.close();
}
