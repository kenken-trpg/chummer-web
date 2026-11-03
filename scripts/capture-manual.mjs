// Run from the repository root: node scripts/capture-manual.mjs
// Requires the backend, the frontend, and Playwright Chromium to be running/installed.
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { dirname, join } from "node:path";
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
  // Puts `ch` in the browser's store as the only character and reopens the
  // editor on it, the way the app itself restores the last one.
  const open = async (ch) => {
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
    }, ch);
    await page.reload();
    await expect(
      page.getByRole("textbox", { name: "キャラクター名" }),
    ).toHaveValue(ch.name);
  };
  await open(character);
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
  // Short animations for the steps a still cannot show: the order of the
  // clicks, and what changes after each. Playwright's screenshots carry no
  // cursor, so the control about to be pressed gets an outline for one frame
  // instead. Each clip is written twice: the animation, and its last frame as
  // `-still` for readers who ask for reduced motion (the manual's <picture>).
  const MARK = "data-manual-mark";
  const motion = (region) => {
    const frames = [];
    const frame = async (hold = 1000) => {
      await page.mouse.move(0, 0);
      const png = await page.screenshot({
        animations: "disabled",
        ...(region ? { clip: region } : {}),
      });
      frames.push({ png, hold });
    };
    return {
      frame,
      // outline the control, hold on it, then press it
      async press(locator, hold = 900) {
        await locator.scrollIntoViewIfNeeded();
        await page.evaluate((mark) => {
          if (document.getElementById(mark)) return;
          const style = document.createElement("style");
          style.id = mark;
          style.textContent = `[${mark}]{outline:3px solid #ffb020 !important;outline-offset:2px}`;
          document.head.append(style);
        }, MARK);
        await locator.evaluate((el, mark) => el.setAttribute(mark, ""), MARK);
        await frame(hold);
        await locator.evaluate((el, mark) => el.removeAttribute(mark), MARK);
        await locator.click();
        // the press is a round trip to the engine; let the result land
        await page.waitForTimeout(500);
        await expect(
          page.getByText("読み込み中…", { exact: true }),
        ).toHaveCount(0);
      },
      async save(name) {
        const scaled = await Promise.all(
          frames.map(({ png }) =>
            sharp(png).resize({ width: 960 }).png().toBuffer(),
          ),
        );
        await sharp(scaled, { join: { animated: true } })
          .webp({
            quality: 75,
            effort: 6,
            loop: 0,
            delay: frames.map(({ hold }) => hold),
          })
          .toFile(`${output}${name}.webp`);
        await sharp(scaled.at(-1))
          .webp({ quality: 85 })
          .toFile(`${output}${name}-still.webp`);
        console.log(`Captured ${name} (${frames.length} frames)`);
      },
    };
  };

  // 1. The first three steps of a build, on a fresh character: a priority
  // swap, a metatype, a raised attribute — and the sidebar's points following.
  await open(
    await api("characters/new", { name: "カイト", metatype: "Human" }),
  );
  await tab("優先度");
  {
    const clip = motion();
    const table = page.locator("table").filter({ hasText: "魔力/共振力" });
    await table.scrollIntoViewIfNeeded();
    await clip.frame(1400);
    // the attributes row's B: attributes and skills trade places
    await clip.press(
      table
        .locator("tr")
        .filter({ hasText: "能力値" })
        .locator("td")
        .nth(2)
        .getByRole("button"),
    );
    await clip.frame(1400);
    await clip.press(
      page
        .locator("nav.tabs")
        .getByRole("button", { name: "メタタイプ", exact: true }),
    );
    await page.evaluate(() => window.scrollTo(0, 0));
    await clip.press(page.getByRole("button", { name: /^オーク/ }));
    await clip.frame(1400);
    await clip.press(
      page
        .locator("nav.tabs")
        .getByRole("button", { name: "能力値", exact: true }),
    );
    await page.evaluate(() => window.scrollTo(0, 0));
    const bod = page.getByRole("slider").first();
    await bod.focus();
    for (let i = 0; i < 3; i++) {
      await page.keyboard.press("ArrowRight");
      await page.waitForTimeout(400);
      await clip.frame(600);
    }
    await clip.frame(2000);
    await clip.save("anim-create");
  }
  await open(character);

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
  // On a tab with the sidebar: in the sheet's full-width toolbar 書き出し sits
  // at the right edge, and its panel runs off the screen.
  await tab("能力値");
  await page.getByRole("button", { name: "書き出し ▾" }).click();
  await shot("ui-export-menu");
  await page.keyboard.press("Escape");

  // 2. A copy from the export menu. Picking an item closes the menu, so the
  // コピー ✓ beside 書き出し is the only sign it worked — the clip ends on it.
  {
    const clip = motion({ x: 0, y: 0, width: 1440, height: 560 });
    await clip.frame(1200);
    await clip.press(page.getByRole("button", { name: "書き出し ▾" }));
    await clip.press(
      page.getByRole("button", { name: "ココフォリア", exact: true }),
    );
    await expect(page.locator(".menu-note")).toHaveText("コピー ✓");
    await clip.frame(2400);
    await clip.save("anim-export-copy");
  }

  // The sample as Chummer would save it, for the import clip further down —
  // written now, before the career clip changes it. What the .chum5書出 button
  // fetches, without the browser's download in between.
  const saved = mkdtempSync(join(tmpdir(), "manual-chum5-"));
  const chum5 = join(saved, "カイト.chum5");
  {
    const response = await page.request.post(
      `${origin}/api/characters/chummer`,
      { data: { state: character } },
    );
    if (!response.ok()) throw new Error(`chum5 export: ${response.status()}`);
    writeFileSync(chum5, await response.body());
  }

  // Career mode: one reward, one raise, and the breakdown that prices it. The
  // sample still has creation errors, so the switch asks first. Recorded as
  // the third clip; the career still below is taken from where it ends.
  const career = motion();
  // the sheet tab is full width; the sidebar comes back on any other tab
  await tab("能力値");
  // the copy above leaves コピー ✓ up for two seconds
  await expect(page.locator(".menu-note")).toBeEmpty();
  await career.frame(1200);
  page.once("dialog", (dialog) => void dialog.accept());
  await career.press(
    page.getByRole("button", { name: "作成完了（キャリア）", exact: true }),
  );
  await expect(
    page.getByRole("button", { name: "キャリア中", exact: true }),
  ).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.getByPlaceholder("Run 名など").fill("港の倉庫");
  await page.getByRole("spinbutton", { name: "カルマ" }).fill("12");
  await page.getByRole("spinbutton", { name: "新円" }).fill("6000");
  await career.press(page.getByRole("button", { name: "報酬を追加" }), 1400);
  await expect(page.getByText("港の倉庫 · 12K")).toBeVisible();
  await page.evaluate(() => window.scrollTo(0, 0));
  await career.frame(1400);
  const agi = page.getByRole("slider").nth(1);
  await agi.focus();
  await page.keyboard.press("ArrowRight");
  await page.waitForTimeout(500);
  await career.frame(1400);
  await career.press(page.getByRole("button", { name: "成長／買い物の内訳" }));
  await career.frame(2600);
  await career.save("anim-career");
  await expect(page.locator(".career-breakdown .stat").first()).toContainText(
    "AGI",
  );
  await shot(
    "ui-career-sidebar",
    page.locator(".career-panel").filter({ hasText: "報酬合計" }),
  );

  // 4. Reading a .chum5 back in: a blank runner, 読込, and カイト opens in its
  // place — name, metatype and sidebar all change. The file picker is the browser's
  // own window and never in a screenshot; the outline on 読込 stands in for it.
  {
    await open(
      await api("characters/new", { name: "Runner", metatype: "Human" }),
    );
    const clip = motion();
    await clip.frame(1200);
    const chooser = page.waitForEvent("filechooser");
    await clip.press(
      page.getByRole("button", {
        name: "読込 (JSON/.chum5/.xlsx)",
        exact: true,
      }),
      1400,
    );
    await (await chooser).setFiles(chum5);
    await expect(
      page.getByRole("textbox", { name: "キャラクター名" }),
    ).toHaveValue("カイト");
    await expect(page.getByText("読み込み中…", { exact: true })).toHaveCount(0);
    // focus stays on 読込 after the picker closes, and its help opens on focus
    await page.evaluate(() => {
      document.activeElement?.blur();
      window.scrollTo(0, 0);
    });
    await clip.frame(3000);
    await clip.save("anim-import");
  }
  rmSync(saved, { recursive: true, force: true });

  // The tabs a mundane orc never shows: one sample per kind of character that
  // opens them. Each is a starting point for the screenshot, not a finished
  // build, so a leftover point or a warning in the sidebar is fine.
  const sample = async (name, metatype, patch) =>
    api("characters/patch", {
      state: await api("characters/new", { name, metatype }),
      patch,
    });
  const samples = [
    [
      await sample("アヤ", "Human", {
        priorities: {
          Heritage: "E",
          Attributes: "B",
          Talent: "A",
          Skills: "C",
          Resources: "D",
        },
        talent: "Mystic Adept",
        tradition_id: item("traditions", "Hermetic"),
        mystic_pp: 2,
        spells: ["Manabolt", "Heal", "Invisibility"].map((n) => ({
          spell_id: item("spells", n),
        })),
        adept_powers: [
          { power_id: item("powers", "Improved Reflexes"), rating: 1 },
          { power_id: item("powers", "Killing Hands") },
        ],
        spirits: [
          {
            spirit_id: item("spirits", "Spirit of Air"),
            force: 4,
            services: 2,
          },
        ],
        foci: [{ gear_id: item("foci", "Power Focus"), force: 1 }],
      }),
      { spells: "呪文", adept: "アデプト", spirits: "精霊", foci: "収束具" },
    ],
    [
      await sample("レン", "Human", {
        priorities: {
          Heritage: "E",
          Attributes: "B",
          Talent: "A",
          Skills: "C",
          Resources: "D",
        },
        talent: "Technomancer",
        complex_forms: ["Puppeteer", "Editor", "Cleaner"].map((n) => ({
          form_id: item("complex_forms", n),
        })),
        sprites: [
          { sprite_id: item("sprites", "Crack Sprite"), level: 3, services: 2 },
        ],
      }),
      { complexforms: "複合体", sprites: "スプライト" },
    ],
    [
      await sample("ゴースト", "A.I.", {
        metavariant: "E-Ghost",
        talent: "A.I.",
        priorities: {
          Heritage: "A",
          Attributes: "B",
          Talent: "C",
          Skills: "D",
          Resources: "E",
        },
        ai_programs: ["Exploit", "Armor"].map((n) => ({
          program_id: item("ai_programs", n),
        })),
      }),
      { aiprograms: "プログラム" },
    ],
    [
      // Karma build: the quality alone costs more than a priority build's 25.
      await sample("ジャック", "Human", {
        build_method: "Karma",
        quality_ids: [item("qualities", "Infected: Ghoul (Human)")],
        quality_extras: {
          [item("qualities", "Infected: Ghoul (Human)")]: "STR",
        },
        critter_powers: [
          { power_id: item("buyable_critter_powers", "Tunneling Claws") },
        ],
      }),
      { critterpowers: "クリッター・パワー" },
    ],
  ];
  for (const [ch, tabs] of samples) {
    await open(ch);
    for (const [key, label] of Object.entries(tabs)) {
      await tab(label);
      await shot(`tab-${key}`);
    }
  }

  // A table's own ruleset folder, laid out the way Chummer keeps one:
  // `settings/` beside `customdata/`, with one house quality in it.
  const table = mkdtempSync(join(tmpdir(), "manual-table-"));
  const guid = "manual-table";
  for (const [path, text] of Object.entries({
    "settings/table.xml": `<?xml version="1.0" encoding="utf-8"?>
<settings>
  <name>卓のハウスルール</name>
  <books><book>SR5</book><book>RG</book></books>
  <customdatadirectorynames>
    <customdatadirectoryname>
      <directoryname>${guid}&gt;1</directoryname>
      <enabled>True</enabled>
    </customdatadirectoryname>
  </customdatadirectorynames>
</settings>`,
    "customdata/table/manifest.xml": `<manifest><guid>${guid}</guid><version>1</version></manifest>`,
    "customdata/table/custom_qualities.xml":
      `<chummer><qualities><quality><id>${guid}-q</id><name>Table Favor</name>` +
      `<karma>5</karma><category>Positive</category><source>SR5</source><page>1</page>` +
      `</quality></qualities></chummer>`,
  })) {
    mkdirSync(dirname(join(table, path)), { recursive: true });
    writeFileSync(join(table, path), text);
  }
  await open(character);
  await tab("優先度");
  await page
    .getByLabel("スタイル一式を読み込む", { exact: true })
    .setInputFiles(table);
  await expect(
    page.getByText("カスタムデータを 1 件適用しました"),
  ).toBeVisible();
  // the report shows before the picker has switched to the loaded file
  await expect(page.locator(".settings-picker select")).toHaveValue(
    "卓のハウスルール",
  );
  await page.getByRole("button", { name: "内訳を見る" }).click();
  await shot("ui-settings-folder", page.locator(".settings-picker"));
  rmSync(table, { recursive: true, force: true });
} finally {
  await browser.close();
}
