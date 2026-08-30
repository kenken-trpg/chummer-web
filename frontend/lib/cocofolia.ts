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

  if (weapons.length || spells.length) out.push("// ── 判定・抵抗 ──");
  roll(at("REA") + at("INT") + (tm.dodge || 0), "完全回避");
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
