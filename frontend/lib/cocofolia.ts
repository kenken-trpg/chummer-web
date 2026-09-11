import type { Catalog, Character } from "@/lib/types";
import { attrShort, makeT } from "@/lib/ui-strings";
import { type Locale, type MsgKey, type UiFn, translate } from "@/lib/i18n";
import { renderNotice } from "@/lib/engine-notices";

// Cocofolia is a Japanese VTT, so the export defaults to Japanese when a
// caller says nothing; it follows the UI locale otherwise. Dice commands
// (`9B6@3`) are BCDice syntax and never translated — only the labels are.
const uiFor =
  (locale: Locale): UiFn =>
  (key, vars) =>
    translate(locale, key, vars);

// BCDice "ShadowRun5": there is no SR5 prefix. It configures the generic
// scattered roll `xB6` (count hits >= 5, auto glitch) and reroll `xR6`
// (reroll 6s for Edge). Limits use `xB6@l`.
//   NB6        -> N d6, count hits
//   NB6@L      -> as above, capped at limit L
//   NR6        -> Edge: N d6, reroll (and add) on 6

const ATTR_ORDER = [
  "BOD",
  "AGI",
  "REA",
  "STR",
  "CHA",
  "INT",
  "LOG",
  "WIL",
  "EDG",
  "MAG",
  "RES",
] as const;

type LimitKind = "physical" | "mental" | "social" | null;
const ATTR_LIMIT: Record<string, LimitKind> = {
  BOD: "physical",
  AGI: "physical",
  REA: "physical",
  STR: "physical",
  CHA: "social",
  INT: "mental",
  LOG: "mental",
  WIL: "mental",
  EDG: null,
  MAG: null,
  RES: null,
};

// weapon category -> active skill (Chummer Weapon.GetSkillDictionaryKey, trimmed)
const WEAPON_SKILL: Record<string, string> = {
  Bows: "Archery",
  Crossbows: "Archery",
  "Assault Rifles": "Automatics",
  Carbines: "Automatics",
  "Machine Pistols": "Automatics",
  "Submachine Guns": "Automatics",
  Blades: "Blades",
  Clubs: "Clubs",
  "Improvised Weapons": "Clubs",
  "Assault Cannons": "Heavy Weapons",
  "Grenade Launchers": "Heavy Weapons",
  "Missile Launchers": "Heavy Weapons",
  "Light Machine Guns": "Heavy Weapons",
  "Medium Machine Guns": "Heavy Weapons",
  "Heavy Machine Guns": "Heavy Weapons",
  Shotguns: "Longarms",
  "Sniper Rifles": "Longarms",
  "Sporting Rifles": "Longarms",
  "Throwing Weapons": "Throwing Weapons",
  Unarmed: "Unarmed Combat",
};
const weaponSkill = (w: { useskill?: string; category?: string }) =>
  (w.useskill || "").trim() || WEAPON_SKILL[w.category || ""] || "Pistols";

/** Newline-separated BCDice ShadowRun5 chat-palette commands. */
export function buildChatPalette(
  ch: Character,
  catalog: Catalog,
  tr: (n: string) => string,
  locale: Locale = "ja",
): string {
  const ui = uiFor(locale);
  const d = ch.derived;
  const totals: Record<string, number> = d.totals || {};
  const at = (k: string) => totals[k] || 0;
  const lim = (k: LimitKind) => (k ? (d.limits?.[k] ?? 0) : 0);

  const skillAttr: Record<string, string> = {};
  for (const s of catalog.skills?.skills || []) skillAttr[s.name] = s.attribute;
  // `<swapskillattribute>` (Empathic Listener: Etiquette off INT) moves the
  // pool *and* the limit that comes with the attribute; the spec-limited
  // variant only moves the specialized roll below.
  const specSwap: Record<string, { spec: string; attribute: string }> = {};
  for (const row of d.skill_attribute_swaps || []) {
    if (row.spec) specSwap[row.skill] = { spec: row.spec, attribute: row.attribute };
    else skillAttr[row.skill] = row.attribute;
  }

  const init = d.initiative || { value: 0, dice: 1 };
  const tm = d.test_mods || {};
  const tabs = d.enabled_tabs || [];
  const out: string[] = [];

  const roll = (pool: number, label: string, l: LimitKind = null) =>
    out.push(`${Math.max(pool, 0)}B6${l ? `@${lim(l)}` : ""} ${label}`);

  out.push(`${init.dice}D6+${init.value} ${ui("coco.initiative")}`);

  const specs = ch.skill_specializations || {};
  Object.entries(d.skill_totals || {})
    .filter(([, r]) => r > 0)
    .sort((a, b) => tr(a[0]).localeCompare(tr(b[0]), locale))
    .forEach(([name, rating]) => {
      const attr = skillAttr[name] || "";
      const limit = ATTR_LIMIT[attr] ?? null;
      const pool = rating + at(attr);
      roll(pool, tr(name), limit);
      const sp = specs[name];
      if (sp) {
        // Only the named specialization swaps — any other one rolls as printed.
        const swap = specSwap[name];
        const swapped = swap && swap.spec === sp ? swap.attribute : "";
        const specAttr = swapped || attr;
        roll(
          rating + at(specAttr) + 2,
          `${tr(name)}：${tr(sp)}`,
          swapped ? (ATTR_LIMIT[specAttr] ?? null) : limit,
        );
      }
    });

  const skillPool = (name: string) => d.skill_totals?.[name] || 0;

  // --- unarmed (adepts: Killing Hands / Critical Strike / Penetrating Strike) --
  const unarmedSkill = skillPool("Unarmed Combat");
  const unarmedMods = (d.unarmed_dv || 0) + (d.unarmed_ap || 0) + (d.unarmed_reach || 0);
  if (unarmedSkill > 0 || unarmedMods !== 0) {
    const dv = Math.ceil(at("STR") / 2) + (d.unarmed_dv || 0);
    const ap = d.unarmed_ap || 0;
    const reach = d.unarmed_reach || 0;
    const info = [`DV${dv}S`, `AP${ap === 0 ? "-" : ap}`, reach ? ui("coco.reach", { reach }) : ""]
      .filter(Boolean)
      .join(" ");
    roll(unarmedSkill + at("AGI"), `${ui("coco.unarmed")} ［${info}］`, "physical");
  }

  // --- weapons: attack test = skill + AGI, limit = weapon Accuracy ---------
  const weapons = d.weapons || [];
  if (weapons.length) out.push(ui("coco.secWeapons"));
  weapons.forEach((w) => {
    const sk = weaponSkill(w);
    const pool = skillPool(sk) + at("AGI");
    const acc = String(w.accuracy || "").trim();
    const accCap = /^\d+$/.test(acc) ? `@${acc}` : "";
    const dmg = [w.damage && `DV${w.damage}`, w.ap && `AP${w.ap}`, w.mode]
      .filter(Boolean)
      .join(" ");
    out.push(
      `${Math.max(pool, 0)}B6${accCap} ${ui("coco.attack", { name: tr(w.name) })}${dmg ? ` ［${dmg}］` : ""}`,
    );
  });

  // --- spells: casting test = Spellcasting + MAG (limit = Force, variable) --
  const spells = (d.spells || []).filter((s) => (s.kind || "spell") === "spell");
  if (spells.length) out.push(ui("coco.secSpells"));
  spells.forEach((s) => {
    const sk = s.useskill || "Spellcasting";
    const pool = skillPool(sk) + at("MAG");
    out.push(`${Math.max(pool, 0)}B6 ${tr(s.name)}${s.dv ? ` ［DV${s.dv}］` : ""}`);
  });

  // --- conjuring: skill + MAG (limit = Force, variable) --------------------
  if (tabs.includes("spirits")) {
    const conj: [string, MsgKey][] = [
      ["Summoning", "coco.summoning"],
      ["Binding", "coco.binding"],
      ["Banishing", "coco.banishing"],
    ];
    const have = conj.filter(([s]) => skillPool(s) > 0);
    if (have.length) out.push(ui("coco.secConjuring"));
    have.forEach(([s, label]) => out.push(`${skillPool(s) + at("MAG")}B6 ${ui(label)}`));
  }

  // --- matrix basic actions (limit = the relevant Matrix attribute) --------
  // a commlink with a dongle can hack too (DT p.61) — after a deck or a living persona
  const donglelink = d.commlink && (d.commlink.attack || d.commlink.sleaze) ? d.commlink : null;
  const persona = d.cyberdeck || d.living_persona || donglelink;
  if (persona) {
    const A = persona.attack ?? 0;
    const S = persona.sleaze ?? 0;
    const DP = persona.dataprocessing ?? 0;
    const FW = persona.firewall ?? 0;
    out.push(ui("coco.secMatrix"));
    // VR only: in AR the character rolls the meat initiative at the top.
    const mi = d.matrix_initiative;
    if (mi) {
      out.push(`${mi.cold_dice}D6+${mi.value} ${ui("coco.matrixInitCold")}`);
      out.push(`${mi.hot_dice}D6+${mi.value} ${ui("coco.matrixInitHot")}`);
    }
    out.push(`${skillPool("Hacking") + at("LOG")}B6@${S} ${ui("coco.hackOnTheFly")}`);
    out.push(`${skillPool("Cybercombat") + at("LOG")}B6@${A} ${ui("coco.bruteForce")}`);
    out.push(`${skillPool("Cybercombat") + at("LOG")}B6@${A} ${ui("coco.dataSpike")}`);
    out.push(`${skillPool("Computer") + at("INT")}B6@${DP} ${ui("coco.matrixPerception")}`);
    out.push(`${at("WIL") + FW}B6 ${ui("coco.matrixDefense", { int: at("INT") })}`);
  }

  if (weapons.length || spells.length || persona || tabs.includes("spirits"))
    out.push(ui("coco.secTests"));
  roll(at("REA") + at("INT") + (tm.dodge || 0), ui("coco.defense"));
  const meleeDef = Math.max(skillPool("Unarmed Combat"), skillPool("Blades"), skillPool("Clubs"));
  roll(at("REA") + at("INT") + meleeDef + (tm.dodge || 0), ui("coco.meleeDefense"), "physical");
  roll(at("REA") + at("INT") + at("WIL") + (tm.dodge || 0), ui("coco.fullDefense"));
  out.push(`2D6 ${ui("coco.scatterThrown")}`);
  out.push(`4D6 ${ui("coco.scatterLaunched")}`);
  roll(at("WIL") + at("CHA") + (tm.composure || 0), ui("coco.composure"), "social");
  roll(at("INT") + at("CHA") + (tm.judge_intentions || 0), ui("coco.judge"), "social");
  roll(at("LOG") + at("WIL") + (tm.memory || 0), ui("coco.memory"), "mental");
  roll(at("STR") + at("BOD"), ui("coco.lifting"), "physical");
  roll(at("BOD"), ui("coco.damageResist"));
  if (d.drain_resist && tabs.includes("spells"))
    roll(d.drain_resist.pool, ui("coco.drainResist", { attrs: d.drain_resist.attrs }));
  if (d.fade_resist && tabs.includes("complexforms"))
    roll(d.fade_resist.pool, ui("coco.fadeResist", { attrs: d.fade_resist.attrs }));
  out.push(ui("coco.edgeNote"));

  return out.join("\n");
}

/** Cocofolia (ccfolia.com) character-piece clipboard payload. */
export function buildCocofolia(
  ch: Character,
  catalog: Catalog,
  tr: (n: string) => string,
  locale: Locale = "ja",
): string {
  const ui = uiFor(locale);
  const d = ch.derived;
  const t = makeT(catalog, locale);
  const totals: Record<string, number> = d.totals || {};
  const at = (k: string) => totals[k] || 0;
  const init = d.initiative || { value: 0, dice: 1 };

  const params = ATTR_ORDER.filter((k) => (k !== "MAG" && k !== "RES") || at(k) > 0).map((k) => ({
    label: attrShort(k, t),
    value: String(at(k)),
  }));
  params.push({ label: ui("coco.limPhysical"), value: String(d.limits?.physical ?? 0) });
  params.push({ label: ui("coco.limMental"), value: String(d.limits?.mental ?? 0) });
  params.push({ label: ui("coco.limSocial"), value: String(d.limits?.social ?? 0) });
  params.push({ label: ui("coco.armor"), value: String(d.armor ?? 0) });
  params.push({ label: "ESS", value: String(d.essence ?? 0) });

  const cm = d.condition_monitor || { physical: 0, stun: 0 };
  const status = [
    { label: ui("coco.cmPhysical"), value: cm.physical, max: cm.physical },
    { label: ui("coco.cmStun"), value: cm.stun, max: cm.stun },
    { label: ui("coco.edge"), value: at("EDG"), max: at("EDG") },
  ];

  const memo = [
    `${tr(ch.metatype)}${ch.metavariant ? " / " + tr(ch.metavariant) : ""}${ui(
      "common.termSep",
    )}${ch.talent || "Mundane"}`,
    d.tradition ? ui("coco.memoTradition", { name: tr(d.tradition.name) }) : "",
    d.mentor
      ? ui(d.needs_paragon ? "coco.memoParagon" : "coco.memoMentor", { name: tr(d.mentor.name) })
      : "",
    ui("coco.memoInit", {
      value: init.value,
      dice: init.dice,
      physical: d.limits?.physical ?? 0,
      mental: d.limits?.mental ?? 0,
      social: d.limits?.social ?? 0,
    }),
    ui("coco.memoArmor", { armor: d.armor ?? 0, essence: d.essence ?? 0 }),
    ui("coco.memoDice"),
  ]
    .filter(Boolean)
    .join("\n");

  return JSON.stringify({
    kind: "character",
    data: {
      name: ch.name || "Runner",
      memo,
      initiative: init.value,
      commands: buildChatPalette(ch, catalog, tr, locale),
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
export function buildSpiritPieces(
  ch: Character,
  _catalog: Catalog,
  tr: (n: string) => string,
  locale: Locale = "ja",
): CocofoliaPiece[] {
  const ui = uiFor(locale);
  return (ch.derived.spirits || [])
    .filter((s) => s.bound)
    .map((s) => {
      const a = s.attributes || {};
      const force = s.force || 1;
      const ini = a.INI ?? force * 2;

      const params: { label: string; value: string }[] = SPIRIT_ATTR_ORDER.filter(
        (k) => (a[k] || 0) > 0,
      ).map((k) => ({
        label: k as string,
        value: String(a[k]),
      }));
      params.push({ label: "INI", value: String(ini) });
      params.push({ label: "Force", value: String(force) });

      const physCM = 8 + Math.ceil((a.BOD || 0) / 2);
      const stunCM = 8 + Math.ceil((a.WIL || 0) / 2);
      const status = [
        { label: ui("coco.cmPhysical"), value: physCM, max: physCM },
        { label: ui("coco.cmStun"), value: stunCM, max: stunCM },
        { label: ui("coco.edge"), value: force, max: force },
      ];

      const cmds: string[] = [];
      cmds.push(`2D6+${ini} ${ui("coco.initiative")}`);
      for (const sk of s.skills || []) {
        const attr = sk.attribute || "";
        const pool = (sk.rating || force) + (attr ? a[attr] || 0 : 0);
        cmds.push(`${Math.max(pool, 0)}B6@${force} ${tr(sk.name)}`);
      }
      cmds.push(`${(a.REA || 0) + (a.INT || 0)}B6 ${ui("coco.defense")}`);
      cmds.push(`${(a.BOD || 0) + force * 2}B6 ${ui("coco.immunityResist")}`);
      cmds.push(`${force * 2}B6 ${ui("coco.resistBanishing")}`);
      const powers = [...(s.powers || []), ...(s.optionalpowers || [])].map((p) => tr(p.name));
      if (powers.length) cmds.push(ui("coco.powers", { list: powers.join(ui("common.listSep")) }));
      if (s.weaknesses?.length)
        cmds.push(ui("coco.weaknesses", { list: s.weaknesses.map(tr).join(ui("common.listSep")) }));
      cmds.push(ui("coco.spiritNote"));

      const memo = [
        ui("coco.spiritName", {
          name: tr(s.name),
          role: s.role_label ? renderNotice(s.role_label, ui) : s.role || ui("coco.spirit"),
          force,
        }),
        ui("coco.spiritMemo", { services: s.services }),
        ui("coco.memoDice"),
      ].join("\n");

      return {
        kind: "character" as const,
        data: {
          name: `${tr(s.name)} F${force}`,
          memo,
          initiative: ini,
          commands: cmds.join("\n"),
          status,
          params,
        },
      };
    });
}

/** One piece per registered sprite. Skill test = 2 × Level, limit = Level. */
export function buildSpritePieces(
  ch: Character,
  _catalog: Catalog,
  tr: (n: string) => string,
  locale: Locale = "ja",
): CocofoliaPiece[] {
  const ui = uiFor(locale);
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
        { label: ui("coco.cmMatrix"), value: cm, max: cm },
        { label: ui("coco.edge"), value: level, max: level },
      ];

      const cmds: string[] = [];
      cmds.push(`${level}D6+${ini} ${ui("coco.initiative")}`);
      for (const sk of s.skills || []) {
        cmds.push(`${(sk.rating || level) + level}B6@${level} ${tr(sk.name)}`);
      }
      cmds.push(`${m.firewall + level}B6 ${ui("coco.matrixDefensePlain")}`);
      cmds.push(`${level * 2}B6 ${ui("coco.resistDerez")}`);
      const powers = (s.powers || []).map((p) => tr(p.name));
      if (powers.length) cmds.push(ui("coco.powers", { list: powers.join(ui("common.listSep")) }));
      cmds.push(ui("coco.spriteNote"));

      const memo = [
        ui("coco.spriteLevel", { name: tr(s.name), level }),
        ui("coco.spriteMemo", { services: s.services }),
        ui("coco.memoDice"),
      ].join("\n");

      return {
        kind: "character" as const,
        data: {
          name: `${tr(s.name)} L${level}`,
          memo,
          initiative: ini,
          commands: cmds.join("\n"),
          status,
          params,
        },
      };
    });
}

/**
 * Cocofolia clipboard payload for every bound spirit + registered sprite,
 * as a JSON array of pieces. Returns "" when the character has none.
 */
export function buildCocofoliaConjured(
  ch: Character,
  catalog: Catalog,
  tr: (n: string) => string,
  locale: Locale = "ja",
): string {
  const pieces = [
    ...buildSpiritPieces(ch, catalog, tr, locale),
    ...buildSpritePieces(ch, catalog, tr, locale),
  ];
  return pieces.length ? JSON.stringify(pieces) : "";
}
