/**
 * Udonarium (ユドナリウム) character export — one piece as a `data.xml`.
 *
 * Udonarium reads a bare `.xml` as well as the `.zip` it ships pieces in; the
 * zip is only needed to carry an image, and this export has none, so it writes
 * the xml directly and the app keeps its zero runtime dependencies.
 *
 * Unlike the Cocofolia export, which hands the table a finished number for
 * every roll, Udonarium's chat palette has variables: `//敏捷力=5` defines one
 * and `{敏捷力}` reads it back. That is the point of the template this follows
 * — the table can retune a pool mid-session without re-exporting. It only
 * works where a roll decomposes into named parts, so this export is a hybrid:
 * attacks, defenses, magic and the Matrix go out as variables, while the skill
 * list and the odd tests go out as plain numbers, exactly as Cocofolia has
 * them. `docs/plans/udonarium-export-plan.md` has the field map.
 *
 * Dice are BCDice `ShadowRun5`, the same dicebot the Cocofolia palette targets.
 */
import type { Catalog, Character, Derived, InstalledWeapon } from "@/lib/types";
import { attrName, makeT } from "@/lib/ui-strings";
import { renderNotice } from "@/lib/engine-notices";
import { type Locale, type MsgKey, type UiFn, translate } from "@/lib/i18n";
import { skillDefault } from "@/lib/character/skill-default";
import { specializationBonus } from "@/lib/character/skill-specialization";
import { skillLabel } from "@/lib/character/format";
import { ATTR_LIMIT, type LimitKind, skillAttributes, weaponSkill } from "@/lib/vtt-pools";

const uiFor =
  (locale: Locale): UiFn =>
  (key, vars) =>
    translate(locale, key, vars);

export type UdonariumOptions = {
  /** Also list every active skill the runner can default on (SR5 p.130),
   *  plus the knowledge skills they actually have. */
  untrained?: boolean;
};

/** The attributes that get a palette variable, in the order Chummer prints
 *  them. MAG and RES only when the character has them. */
const ATTR_ORDER = ["BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL"] as const;

/** `A`, `B`, … `Z`, `AA`, `AB`, … — the suffix that tells one weapon's set of
 *  variables from the next. The template has a fixed A/B pair; a real
 *  character carries as many weapons as it likes. */
export function slotTag(i: number): string {
  let n = i;
  let out = "";
  do {
    out = String.fromCharCode(65 + (n % 26)) + out;
    n = Math.floor(n / 26) - 1;
  } while (n >= 0);
  return out;
}

/** XML text and attribute values. Udonarium's parser is a browser's, so the
 *  five predefined entities are all it knows — and weapon names really do
 *  carry `&` (`Ares S-III Super Squirt`) and quotes. */
export function xmlEscape(s: string): string {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&apos;");
}

/** A palette variable name has to survive being written as `//name=value` and
 *  read back as `{name}`, so it cannot contain the characters that delimit
 *  either. Weapon and spell names go in values, not names, but a skill's
 *  translated name becomes a variable name. */
const varName = (s: string) => String(s ?? "").replace(/[{}=/\s]+/g, "");

type Lines = string[];

/** Both halves of the palette: the rolls that reference variables and the
 *  definitions that give them values. They are emitted per section — rolls
 *  first, then the `//` block they read — so a section can be dropped whole
 *  when the character has nothing in it. */
class Section {
  rolls: Lines = [];
  defs: Lines = [];
  def(name: string, value: string | number) {
    this.defs.push(`//${varName(name)}=${value}`);
  }
  roll(expr: string, label: string) {
    this.rolls.push(`${expr} ${label}`);
  }
  get empty() {
    return !this.rolls.length;
  }
  text(heading?: string) {
    const parts = [heading, this.rolls.join("\n"), this.defs.join("\n")].filter(Boolean);
    return parts.join("\n\n");
  }
}

/** Newline-separated BCDice ShadowRun5 commands for Udonarium's chat palette. */
export function buildUdonariumPalette(
  ch: Character,
  catalog: Catalog,
  tr: (n: string) => string,
  locale: Locale = "ja",
  opts: UdonariumOptions = {},
): string {
  const ui = uiFor(locale);
  const t = makeT(catalog, locale);
  const d: Derived = ch.derived;
  const totals: Record<string, number> = d.totals || {};
  const at = (k: string) => totals[k] || 0;
  const lim = (k: Exclude<LimitKind, null>) => d.limits?.[k] ?? 0;
  const tm = d.test_mods || {};
  const tabs = d.enabled_tabs || [];
  const skillPool = (name: string) => (d.skill_totals?.[name] || 0) + (d.skill_bonus?.[name] || 0);

  const A = (k: string) => varName(attrName(k, t));
  const LIM: Record<Exclude<LimitKind, null>, string> = {
    physical: varName(ui("udo.varLimPhysical")),
    mental: varName(ui("udo.varLimMental")),
    social: varName(ui("udo.varLimSocial")),
  };
  const armorVar = varName(ui("udo.varArmor"));

  const blocks: string[] = [];

  // --- the core: attributes, limits and armour as variables ---------------
  const core = new Section();
  const init = d.initiative || { value: 0, dice: 1 };
  core.roll(`${init.dice}D6+${init.value}`, ui("coco.initiative"));
  for (const k of ATTR_ORDER) core.def(A(k), at(k));
  for (const k of ["MAG", "RES"] as const) if (at(k) > 0) core.def(A(k), at(k));
  core.def(LIM.physical, lim("physical"));
  core.def(LIM.mental, lim("mental"));
  core.def(LIM.social, lim("social"));
  core.def(armorVar, d.armor ?? 0);
  blocks.push(core.text());

  // --- weapons: attack = skill + AGI + mod, limit = Accuracy --------------
  // Ranged and melee are split because the template's variable sets are, and
  // because a melee weapon's Accuracy is the Physical limit rather than a
  // printed number.
  // Two cyberarms carry two sets of Spurs, and Chummer saves one row each, so
  // a real character hands this four identical weapons. They roll the same
  // test, and four copies of it is four variable sets nobody will tune
  // separately, so rows that agree on everything the palette shows collapse
  // into one.
  const distinct = (rows: InstalledWeapon[]) => {
    const seen = new Set<string>();
    return rows.filter((w) => {
      const key = [w.name, w.accuracy, w.damage, w.ap, w.mode, w.reach, w.useskill, w.category]
        .map((v) => String(v ?? ""))
        .join("\u0000");
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    });
  };
  const weapons = d.weapons || [];
  const ranged = distinct(weapons.filter((w) => (w.type || "") !== "Melee"));
  const melee = distinct(weapons.filter((w) => (w.type || "") === "Melee"));

  const weaponBlock = (
    rows: InstalledWeapon[],
    keys: { weapon: MsgKey; acc: MsgKey; skill: MsgKey; mod: MsgKey },
    attr: string,
    heading: MsgKey,
  ) => {
    if (!rows.length) return;
    const sec = new Section();
    rows.forEach((w, i) => {
      const idx = slotTag(i);
      const vw = varName(ui(keys.weapon, { idx }));
      const vacc = varName(ui(keys.acc, { idx }));
      const vsk = varName(ui(keys.skill, { idx }));
      const vmod = varName(ui(keys.mod, { idx }));
      const acc = String(w.accuracy || "").trim();
      // Melee Accuracy is quoted as the Physical limit; keep it a reference so
      // retuning the limit retunes the weapon.
      const accValue = /^\d+$/.test(acc) ? acc : `{${LIM.physical}}`;
      sec.roll(`({${A(attr)}}+{${vsk}}+{${vmod}}+0)B6@{${vacc}}`, `{${vw}}`);
      const info = [
        w.damage && `DV${w.damage}`,
        w.ap && `AP${w.ap}`,
        w.reach && ui("coco.reach", { reach: w.reach }),
        // a melee row carries `0` where a firearm carries SA/BF/FA
        w.mode && w.mode !== "0" ? w.mode : "",
      ]
        .filter(Boolean)
        .join("/");
      sec.def(vw, `${tr(w.name)}${info ? ` [${info}]` : ""}`);
      sec.def(vacc, accValue);
      sec.def(vsk, skillPool(weaponSkill(w)));
      sec.def(vmod, 0);
    });
    blocks.push(sec.text(ui(heading)));
  };

  weaponBlock(
    ranged,
    {
      weapon: "udo.varRangedWeapon",
      acc: "udo.varRangedAcc",
      skill: "udo.varRangedSkill",
      mod: "udo.varRangedMod",
    },
    "AGI",
    "udo.secRanged",
  );
  weaponBlock(
    melee,
    {
      weapon: "udo.varMeleeWeapon",
      acc: "udo.varMeleeAcc",
      skill: "udo.varMeleeSkill",
      mod: "udo.varMeleeMod",
    },
    "AGI",
    "udo.secMelee",
  );

  // --- defense and damage resistance -------------------------------------
  const def = new Section();
  const dodge = tm.dodge || 0;
  def.roll(`({${A("REA")}}+{${A("INT")}}+${dodge})B6`, ui("coco.defense"));
  const meleeDef = Math.max(skillPool("Unarmed Combat"), skillPool("Blades"), skillPool("Clubs"));
  def.roll(
    `({${A("REA")}}+{${A("INT")}}+${meleeDef + dodge})B6@{${LIM.physical}}`,
    ui("coco.meleeDefense"),
  );
  def.roll(`({${A("REA")}}+{${A("INT")}}+{${A("WIL")}}+${dodge})B6`, ui("coco.fullDefense"));
  def.roll(`({${A("BOD")}}+{${armorVar}}+0)B6`, ui("udo.damageResist"));
  blocks.push(def.text(ui("udo.secDefense")));

  // --- the skill list, as plain numbers ----------------------------------
  const { skillAttr, specSwap } = skillAttributes(catalog, d);
  const specs = { ...ch.skill_specializations, ...d.skill_specializations };
  const skills = new Section();
  const numericRoll = (pool: number, label: string, l: LimitKind) =>
    skills.roll(`${Math.max(pool, 0)}B6${l ? `@{${LIM[l]}}` : ""}`, label);
  Object.entries(d.skill_totals || {})
    .filter(([, r]) => r > 0)
    .sort((a, b) => tr(a[0]).localeCompare(tr(b[0]), locale))
    .forEach(([name, rating]) => {
      const attr = skillAttr[name] || "";
      const limit = ATTR_LIMIT[attr] ?? null;
      const bonus = d.skill_bonus?.[name] || 0;
      numericRoll(rating + at(attr) + bonus, skillLabel(name, tr), limit);
      const sp = specs[name];
      const specBonus = specializationBonus(d, name);
      if (sp && specBonus > 0) {
        const swap = specSwap[name];
        const swapped = swap && swap.spec === sp ? swap.attribute : "";
        const specAttr = swapped || attr;
        numericRoll(
          rating + at(specAttr) + bonus + specBonus,
          `${tr(name)}：${tr(sp)}`,
          swapped ? (ATTR_LIMIT[specAttr] ?? null) : limit,
        );
      }
    });
  if (!skills.empty) blocks.push(skills.text(ui("udo.secSkills")));

  if (opts.untrained) {
    const un = new Section();
    (catalog.skills?.skills || [])
      .filter((s) => !s.exotic && !((d.skill_totals?.[s.name] || 0) > 0))
      .map((s) => {
        const attr = skillAttr[s.name] || s.attribute;
        return { s, attr, def: skillDefault({ ...s, attribute: attr }, d) };
      })
      .filter((row) => !row.def.blocked)
      .sort((a, b) => tr(a.s.name).localeCompare(tr(b.s.name), locale))
      .forEach(({ s, attr, def: dd }) => {
        if (dd.blocked) return;
        const l = ATTR_LIMIT[attr] ?? null;
        un.roll(`${Math.max(dd.pool, 0)}B6${l ? `@{${LIM[l]}}` : ""}`, tr(s.name));
      });
    if (!un.empty) blocks.push(un.text(ui("udo.secUntrained")));

    const kn = new Section();
    (d.knowledge_skills || [])
      .filter((k) => k.rating > 0)
      .sort((a, b) => tr(a.name).localeCompare(tr(b.name), locale))
      .forEach((k) => {
        const pool = k.rating + at(k.attribute);
        kn.roll(`${Math.max(pool, 0)}B6@{${LIM.mental}}`, tr(k.name));
        if (k.spec)
          kn.roll(`${Math.max(pool + 2, 0)}B6@{${LIM.mental}}`, `${tr(k.name)}：${tr(k.spec)}`);
      });
    if (!kn.empty) blocks.push(kn.text(ui("udo.secKnowledge")));
  }

  // --- magic: the template's メイジ用 block -------------------------------
  if (tabs.includes("spells") || tabs.includes("spirits")) {
    const mag = new Section();
    const magVar = A("MAG");
    const casting: [string, string][] = [
      ["Spellcasting", "udo.castSpellcasting"],
      ["Ritual Spellcasting", "udo.castRitual"],
      ["Alchemy", "udo.castAlchemy"],
      ["Summoning", "udo.castSummoning"],
      ["Binding", "udo.castBinding"],
      ["Banishing", "udo.castBanishing"],
    ];
    const used = new Set<string>();
    for (const [skill, key] of casting) {
      if (skillPool(skill) <= 0) continue;
      const v = varName(tr(skill));
      mag.roll(`({${magVar}}+{${v}}+0)B6`, ui(key as MsgKey));
      used.add(skill);
    }
    // each spell on its own line, with its own modifier to tune
    (d.spells || [])
      .filter((s) => (s.kind || "spell") === "spell")
      .forEach((s, i) => {
        const idx = slotTag(i);
        const vs = varName(ui("udo.varSpell", { idx }));
        const vmod = varName(ui("udo.varSpellMod", { idx }));
        const skill = s.useskill || "Spellcasting";
        const v = varName(tr(skill));
        mag.roll(`({${magVar}}+{${v}}+{${vmod}}+0)B6`, `{${vs}}`);
        mag.defs.push(`//${vs}=${tr(s.name)}${s.dv ? ` [DV${s.dv}]` : ""}`);
        mag.def(vmod, 0);
        if (!used.has(skill) && skillPool(skill) > 0) used.add(skill);
      });
    if (skillPool("Assensing") > 0) {
      const v = varName(tr("Assensing"));
      mag.roll(`({${A("INT")}}+{${v}}+0)B6@{${A("CHA")}}`, ui("udo.assensing"));
      used.add("Assensing");
    }
    if (d.drain_resist && tabs.includes("spells"))
      mag.roll(
        `${Math.max(d.drain_resist.pool, 0)}B6`,
        ui("coco.drainResist", { attrs: d.drain_resist.attrs }),
      );
    for (const skill of used) mag.def(varName(tr(skill)), skillPool(skill));
    if (!mag.empty) blocks.push(mag.text(ui("udo.secMagic")));
  }

  // --- the Matrix: the template's デッカー用 block ------------------------
  // a commlink with a dongle can hack too (DT p.61) — after a deck or a living persona
  const donglelink = d.commlink && (d.commlink.attack || d.commlink.sleaze) ? d.commlink : null;
  const persona = d.cyberdeck || d.living_persona || donglelink;
  if (persona) {
    const mx = new Section();
    const vAtk = varName(ui("udo.varAttack"));
    const vSlz = varName(ui("udo.varSleaze"));
    const vDp = varName(ui("udo.varDataProc"));
    const vFw = varName(ui("udo.varFirewall"));
    const vHack = varName(tr("Hacking"));
    const vCyb = varName(tr("Cybercombat"));
    const vComp = varName(tr("Computer"));
    const mi = d.matrix_initiative;
    if (mi) {
      mx.roll(`${mi.cold_dice}D6+${mi.value}`, ui("coco.matrixInitCold"));
      mx.roll(`${mi.hot_dice}D6+${mi.value}`, ui("coco.matrixInitHot"));
    }
    mx.roll(`({${A("LOG")}}+{${vHack}}+0)B6@{${vSlz}}`, ui("coco.hackOnTheFly"));
    mx.roll(`({${A("LOG")}}+{${vCyb}}+0)B6@{${vAtk}}`, ui("coco.bruteForce"));
    mx.roll(`({${A("LOG")}}+{${vCyb}}+0)B6@{${vAtk}}`, ui("coco.dataSpike"));
    mx.roll(`({${A("INT")}}+{${vComp}}+0)B6@{${vDp}}`, ui("coco.matrixPerception"));
    mx.roll(`({${A("WIL")}}+{${vFw}}+0)B6`, ui("coco.matrixDefense", { int: at("INT") }));
    if (d.fade_resist && tabs.includes("complexforms"))
      mx.roll(
        `${Math.max(d.fade_resist.pool, 0)}B6`,
        ui("coco.fadeResist", { attrs: d.fade_resist.attrs }),
      );
    mx.def(vAtk, persona.attack ?? 0);
    mx.def(vSlz, persona.sleaze ?? 0);
    mx.def(vDp, persona.dataprocessing ?? 0);
    mx.def(vFw, persona.firewall ?? 0);
    mx.def(vHack, skillPool("Hacking"));
    mx.def(vCyb, skillPool("Cybercombat"));
    mx.def(vComp, skillPool("Computer"));
    blocks.push(mx.text(ui("udo.secMatrix")));
  }

  // --- complex forms, as plain numbers -----------------------------------
  // The engine resolves each one's threading test (`test.pool`) and its limit
  // (the Level it is threaded at), so there is nothing left to decompose.
  if (tabs.includes("complexforms")) {
    const cf = new Section();
    for (const f of d.complex_forms || []) {
      const test = f.test;
      if (!test) continue;
      const limit = test.limit || f.level || 0;
      cf.roll(
        `${Math.max(test.pool || 0, 0)}B6${limit ? `@${limit}` : ""}`,
        `${tr(f.name)}${f.fv ? ` [FV${f.fv}]` : ""}`,
      );
    }
    if (!cf.empty) blocks.push(cf.text(ui("udo.secComplexForms")));
  }

  // --- the odd tests, as plain numbers -----------------------------------
  const tests = new Section();
  const numeric = (pool: number, label: string, l: LimitKind = null) =>
    tests.roll(`${Math.max(pool, 0)}B6${l ? `@{${LIM[l]}}` : ""}`, label);
  numeric(at("WIL") + at("CHA") + (tm.composure || 0), ui("coco.composure"), "social");
  numeric(at("INT") + at("CHA") + (tm.judge_intentions || 0), ui("coco.judge"), "social");
  numeric(at("LOG") + at("WIL") + (tm.memory || 0), ui("coco.memory"), "mental");
  numeric(at("STR") + at("BOD"), ui("coco.lifting"), "physical");
  tests.roll("2D6", ui("coco.scatterThrown"));
  tests.roll("4D6", ui("coco.scatterLaunched"));
  blocks.push(tests.text(ui("udo.secTests")));

  blocks.push([ui("udo.noteEdge"), ui("udo.noteDice")].join("\n"));

  return blocks.join("\n\n");
}

/** `<data name="…" type="numberResource" currentValue="v">max</data>` */
const resource = (name: string, current: number, max: number) =>
  `        <data name="${xmlEscape(name)}" type="numberResource" currentValue="${current}">${max}</data>`;

/**
 * Where a piece lands on the table.
 *
 * Udonarium drops a piece exactly where the file says, so writing them all at
 * one spot leaves a party loaded one file at a time in a single stack.
 * Hashing the name spreads them over a small grid and keeps the export
 * reproducible — the same character always writes the same file — putting two
 * pieces in one place only when their names collide.
 */
function spotFor(name: string): { x: number; y: number } {
  let h = 0;
  for (const c of name || "") h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return { x: 200 + (h % 6) * 100, y: 50 + (Math.floor(h / 6) % 4) * 100 };
}

/**
 * The envelope every piece shares: the placement and display attributes, the
 * name, the `detail` panels of counters, and the chat palette.
 *
 * A runner, a bound spirit and a registered sprite differ only in what goes
 * in the panels and the palette, so the XML around them is written once.
 */
function pieceXml(piece: {
  name: string;
  panels: { title: string; rows: string[] }[];
  buffLabel: string;
  palette: string;
}): string {
  const spot = spotFor(piece.name);
  const panels = piece.panels
    .filter((p) => p.rows.length)
    .map((p) => `      <data name="${xmlEscape(p.title)}">\n${p.rows.join("\n")}\n      </data>`)
    .join("\n");
  return `<?xml version="1.0" encoding="UTF-8"?>
<character location.name="table" location.x="${spot.x}" location.y="${spot.y}" posZ="0" rotate="0" roll="0" isAltitudeIndicate="true" isLock="false" isDropShadow="false" hideInventory="false" nonTalkFlag="false" overViewWidth="270" overViewMaxHeight="250" specifyKomaImageFlag="false" komaImageHeignt="100" chatColorCode.0="#000000" chatColorCode.1="#FF0000" chatColorCode.2="#0099FF" syncDummyCounter="0">
  <data name="character">
    <data name="image">
      <data type="image" name="imageIdentifier">none_icon</data>
    </data>
    <data name="common">
      <data name="name">${xmlEscape(piece.name)}</data>
      <data name="size">2</data>
      <data name="altitude">0</data>
    </data>
    <data name="detail">
${panels}
    </data>
    <data name="buff">
      <data name="${xmlEscape(piece.buffLabel)}"></data>
    </data>
  </data>
  <chat-palette dicebot="ShadowRun5">${xmlEscape(piece.palette)}</chat-palette>
</character>
`;
}

/**
 * The whole `data.xml` for one Udonarium character piece.
 *
 * The `detail` panel carries only the resources the table clicks during play —
 * the condition monitors, Edge and the movement left this turn. Everything the
 * character *is* lives in the palette's variables, which is where the table can
 * reach it, so it is not duplicated here.
 */
export function buildUdonariumXml(
  ch: Character,
  catalog: Catalog,
  tr: (n: string) => string,
  locale: Locale = "ja",
  opts: UdonariumOptions = {},
): string {
  const ui = uiFor(locale);
  const d: Derived = ch.derived;
  const cm = d.condition_monitor || { physical: 0, stun: 0 };
  const edge = d.totals?.EDG || 0;
  // A persona's Matrix condition monitor is 8 + half its Device Rating,
  // rounded up (SR5 p.228) — and a technomancer has one too, off the living
  // persona, which is why this asks the same question the palette's Matrix
  // block does rather than only looking for a deck.
  const donglelink = d.commlink && (d.commlink.attack || d.commlink.sleaze) ? d.commlink : null;
  const persona = d.cyberdeck || d.living_persona || donglelink;
  const matrixCm = persona ? 8 + Math.ceil((persona.device_rating || 1) / 2) : 0;
  // `movement.run` is Chummer's metres-per-Complex-Action string; a rating
  // modifier can leave it non-numeric, and then the piece starts at 0.
  const parsed = Number.parseInt(String(d.movement?.run ?? ""), 10);
  const run = Number.isFinite(parsed) ? parsed : 0;

  return pieceXml({
    name: ch.name || tr(ch.metatype) || "Runner",
    buffLabel: ui("udo.panelBuff"),
    palette: buildUdonariumPalette(ch, catalog, tr, locale, opts),
    panels: [
      {
        title: ui("udo.panelStatus"),
        rows: [
          resource(ui("coco.initiative"), 0, 0),
          resource(ui("coco.edge"), edge, edge),
          resource(ui("udo.movementLeft"), run, run),
        ],
      },
      {
        title: ui("udo.panelCm"),
        rows: [
          resource(ui("coco.cmPhysical"), 0, cm.physical),
          resource(ui("coco.cmStun"), 0, cm.stun),
          ...(matrixCm ? [resource(ui("coco.cmMatrix"), 0, matrixCm)] : []),
          woundTrack(ui, cm.physical, cm.stun),
        ],
      },
    ],
  });
}

/** The box-ticking damage track the template keeps beside the monitors. */
function woundTrack(ui: UiFn, physical: number, stun: number): string {
  const boxes = (n: number) => "[]".repeat(Math.max(n, 0));
  const text = [
    `${ui("udo.woundPhysical")}${boxes(physical)}`,
    `${ui("udo.woundStun")}${boxes(stun)}`,
  ].join("\n");
  return `        <data name="${xmlEscape(ui("udo.woundTrack"))}" type="markdown">${xmlEscape(text)}</data>`;
}

// --- bound spirits and registered sprites, as their own pieces -------------
// A bound spirit or a registered sprite is dropped on the table and run like
// anything else there, so it gets a piece of its own — the same thing the
// Cocofolia export does with `buildCocofoliaConjured`.
//
// Force (or Level) is the variable worth having here. Every limit on the
// sheet is it, and raising it at the table is the one adjustment that comes
// up, so the rolls reference it rather than the number it happened to be at
// export time. The attributes it already determined stay as they are: nothing
// recomputes them when the variable moves.

const SPIRIT_ATTRS = ["BOD", "AGI", "REA", "STR", "CHA", "INT", "LOG", "WIL"] as const;

/** One piece per bound spirit. Skill test = Force + linked attribute,
 *  limit = Force (SR5 p.395). */
export function buildSpiritPieces(
  ch: Character,
  catalog: Catalog,
  tr: (n: string) => string,
  locale: Locale = "ja",
): { name: string; xml: string }[] {
  const ui = uiFor(locale);
  const t = makeT(catalog, locale);
  const A = (k: string) => varName(attrName(k, t));
  const forceVar = varName(ui("udo.varForce"));

  return (ch.derived.spirits || [])
    .filter((s) => s.bound)
    .map((s) => {
      const a = s.attributes || {};
      const force = s.force || 1;
      const sec = new Section();

      sec.roll(`2D6+${a.INI ?? force * 2}`, ui("coco.initiative"));
      for (const sk of s.skills || []) {
        const v = varName(tr(sk.name));
        const attr = sk.attribute || "";
        sec.roll(
          `({${attr ? A(attr) : forceVar}}+{${v}}+0)B6@{${forceVar}}`,
          skillLabel(sk.name, tr),
        );
      }
      sec.roll(`({${A("REA")}}+{${A("INT")}}+0)B6`, ui("coco.defense"));
      // Immunity to Normal Weapons: Force twice over, on top of Body.
      sec.roll(`({${A("BOD")}}+{${forceVar}}+{${forceVar}})B6`, ui("coco.immunityResist"));
      sec.roll(`({${forceVar}}+{${forceVar}})B6`, ui("coco.resistBanishing"));

      sec.def(forceVar, force);
      for (const k of SPIRIT_ATTRS) if ((a[k] || 0) > 0) sec.def(A(k), a[k]);
      for (const sk of s.skills || []) sec.def(varName(tr(sk.name)), sk.rating || force);

      const powers = [...(s.powers || []), ...(s.optionalpowers || [])].map((p) => tr(p.name));
      const notes = [
        ui("coco.spiritName", {
          name: tr(s.name),
          role: s.role_label ? renderNotice(s.role_label, ui) : s.role || ui("coco.spirit"),
          force,
        }),
        ui("coco.spiritMemo", { services: s.services }),
        powers.length ? ui("coco.powers", { list: powers.join(ui("common.listSep")) }) : "",
        s.weaknesses?.length
          ? ui("coco.weaknesses", { list: s.weaknesses.map(tr).join(ui("common.listSep")) })
          : "",
        ui("coco.spiritNote"),
      ].filter(Boolean);

      const physCM = 8 + Math.ceil((a.BOD || 0) / 2);
      const stunCM = 8 + Math.ceil((a.WIL || 0) / 2);
      return {
        name: `${tr(s.name)} F${force}`,
        xml: pieceXml({
          name: `${tr(s.name)} F${force}`,
          buffLabel: ui("udo.panelBuff"),
          palette: [notes.join("\n"), sec.text()].join("\n\n"),
          panels: [
            {
              title: ui("udo.panelStatus"),
              rows: [
                resource(ui("coco.initiative"), 0, 0),
                resource(ui("udo.varForce"), force, force),
                resource(ui("udo.services"), s.services || 0, s.services || 0),
              ],
            },
            {
              title: ui("udo.panelCm"),
              rows: [
                resource(ui("coco.cmPhysical"), 0, physCM),
                resource(ui("coco.cmStun"), 0, stunCM),
                woundTrack(ui, physCM, stunCM),
              ],
            },
          ],
        }),
      };
    });
}

/** One piece per registered sprite. Skill test = Level + skill, limit = Level
 *  (SR5 p.254). */
export function buildSpritePieces(
  ch: Character,
  _catalog: Catalog,
  tr: (n: string) => string,
  locale: Locale = "ja",
): { name: string; xml: string }[] {
  const ui = uiFor(locale);
  const levelVar = varName(ui("udo.varLevel"));
  const vFw = varName(ui("udo.varFirewall"));

  return (ch.derived.sprites || [])
    .filter((s) => s.registered)
    .map((s) => {
      const level = s.level || 1;
      const m = s.matrix || { attack: 0, sleaze: 0, dataprocessing: 0, firewall: 0, initiative: 0 };
      const sec = new Section();

      sec.roll(`${level}D6+${m.initiative || level * 2}`, ui("coco.initiative"));
      for (const sk of s.skills || []) {
        const v = varName(tr(sk.name));
        sec.roll(`({${levelVar}}+{${v}}+0)B6@{${levelVar}}`, skillLabel(sk.name, tr));
      }
      sec.roll(`({${vFw}}+{${levelVar}}+0)B6`, ui("coco.matrixDefensePlain"));
      sec.roll(`({${levelVar}}+{${levelVar}})B6`, ui("coco.resistDerez"));

      sec.def(levelVar, level);
      sec.def(varName(ui("udo.varAttack")), m.attack);
      sec.def(varName(ui("udo.varSleaze")), m.sleaze);
      sec.def(varName(ui("udo.varDataProc")), m.dataprocessing);
      sec.def(vFw, m.firewall);
      for (const sk of s.skills || []) sec.def(varName(tr(sk.name)), sk.rating || level);

      const powers = (s.powers || []).map((p) => tr(p.name));
      const notes = [
        ui("coco.spriteLevel", { name: tr(s.name), level }),
        ui("coco.spriteMemo", { services: s.services }),
        powers.length ? ui("coco.powers", { list: powers.join(ui("common.listSep")) }) : "",
        ui("coco.spriteNote"),
      ].filter(Boolean);

      const cm = 8 + Math.ceil(level / 2);
      const name = `${tr(s.name)} L${level}`;
      return {
        name,
        xml: pieceXml({
          name,
          buffLabel: ui("udo.panelBuff"),
          palette: [notes.join("\n"), sec.text()].join("\n\n"),
          panels: [
            {
              title: ui("udo.panelStatus"),
              rows: [
                resource(ui("coco.initiative"), 0, 0),
                resource(ui("udo.varLevel"), level, level),
                resource(ui("udo.tasks"), s.services || 0, s.services || 0),
              ],
            },
            {
              title: ui("udo.panelCm"),
              rows: [resource(ui("coco.cmMatrix"), 0, cm)],
            },
          ],
        }),
      };
    });
}

/**
 * Every bound spirit and registered sprite, one `.xml` per piece, ready for
 * one zip. Udonarium reads every xml an archive holds, so the whole retinue
 * goes on the table in one drop. Empty when the character has none.
 */
export function buildUdonariumConjured(
  ch: Character,
  catalog: Catalog,
  tr: (n: string) => string,
  locale: Locale = "ja",
): { name: string; content: string }[] {
  const pieces = [
    ...buildSpiritPieces(ch, catalog, tr, locale),
    ...buildSpritePieces(ch, catalog, tr, locale),
  ];
  // The entry names are Udonarium's to read, not the table's to see — the
  // piece's own name comes from inside the xml — so they are numbered rather
  // than named after a spirit, which keeps them ASCII and unique.
  return pieces.map((p, i) => ({ name: i ? `data_${i}.xml` : "data.xml", content: p.xml }));
}
