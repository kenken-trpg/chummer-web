/** The chat palette: the rolls a piece carries, and the variables they read. */
import type { Catalog, Character, Derived, InstalledWeapon } from "@/lib/types";
import { attrName, makeT, specTr } from "@/lib/ui-strings";
import { type Locale, type MsgKey } from "@/lib/i18n";
import { skillDefault } from "@/lib/character/skill-default";
import { specializationBonus } from "@/lib/character/skill-specialization";
import { skillLabel } from "@/lib/character/format";
import { ATTR_LIMIT, type LimitKind, skillAttributes, weaponSkill } from "@/lib/vtt-pools";
import { ATTR_ORDER, Section, type UdonariumOptions, slotTag, uiFor, varName } from "./shared";

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
  const weapons = (d.weapons || []).filter(
    (weapon) => weapon.modular_equipped !== false && !weapon.vehicle_id,
  );
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
          `${tr(name)}：${specTr(tr, name, sp)}`,
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
          kn.roll(
            `${Math.max(pool + 2, 0)}B6@{${LIM.mental}}`,
            `${tr(k.name)}：${specTr(tr, k.name, k.spec)}`,
          );
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
