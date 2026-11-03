// Records a narrated walkthrough for YouTube: the character-creation steps
// played by Playwright, one narration clip per scene from macOS `say`, the
// subtitles, a cursor and title/end cards drawn into the page, and ffmpeg to
// put it together as a 1080p mp4.
//
// Run from the repository root with the API on 8100 and the frontend on 3100
// (the same setup as capture-manual.mjs; see scripts/README.md):
//
//   node scripts/record-walkthrough.mjs [--out DIR] [--bgm FILE] [--build-only]
//
// --out         working directory and output (default: chummer-walkthrough in the OS temp dir)
// --bgm         music under the narration: looped, faded, and ducked while it speaks
// --build-only  reuse the last recording in --out; only re-mix (e.g. to add --bgm)
//
// Needs macOS (`say`, `afinfo`), ffmpeg, and Playwright Chromium.
import { execFileSync } from "node:child_process";
import { mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { parseArgs } from "node:util";

const require = createRequire(
  new URL("../frontend/package.json", import.meta.url),
);
const { chromium, expect } = require("@playwright/test");

const { values: args } = parseArgs({
  options: {
    out: { type: "string", default: join(tmpdir(), "chummer-walkthrough") },
    bgm: { type: "string" },
    "build-only": { type: "boolean", default: false },
  },
});
const out = resolve(args.out);
const origin = process.env.MANUAL_ORIGIN || "http://127.0.0.1:3100";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// --- narration -------------------------------------------------------------
// `say` reads English words letter by letter or oddly, so the spoken line and
// the subtitle are kept apart.
const scenes = [
  {
    id: "title",
    say: "チャマー・ウェブの使い方、キャラクター作成編です。",
    sub: "Chummer Web の使い方 ― キャラクター作成編",
  },
  {
    id: "intro",
    say: "チャマー・ウェブは、ブラウザで使える、シャドウラン第5版のキャラクター作成ツールです。インストールは要りません。",
    sub: "Chummer Web は、ブラウザで使える Shadowrun 第5版のキャラクター作成ツールです。\nインストールは要りません。",
  },
  {
    id: "name",
    say: "開くと、新しいキャラクターがひとりできています。まず、名前を入れましょう。",
    sub: "開くと、新しいキャラクターがひとりできています。\nまず名前を入れましょう。",
  },
  {
    id: "priority",
    say: "最初に優先度を決めます。表のマスを押すと、その項目に優先度が割り当てられます。ここでは、能力値をビーにします。",
    sub: "最初に優先度を決めます。表のマスを押すと、その項目に優先度が割り当てられます。\nここでは能力値を B にします。",
  },
  {
    id: "metatype",
    say: "メタタイプのタブで、種族を選びます。今回は、オークにします。",
    sub: "メタタイプのタブで種族を選びます。今回はオークにします。",
  },
  {
    id: "attributes",
    say: "能力値は、スライダーで上げ下げします。右のサイドバーには、残りのポイントや注意点が、すぐに反映されます。",
    sub: "能力値はスライダーで上げ下げします。\n右のサイドバーには、残りのポイントや注意点がすぐに反映されます。",
  },
  {
    id: "sample",
    say: "ここからは、装備まで作り込んだサンプルを読み込んで見ていきます。",
    sub: "ここからは、装備まで作り込んだサンプルを読み込んで見ていきます。",
  },
  {
    id: "sheet",
    say: "シートのタブでは、完成したキャラクターシートを確認できます。印刷や、ピーディーエフにも対応しています。",
    sub: "シートタブでは、完成したキャラクターシートを確認できます。\n印刷や PDF にも対応しています。",
  },
  {
    id: "export",
    say: "書き出しメニューからは、ココフォリアや、ユドナリウム向けのデータをコピーできます。",
    sub: "「書き出し」メニューからは、ココフォリアやユドナリウム向けのデータをコピーできます。",
  },
  {
    id: "copied",
    say: "ボタンの表示が、コピーに変わったら完了です。あとは、そのまま貼り付けるだけです。",
    sub: "ボタンの表示が「コピー ✓」に変わったら完了です。\nあとはそのまま貼り付けるだけです。",
  },
  {
    id: "save",
    say: "キャラクターは、ブラウザの中に自動で保存されます。別の端末に移すときは、ジェイソンで保存してください。",
    sub: "キャラクターはブラウザの中に自動で保存されます。\n別の端末に移すときは「JSON保存」を使ってください。",
  },
  {
    id: "end",
    say: "ご覧いただき、ありがとうございました。",
    sub: "ご覧いただき、ありがとうございました。",
  },
];
if (!args["build-only"]) {
  rmSync(out, { recursive: true, force: true });
  mkdirSync(join(out, "frames"), { recursive: true });
  mkdirSync(join(out, "voice"), { recursive: true });
  for (const [i, s] of scenes.entries()) {
    s.file = join(out, "voice", `${String(i).padStart(2, "0")}-${s.id}.aiff`);
    execFileSync("say", ["-v", "Kyoko", "-r", "185", "-o", s.file, s.say]);
    const info = execFileSync("afinfo", [s.file]).toString();
    s.duration = Number(/estimated duration: ([\d.]+)/.exec(info)[1]);
  }

  // --- browser ----------------------------------------------------------------
  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 720 },
    deviceScaleFactor: 1.5,
    locale: "ja-JP",
  });
  await context.grantPermissions(["clipboard-read", "clipboard-write"], {
    origin,
  });
  // A cursor the screencast can see (the real one is never in it), and the
  // subtitle and card layers, re-created on every load.
  await context.addInitScript(() => {
    const css = `
      #v-cursor{position:fixed;left:-50px;top:-50px;width:26px;height:26px;z-index:2147483647;pointer-events:none;transition:transform .12s}
      #v-cursor.down{transform:scale(.8)}
      #v-ripple{position:fixed;width:44px;height:44px;margin:-22px 0 0 -22px;border-radius:50%;border:3px solid #ffb020;z-index:2147483646;pointer-events:none;opacity:0}
      #v-ripple.on{animation:vr .5s ease-out}
      @keyframes vr{from{opacity:1;transform:scale(.4)}to{opacity:0;transform:scale(1.3)}}
      #v-sub{position:fixed;left:0;right:0;margin:0 auto;width:fit-content;bottom:22px;max-width:92vw;z-index:2147483645;pointer-events:none;
        background:rgba(0,0,0,.78);color:#fff;font:600 23px/1.5 "Hiragino Sans","IBM Plex Sans JP",sans-serif;padding:8px 20px;border-radius:8px;white-space:pre-line;text-align:center}
      #v-sub:empty{display:none}
      body:has(#v-card) #v-cursor{display:none}
      #v-card{position:fixed;inset:0;z-index:2147483644;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;
        background:radial-gradient(circle at 30% 20%,#123a3a,#0b0f14 70%);color:#e8f1f1;font-family:"Hiragino Sans","IBM Plex Sans JP",sans-serif;text-align:center}
      #v-card h1{font-size:64px;margin:0;letter-spacing:.04em}
      #v-card h2{font-size:34px;margin:0;color:#4fd1c5;font-weight:600}
      #v-card p{font-size:20px;margin:0;color:#9fb3b3}
      #v-card .url{font-size:30px;color:#fff;font-weight:600}
    `;
    const add = () => {
      const style = document.createElement("style");
      style.textContent = css;
      document.head.append(style);
      const cursor = document.createElement("div");
      cursor.id = "v-cursor";
      cursor.innerHTML =
        '<svg viewBox="0 0 24 24" width="26" height="26"><path d="M3 2l7.5 19 2.6-7.4L21 11z" fill="#fff" stroke="#000" stroke-width="1.5" stroke-linejoin="round"/></svg>';
      const ripple = document.createElement("div");
      ripple.id = "v-ripple";
      const sub = document.createElement("div");
      sub.id = "v-sub";
      document.body.append(cursor, ripple, sub);
      const at = (e) => {
        cursor.style.left = `${e.clientX - 3}px`;
        cursor.style.top = `${e.clientY - 2}px`;
      };
      document.addEventListener("mousemove", at, true);
      document.addEventListener(
        "mousedown",
        (e) => {
          at(e);
          cursor.classList.add("down");
          ripple.style.left = `${e.clientX}px`;
          ripple.style.top = `${e.clientY}px`;
          ripple.classList.remove("on");
          void ripple.offsetWidth;
          ripple.classList.add("on");
        },
        true,
      );
      document.addEventListener(
        "mouseup",
        () => cursor.classList.remove("down"),
        true,
      );
      const last = sessionStorage.getItem("v-pos");
      if (last) {
        const [x, y] = JSON.parse(last);
        at({ clientX: x, clientY: y });
      }
      window.addEventListener("beforeunload", () => {
        const r = cursor.getBoundingClientRect();
        sessionStorage.setItem(
          "v-pos",
          JSON.stringify([r.left + 3, r.top + 2]),
        );
      });
    };
    if (document.body) add();
    else document.addEventListener("DOMContentLoaded", add);
  });
  const page = await context.newPage();
  let mouse = { x: 640, y: 400 };
  const api = async (path, data) => {
    const response = data
      ? await page.request.post(`${origin}/api/${path}`, { data })
      : await page.request.get(`${origin}/api/${path}`);
    if (!response.ok()) throw new Error(`${path}: ${response.status()}`);
    return response.json();
  };

  // --- helpers ----------------------------------------------------------------
  const glide = async (x, y, ms = 600) => {
    const steps = Math.max(8, Math.round(ms / 16));
    await page.mouse.move(x, y, { steps });
    mouse = { x, y };
  };
  // `edge`: aim near the left end, so the path down a menu column stays clear of
  // the "?" beside each item (hovering one opens a help box over the next item)
  const moveTo = async (locator, ms, edge = false) => {
    await locator.scrollIntoViewIfNeeded();
    const b = await locator.boundingBox();
    await glide(
      edge ? b.x + Math.min(22, b.width / 2) : b.x + b.width / 2,
      b.y + b.height / 2,
      ms,
    );
    await sleep(250);
  };
  const clickOn = async (locator, ms, edge = false) => {
    await moveTo(locator, ms, edge);
    await page.mouse.down();
    await sleep(90);
    await page.mouse.up();
    await sleep(500);
  };
  const tabButton = (name) =>
    page.locator("nav.tabs").getByRole("button", { name, exact: true });
  const subtitle = (text) =>
    page.evaluate((t) => {
      const el = document.getElementById("v-sub");
      if (el) el.textContent = t;
    }, text);
  const card = (html) =>
    page.evaluate((h) => {
      document.getElementById("v-card")?.remove();
      if (!h) return;
      const el = document.createElement("div");
      el.id = "v-card";
      el.innerHTML = h;
      document.body.append(el);
    }, html);
  const smoothScroll = (y, ms) =>
    page.evaluate(
      ([y, ms]) =>
        new Promise((done) => {
          const from = window.scrollY;
          const t0 = performance.now();
          const step = (t) => {
            const k = Math.min(1, (t - t0) / ms);
            const e = k < 0.5 ? 2 * k * k : 1 - (-2 * k + 2) ** 2 / 2;
            window.scrollTo(0, from + (y - from) * e);
            if (k < 1) requestAnimationFrame(step);
            else done();
          };
          requestAnimationFrame(step);
        }),
      [y, ms],
    );
  const ready = () =>
    expect(page.getByText("読み込み中…", { exact: true })).toHaveCount(0);

  // the finished sample, the same one the manual shows
  const catalog = await api("catalog");
  const item = (kind, name) => {
    const rows = Array.isArray(catalog[kind])
      ? catalog[kind]
      : catalog[kind].items;
    const found = rows.find((row) => row.name === name);
    if (!found) throw new Error(`Missing: ${kind}/${name}`);
    return found.id;
  };
  const sample = await api("characters/patch", {
    state: await api("characters/new", { name: "カイト", metatype: "Ork" }),
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
      notes: "動画用の操作サンプルです。",
    },
  });

  await page.goto(origin);
  await expect(
    page.getByRole("textbox", { name: "キャラクター名" }),
  ).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
  await ready();
  await page.mouse.move(mouse.x, mouse.y);

  // --- screencast ---------------------------------------------------------------
  const cdp = await context.newCDPSession(page);
  const frames = [];
  cdp.on("Page.screencastFrame", async ({ data, metadata, sessionId }) => {
    const n = frames.length;
    const file = join(out, "frames", `${String(n).padStart(5, "0")}.png`);
    writeFileSync(file, Buffer.from(data, "base64"));
    frames.push({ file, t: metadata.timestamp });
    await cdp.send("Page.screencastFrameAck", { sessionId }).catch(() => {});
  });
  await card(
    `<h1>Chummer Web</h1><h2>使い方 ― キャラクター作成編</h2><p>Shadowrun 第5版 キャラクター作成ツール（非公式ファンツール）</p>`,
  );
  await sleep(300);
  await cdp.send("Page.startScreencast", {
    format: "png",
    maxWidth: 1920,
    maxHeight: 1080,
    everyNthFrame: 1,
  });
  await sleep(500);
  const t0 = Date.now() / 1000;
  const timeline = [];

  const actions = {
    async title() {},
    async intro() {
      await sleep(400);
      await card(null);
      await sleep(1200);
      await glide(560, 130, 900);
      await sleep(900);
      await glide(1100, 300, 900);
    },
    async name() {
      const box = page.getByRole("textbox", { name: "キャラクター名" });
      await clickOn(box);
      await page.keyboard.press("ControlOrMeta+a");
      await sleep(300);
      await page.keyboard.type("カイト", { delay: 220 });
      await sleep(400);
      await page.keyboard.press("Tab");
      await ready();
    },
    async priority() {
      await clickOn(tabButton("優先度"));
      await ready();
      const table = page.locator("table").filter({ hasText: "魔力/共振力" });
      await table.scrollIntoViewIfNeeded();
      await sleep(800);
      const b = table
        .locator("tr")
        .filter({ hasText: "能力値" })
        .locator("td")
        .nth(2)
        .getByRole("button");
      await moveTo(b, 900);
      await sleep(1800);
      await clickOn(b, 200);
      await ready();
    },
    async metatype() {
      await smoothScroll(0, 600);
      await clickOn(tabButton("メタタイプ"));
      await ready();
      await sleep(600);
      await clickOn(page.getByRole("button", { name: /^オーク/ }), 900);
      await ready();
      await glide(1150, 140, 800);
    },
    async attributes() {
      await clickOn(tabButton("能力値"));
      await ready();
      const bod = page.getByRole("slider").first();
      await moveTo(bod, 800);
      await bod.focus();
      for (let i = 0; i < 3; i++) {
        await sleep(700);
        await page.keyboard.press("ArrowRight");
      }
      await sleep(600);
      await glide(1100, 200, 900);
      await sleep(500);
      await glide(1100, 420, 1200);
    },
    async sample() {
      // the toolbar's own 読込, minus the browser's file picker
      // no hover on 読込 or the buttons near it: each opens a long help box
      await page
        .locator('input[type="file"][aria-label="読込 (JSON/.chum5/.xlsx)"]')
        .setInputFiles({
          name: "kaito.json",
          mimeType: "application/json",
          buffer: Buffer.from(JSON.stringify(sample)),
        });
      await expect(page.getByText("街で生きる用心棒").first())
        .toBeAttached()
        .catch(() => {});
      await ready();
      await page.evaluate(() => document.activeElement?.blur());
      await glide(1100, 330, 900);
    },
    async sheet() {
      await clickOn(tabButton("シート"));
      await ready();
      await sleep(800);
      const top = await page.evaluate(
        () =>
          document.querySelector(".character-sheet").getBoundingClientRect()
            .top +
          window.scrollY -
          60,
      );
      await smoothScroll(top, 1500);
      await sleep(1200);
      await smoothScroll(top + 700, 2500);
      await sleep(800);
      await smoothScroll(0, 900);
    },
    async export() {
      await clickOn(page.getByRole("button", { name: "書き出し ▾" }));
      await sleep(900);
      const first = page.getByRole("button", {
        name: ".chum5書出",
        exact: true,
      });
      const fb = await first.boundingBox();
      await glide(fb.x + 22, fb.y + fb.height / 2, 500);
      await sleep(600);
      await moveTo(
        page.getByRole("button", { name: "ココフォリア", exact: true }),
        900,
        true,
      );
    },
    async copied() {
      await clickOn(
        page.getByRole("button", { name: "ココフォリア", exact: true }),
        200,
        true,
      );
      await expect(page.locator(".menu-note")).toHaveText("コピー ✓");
      await glide(mouse.x + 120, mouse.y + 160, 700);
    },
    async save() {
      await moveTo(
        page.getByRole("button", { name: "JSON保存", exact: true }),
        900,
      );
    },
    async end() {
      await card(
        `<h1>Chummer Web</h1><p class="url">chummer-web.millionskenken.org</p><p>使い方の詳しい説明はサイト内のマニュアルへ</p><p>非公式ファンツール。Catalyst Game Labs / Topps とは関係ありません。データは Chummer5a（GPL-3.0）</p>`,
      );
    },
  };

  for (const s of scenes) {
    const start = Date.now() / 1000 - t0;
    timeline.push({
      id: s.id,
      start,
      voice: s.file,
      duration: s.duration,
      sub: s.sub,
    });
    await subtitle(s.sub);
    const minimum = (s.duration + (s.id === "end" ? 2.5 : 0.9)) * 1000;
    const begun = Date.now();
    await actions[s.id]();
    const left = minimum - (Date.now() - begun);
    if (left > 0) await sleep(left);
    console.log(
      `${s.id}: ${start.toFixed(2)}s (+${((Date.now() - begun) / 1000).toFixed(2)}s)`,
    );
  }
  await subtitle("");
  await sleep(300);
  const end = Date.now() / 1000 - t0;
  await cdp.send("Page.stopScreencast");
  await browser.close();

  writeFileSync(
    join(out, "timeline.json"),
    JSON.stringify(
      {
        t0,
        end,
        frames: frames.map((f) => ({ file: f.file, t: f.t - t0 })),
        timeline,
      },
      null,
      1,
    ),
  );
  console.log(`frames ${frames.length}, length ${end.toFixed(1)}s`);
}

// --- mix --------------------------------------------------------------------
// The screencast sends a frame only when the page changes, so each frame is
// held until the next one arrives (ffmpeg's concat demuxer with durations).
const data = JSON.parse(readFileSync(join(out, "timeline.json"), "utf8"));
const { end } = data;
let frames = data.frames.filter((f) => f.t >= 0);
const before = data.frames.filter((f) => f.t < 0);
if (before.length) frames = [{ ...before.at(-1), t: 0 }, ...frames];
const list = frames.map((f, i) => {
  const next = i + 1 < frames.length ? frames[i + 1].t : end;
  return `file '${f.file}'\nduration ${Math.max(next - f.t, 0.001).toFixed(4)}`;
});
list.push(`file '${frames.at(-1).file}'`);
writeFileSync(join(out, "frames.txt"), list.join("\n") + "\n");

const inputs = ["-f", "concat", "-safe", "0", "-i", join(out, "frames.txt")];
const filters = [];
data.timeline.forEach((scene, i) => {
  inputs.push("-i", scene.voice);
  const ms = Math.round(scene.start * 1000) + 250;
  filters.push(
    `[${i + 1}:a]aresample=48000,adelay=${ms}|${ms},apad[v${i + 1}]`,
  );
});
const voices = data.timeline.map((_, i) => `[v${i + 1}]`).join("");
filters.push(
  `${voices}amix=inputs=${data.timeline.length}:normalize=0,atrim=0:${end.toFixed(3)},asplit=2[voice][key]`,
);
// YouTube plays everything at about -14 LUFS; -16 leaves it headroom
const loud = "loudnorm=I=-16:TP=-1.5:LRA=11,aresample=48000[a]";
if (args.bgm) {
  inputs.push("-stream_loop", "-1", "-i", resolve(args.bgm));
  const b = data.timeline.length + 1;
  filters.push(
    `[${b}:a]aresample=48000,volume=0.35,atrim=0:${end.toFixed(3)},` +
      `afade=t=in:d=1.5,afade=t=out:st=${Math.max(end - 3, 0).toFixed(3)}:d=3[bed]`,
    // the music steps back while the narration plays
    "[bed][key]sidechaincompress=threshold=0.03:ratio=8:attack=20:release=400[ducked]",
    `[voice][ducked]amix=inputs=2:normalize=0,${loud}`,
  );
} else {
  filters.push("[key]anullsink", `[voice]${loud}`);
}
const mp4 = join(out, args.bgm ? "walkthrough-bgm.mp4" : "walkthrough.mp4");
execFileSync(
  "ffmpeg",
  [
    "-y",
    "-loglevel",
    "error",
    ...inputs,
    "-filter_complex",
    filters.join(";"),
    "-map",
    "0:v",
    "-map",
    "[a]",
    "-vf",
    "fps=30,scale=1920:1080:flags=lanczos,format=yuv420p",
    "-c:v",
    "libx264",
    "-preset",
    "slow",
    "-crf",
    "18",
    "-c:a",
    "aac",
    "-b:a",
    "192k",
    "-ar",
    "48000",
    "-movflags",
    "+faststart",
    "-t",
    end.toFixed(3),
    mp4,
  ],
  { stdio: "inherit" },
);
console.log(`Wrote ${mp4} (${end.toFixed(1)}s)`);
