import type { Catalog, Character } from "@/lib/types";
import { attrShort, makeT } from "@/lib/ui-strings";

// BCDice "ShadowRun5": there is no SR5 prefix. It configures the generic
// scattered roll `xB6` (count hits >= 5, auto glitch) and reroll `xR6`
// (reroll 6s for Edge). Limits use `xB6@l`.
//   NB6        -> N d6, count hits
//   NB6@L      -> as above, capped at limit L
//   NR6        -> Edge: N d6, reroll (and add) on 6

const ATTR_ORDER = ["BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL", "EDG", "MAG", "RES"] as const;

type LimitKind = "physical" | "mental" | "social" | null;
const ATTR_LIMIT: Record<string, LimitKind> = {
  BOD: "physical", AGI: "physical", REA: "physical", STR: "physical",
  CHA: "social",
  INT: "mental", LOG: "mental", WIL: "mental",
  EDG: null, MAG: null, RES: null,
};

// weapon category -> active skill (Chummer Weapon.GetSkillDictionaryKey, trimmed)
const WEAPON_SKILL: Record<string, string> = {
  Bows: "Archery", Crossbows: "Archery",
  "Assault Rifles": "Automatics", Carbines: "Automatics", "Machine Pistols": "Automatics",
  "Submachine Guns": "Automatics",
  Blades: "Blades", Clubs: "Clubs", "Improvised Weapons": "Clubs",
  "Assault Cannons": "Heavy Weapons", "Grenade Launchers": "Heavy Weapons",
  "Missile Launchers": "Heavy Weapons", "Light Machine Guns": "Heavy Weapons",
  "Medium Machine Guns": "Heavy Weapons", "Heavy Machine Guns": "Heavy Weapons",
  Shotguns: "Longarms", "Sniper Rifles": "Longarms", "Sporting Rifles": "Longarms",
  "Throwing Weapons": "Throwing Weapons", Unarmed: "Unarmed Combat",
};
const weaponSkill = (w: { useskill?: string; category?: string }) =>
  (w.useskill || "").trim() || WEAPON_SKILL[w.category || ""] || "Pistols";

/** Newline-separated BCDice ShadowRun5 chat-palette commands. */
export function buildChatPalette(ch: Character, catalog: Catalog, tr: (n: string) => string): string {
  const d = ch.derived;
  const totals: Record<string, number> = d.totals || {};
  const at = (k: string) => totals[k] || 0;
  const lim = (k: LimitKind) => (k ? d.limits?.[k] ?? 0 : 0);

  const skillAttr: Record<string, string> = {};
  for (const s of catalog.skills?.skills || []) skillAttr[s.name] = s.attribute;

  const init = d.initiative || { value: 0, dice: 1 };
  const tm = d.test_mods || {};
  const tabs = d.enabled_tabs || [];
  const out: string[] = [];

  const roll = (pool: number, label: string, l: LimitKind = null) =>
    out.push(`${Math.max(pool, 0)}B6${l ? `@${lim(l)}` : ""} ${label}`);

  out.push(`${init.dice}D6+${init.value} イニシアチブ`);

  const specs = ch.skill_specializations || {};
  Object.entries(d.skill_totals || {})
    .filter(([, r]) => r > 0)
    .sort((a, b) => tr(a[0]).localeCompare(tr(b[0]), "ja"))
    .forEach(([name, rating]) => {
      const attr = skillAttr[name] || "";
      const limit = ATTR_LIMIT[attr] ?? null;
      const pool = rating + at(attr);
      roll(pool, tr(name), limit);
      const sp = specs[name];
      if (sp) roll(pool + 2, `${tr(name)}：${tr(sp)}`, limit);
    });

  const skillPool = (name: string) => (d.skill_totals?.[name] || 0);

  // --- unarmed (adepts: Killing Hands / Critical Strike / Penetrating Strike) --
  const unarmedSkill = skillPool("Unarmed Combat");
  const unarmedMods = (d.unarmed_dv || 0) + (d.unarmed_ap || 0) + (d.unarmed_reach || 0);
  if (unarmedSkill > 0 || unarmedMods !== 0) {
    const dv = Math.ceil(at("STR") / 2) + (d.unarmed_dv || 0);
    const ap = d.unarmed_ap || 0;
    const reach = d.unarmed_reach || 0;
    const info = [`DV${dv}S`, `AP${ap === 0 ? "-" : ap}`, reach ? `リーチ+${reach}` : ""].filter(Boolean).join(" ");
    roll(unarmedSkill + at("AGI"), `非武装攻撃 ［${info}］`, "physical");
  }

  // --- weapons: attack test = skill + AGI, limit = weapon Accuracy ---------
  const weapons = d.weapons || [];
  if (weapons.length) out.push("// ── 武器 ──");
  weapons.forEach((w) => {
    const sk = weaponSkill(w);
    const pool = skillPool(sk) + at("AGI");
    const acc = String(w.accuracy || "").trim();
    const accCap = /^\d+$/.test(acc) ? `@${acc}` : "";
    const dmg = [w.damage && `DV${w.damage}`, w.ap && `AP${w.ap}`, w.mode].filter(Boolean).join(" ");
    out.push(`${Math.max(pool, 0)}B6${accCap} ${tr(w.name)}攻撃${dmg ? ` ［${dmg}］` : ""}`);
  });

  // --- spells: casting test = Spellcasting + MAG (limit = Force, variable) --
  const spells = (d.spells || []).filter((s) => (s.kind || "spell") === "spell");
  if (spells.length) out.push("// ── 術式（リミット＝Force） ──");
  spells.forEach((s) => {
    const sk = s.useskill || "Spellcasting";
    const pool = skillPool(sk) + at("MAG");
    out.push(`${Math.max(pool, 0)}B6 ${tr(s.name)}${s.dv ? ` ［DV${s.dv}］` : ""}`);
  });

  // --- conjuring: skill + MAG (limit = Force, variable) --------------------
  if (tabs.includes("spirits")) {
    const conj: [string, string][] = [
      ["Summoning", "精霊召喚"],
      ["Binding", "精霊束縛"],
      ["Banishing", "精霊追放"],
    ];
    const have = conj.filter(([s]) => skillPool(s) > 0);
    if (have.length) out.push("// ── 召喚（リミット＝Force、対抗＝精霊のForce） ──");
    have.forEach(([s, label]) => out.push(`${skillPool(s) + at("MAG")}B6 ${label}`));
  }

  // --- matrix basic actions (limit = the relevant Matrix attribute) --------
  const persona = d.cyberdeck || d.living_persona;
  if (persona) {
    const A = persona.attack ?? 0;
    const S = persona.sleaze ?? 0;
    const DP = persona.dataprocessing ?? 0;
    const FW = persona.firewall ?? 0;
    out.push("// ── マトリクス ──");
    out.push(`${skillPool("Hacking") + at("LOG")}B6@${S} 素早いハッキング`);
    out.push(`${skillPool("Cybercombat") + at("LOG")}B6@${A} 強行アクセス`);
    out.push(`${skillPool("Cybercombat") + at("LOG")}B6@${A} データスパイク`);
    out.push(`${skillPool("Computer") + at("INT")}B6@${DP} マトリクス知覚`);
    out.push(`${at("WIL") + FW}B6 マトリクス防御（フルは +${at("INT")}）`);
  }

  if (weapons.length || spells.length || persona || tabs.includes("spirits")) out.push("// ── 判定・抵抗 ──");
  roll(at("REA") + at("INT") + (tm.dodge || 0), "完全回避");
  const meleeDef = Math.max(skillPool("Unarmed Combat"), skillPool("Blades"), skillPool("Clubs"));
  roll(at("REA") + at("INT") + meleeDef + (tm.dodge || 0), "受け（ブロック／パリィ）", "physical");
  roll(at("REA") + at("INT") + at("WIL") + (tm.dodge || 0), "フル防御");
  out.push("2D6 グレネード散乱（投擲・m／実効ヒットで減算）");
  out.push("4D6 グレネード散乱（発射・m／実効ヒットで減算）");
  roll(at("WIL") + at("CHA") + (tm.composure || 0), "冷静", "social");
  roll(at("INT") + at("CHA") + (tm.judge_intentions || 0), "意図看破", "social");
  roll(at("LOG") + at("WIL") + (tm.memory || 0), "記憶", "mental");
  roll(at("STR") + at("BOD"), "運搬", "physical");
  roll(at("BOD"), "ダメージ抵抗（＋装甲）");
  if (d.drain_resist && tabs.includes("spells")) roll(d.drain_resist.pool, `ドレイン抵抗（${d.drain_resist.attrs}）`);
  if (d.fade_resist && tabs.includes("complexforms")) roll(d.fade_resist.pool, `フェード抵抗（${d.fade_resist.attrs}）`);
  out.push(`// エッジ振り足しは B6→R6、限界突破は @L を外す`);

  return out.join("\n");
}

/** Cocofolia (ccfolia.com) character-piece clipboard payload. */
export function buildCocofolia(ch: Character, catalog: Catalog, tr: (n: string) => string): string {
  const d = ch.derived;
  const t = makeT(catalog);
  const totals: Record<string, number> = d.totals || {};
  const at = (k: string) => totals[k] || 0;
  const init = d.initiative || { value: 0, dice: 1 };

  const params = ATTR_ORDER.filter((k) => (k !== "MAG" && k !== "RES") || at(k) > 0).map((k) => ({
    label: attrShort(k, t),
    value: String(at(k)),
  }));
  params.push({ label: "物理LIM", value: String(d.limits?.physical ?? 0) });
  params.push({ label: "精神LIM", value: String(d.limits?.mental ?? 0) });
  params.push({ label: "社会LIM", value: String(d.limits?.social ?? 0) });
  params.push({ label: "装甲", value: String(d.armor ?? 0) });
  params.push({ label: "ESS", value: String(d.essence ?? 0) });

  const cm = d.condition_monitor || { physical: 0, stun: 0 };
  const status = [
    { label: "物理CM", value: cm.physical, max: cm.physical },
    { label: "精神CM", value: cm.stun, max: cm.stun },
    { label: "エッジ", value: at("EDG"), max: at("EDG") },
  ];

  const memo = [
    `${tr(ch.metatype)}${ch.metavariant ? " / " + tr(ch.metavariant) : ""} ・ ${ch.talent || "Mundane"}`,
    d.tradition ? `伝統: ${tr(d.tradition.name)}` : "",
    d.mentor ? `メンター: ${tr(d.mentor.name)}` : "",
    `イニシアチブ ${init.value}+${init.dice}d6 ・ リミット 物${d.limits?.physical}/精${d.limits?.mental}/社${d.limits?.social}`,
    `装甲 ${d.armor} ・ エッセンス ${d.essence}`,
    "判定は BCDice の ShadowRun5 で。",
  ]
    .filter(Boolean)
    .join("\n");

  return JSON.stringify({
    kind: "character",
    data: {
      name: ch.name || "Runner",
      memo,
      initiative: init.value,
      commands: buildChatPalette(ch, catalog, tr),
      status,
      params,
    },
  });
}

// --- spirits / sprites as their own Cocofolia pieces -----------------------
// A bound spirit / registered sprite is dropped on the table as a separate
// piece so the GM (or the summoner) can run it directly. Attributes are the
// Force / Level-derived values the engine already resolved.

const SPIRIT_ATTR_ORDER = ["BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL"] as const;

type CocofoliaPiece = {
  kind: "character";
  data: {
    name: string;
    memo: string;
    initiative: number;
    commands: string;
    status: { label: string; value: number; max: number }[];
    params: { label: string; value: string }[];
  };
};

/** One piece per bound spirit. Skill test = Force + linked attribute, limit = Force. */
export function buildSpiritPieces(ch: Character, _catalog: Catalog, tr: (n: string) => string): CocofoliaPiece[] {
  return (ch.derived.spirits || [])
    .filter((s) => s.bound)
    .map((s) => {
      const a = s.attributes || {};
      const force = s.force || 1;
      const ini = a.INI ?? force * 2;

      const params: { label: string; value: string }[] = SPIRIT_ATTR_ORDER.filter((k) => (a[k] || 0) > 0).map((k) => ({
        label: k as string,
        value: String(a[k]),
      }));
      params.push({ label: "INI", value: String(ini) });
      params.push({ label: "Force", value: String(force) });

      const physCM = 8 + Math.ceil((a.BOD || 0) / 2);
      const stunCM = 8 + Math.ceil((a.WIL || 0) / 2);
      const status = [
        { label: "物理CM", value: physCM, max: physCM },
        { label: "精神CM", value: stunCM, max: stunCM },
        { label: "エッジ", value: force, max: force },
      ];

      const cmds: string[] = [];
      cmds.push(`2D6+${ini} イニシアチブ`);
      for (const sk of s.skills || []) {
        const attr = sk.attribute || "";
        const pool = (sk.rating || force) + (attr ? a[attr] || 0 : 0);
        cmds.push(`${Math.max(pool, 0)}B6@${force} ${tr(sk.name)}`);
      }
      cmds.push(`${(a.REA || 0) + (a.INT || 0)}B6 完全回避`);
      cmds.push(`${(a.BOD || 0) + force * 2}B6 ダメージ抵抗（イミュニティ）`);
      cmds.push(`${force * 2}B6 精霊追放に対抗`);
      const powers = [...(s.powers || []), ...(s.optionalpowers || [])].map(tr);
      if (powers.length) cmds.push(`// パワー: ${powers.join("、")}`);
      if (s.weaknesses?.length) cmds.push(`// 弱点: ${s.weaknesses.map(tr).join("、")}`);
      cmds.push("// 技能のリミット＝Force。対抗判定はGM。");

      const memo = [
        `${tr(s.name)}（${s.role_label || s.role || "精霊"}） Force ${force}`,
        `束縛済み ・ 残サービス ${s.services}`,
        "判定は BCDice の ShadowRun5。",
      ].join("\n");

      return {
        kind: "character" as const,
        data: { name: `${tr(s.name)} F${force}`, memo, initiative: ini, commands: cmds.join("\n"), status, params },
      };
    });
}

/** One piece per registered sprite. Skill test = 2 × Level, limit = Level. */
export function buildSpritePieces(ch: Character, _catalog: Catalog, tr: (n: string) => string): CocofoliaPiece[] {
  return (ch.derived.sprites || [])
    .filter((s) => s.registered)
    .map((s) => {
      const level = s.level || 1;
      const m = s.matrix || { attack: 0, sleaze: 0, dataprocessing: 0, firewall: 0, initiative: 0 };
      const ini = m.initiative || level * 2;

      const params = [
        { label: "A", value: String(m.attack) },
        { label: "S", value: String(m.sleaze) },
        { label: "DP", value: String(m.dataprocessing) },
        { label: "FW", value: String(m.firewall) },
        { label: "INI", value: String(ini) },
        { label: "Level", value: String(level) },
      ];

      const cm = 8 + Math.ceil(level / 2);
      const status = [
        { label: "マトリクスCM", value: cm, max: cm },
        { label: "エッジ", value: level, max: level },
      ];

      const cmds: string[] = [];
      cmds.push(`${level}D6+${ini} イニシアチブ`);
      for (const sk of s.skills || []) {
        cmds.push(`${(sk.rating || level) + level}B6@${level} ${tr(sk.name)}`);
      }
      cmds.push(`${m.firewall + level}B6 マトリクス防御`);
      cmds.push(`${level * 2}B6 消去（デレゾ）に対抗`);
      const powers = (s.powers || []).map(tr);
      if (powers.length) cmds.push(`// パワー: ${powers.join("、")}`);
      cmds.push("// 技能判定は レベル×2、リミット＝レベル。");

      const memo = [
        `${tr(s.name)} レベル ${level}`,
        `登録済み ・ 残タスク ${s.services}`,
        "判定は BCDice の ShadowRun5。",
      ].join("\n");

      return {
        kind: "character" as const,
        data: { name: `${tr(s.name)} L${level}`, memo, initiative: ini, commands: cmds.join("\n"), status, params },
      };
    });
}

/**
 * Cocofolia clipboard payload for every bound spirit + registered sprite,
 * as a JSON array of pieces. Returns "" when the character has none.
 */
export function buildCocofoliaConjured(ch: Character, catalog: Catalog, tr: (n: string) => string): string {
  const pieces = [...buildSpiritPieces(ch, catalog, tr), ...buildSpritePieces(ch, catalog, tr)];
  return pieces.length ? JSON.stringify(pieces) : "";
}
