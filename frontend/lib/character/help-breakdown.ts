import type { HelpLine } from "@/components/help/HelpTip";
import type { UiFn } from "@/lib/i18n";
import type { Derived } from "@/lib/types";

type Tr = (name: string) => string;
type Sources = { source: string; value: number }[] | undefined;

const signed = (n: number) => (n > 0 ? `+${n}` : n);

/** Base, modifier and total lines for a value the engine computed as
 *  `base + modifiers`. Each named source gets its own line; whatever they do
 *  not explain — non-stacking bonuses, rules applied outside `<bonus>` — is
 *  one "other" line, so the lines always add up to the total. */
function parts(
  ui: UiFn,
  tr: Tr,
  formula: string,
  base: number,
  total: number,
  sources: Sources,
  note?: string,
): HelpLine[] {
  const lines: HelpLine[] = [{ label: formula }, { label: ui("help.base"), value: base }];
  let rest = total - base;
  for (const row of sources || []) {
    lines.push({ label: tr(row.source), value: signed(row.value) });
    rest -= row.value;
  }
  if (rest !== 0) {
    lines.push({
      label: ui(sources?.length ? "help.bonusOther" : "help.bonus"),
      value: signed(rest),
    });
  }
  lines.push({ label: ui("help.total"), value: total, strong: true });
  if (note) lines.push({ label: note });
  return lines;
}

const up = (n: number) => Math.ceil(n - 1e-9);

export function limitHelp(d: Derived, ui: UiFn, tr: Tr = (n) => n): HelpLine[] {
  const t = d.totals || {};
  const src = d.stat_sources || {};
  const v = (k: string) => Number(t[k] || 0);
  const ess = Math.ceil(Number(d.essence || 0));
  return [
    ...parts(
      ui,
      tr,
      ui("help.limit.physical"),
      up((v("STR") * 2 + v("BOD") + v("REA")) / 3),
      d.limits.physical,
      src.limit_physical,
    ),
    ...parts(
      ui,
      tr,
      ui("help.limit.mental"),
      up((v("LOG") * 2 + v("INT") + v("WIL")) / 3),
      d.limits.mental,
      src.limit_mental,
    ),
    ...parts(
      ui,
      tr,
      ui("help.limit.social"),
      up((v("CHA") * 2 + v("WIL") + ess) / 3),
      d.limits.social,
      src.limit_social,
      ui("help.limit.note"),
    ),
  ];
}

export function conditionHelp(d: Derived, ui: UiFn, tr: Tr = (n) => n): HelpLine[] {
  const t = d.totals || {};
  const src = d.stat_sources || {};
  if (d.condition_monitor.core && d.condition_monitor.vehicle && d.home_node)
    return [
      {
        label: ui("help.cm.vehicle", { name: tr(d.home_node.name) }),
        value: d.condition_monitor.physical,
      },
      {
        label: ui("help.cm.homeNode", { name: tr(d.home_node.name) }),
        value: d.condition_monitor.stun,
      },
    ];
  if (d.condition_monitor.core)
    return [
      ...parts(
        ui,
        tr,
        ui("help.cm.core"),
        8 + up(Number(t.DEP || 0) / 2),
        d.condition_monitor.physical,
        src.cm_physical,
        ui("help.cm.note"),
      ),
      ...(d.home_node
        ? [
            {
              label: ui("help.cm.homeNode", { name: tr(d.home_node.name) }),
              value: d.condition_monitor.stun,
            },
          ]
        : []),
    ];
  return [
    ...parts(
      ui,
      tr,
      ui("help.cm.physical"),
      8 + up(Number(t.BOD || 0) / 2),
      d.condition_monitor.physical,
      src.cm_physical,
    ),
    ...parts(
      ui,
      tr,
      ui("help.cm.stun"),
      8 + up(Number(t.WIL || 0) / 2),
      d.condition_monitor.stun,
      src.cm_stun,
      ui("help.cm.note"),
    ),
  ];
}

export function initiativeHelp(d: Derived, ui: UiFn, tr: Tr = (n) => n): HelpLine[] {
  const t = d.totals || {};
  const src = d.stat_sources || {};
  return [
    ...parts(
      ui,
      tr,
      ui("help.init.value"),
      Number(t.REA || 0) + Number(t.INT || 0),
      d.initiative.value,
      src.initiative,
    ),
    ...parts(
      ui,
      tr,
      ui("help.init.dice"),
      1,
      d.initiative.dice,
      src.initiative_dice,
      ui("help.init.note"),
    ),
  ];
}

/**
 * What the stat line of a weapon means, line by line — and only for the stats
 * this weapon actually has, so a knife does not explain firing modes.
 */
export function weaponHelpLines(
  item: {
    accuracy?: string;
    damage?: string;
    ap?: string;
    mode?: string;
    ammo?: string;
    reach?: string;
    rc?: string;
  },
  ui: UiFn,
): HelpLine[] {
  const lines: HelpLine[] = [];
  const has = (v: string | undefined) => Boolean(v) && v !== "0" && v !== "-";
  if (has(item.accuracy)) lines.push({ label: ui("help.weapon.acc") });
  if (has(item.damage)) lines.push({ label: ui("help.weapon.dv") });
  if (has(item.ap)) lines.push({ label: ui("help.weapon.ap") });
  if (has(item.rc)) lines.push({ label: ui("help.weapon.rc") });
  if (has(item.mode)) lines.push({ label: ui("help.weapon.mode") });
  if (has(item.ammo)) lines.push({ label: ui("help.weapon.ammo") });
  if (has(item.reach)) lines.push({ label: ui("help.weapon.reach") });
  return lines;
}

/**
 * The sheet's weapon table explains its columns once, above the table: every
 * line {@link weaponHelpLines} gives for any of the weapons, each once and in
 * column order.
 */
export function weaponTableHelpLines(
  weapons: Parameters<typeof weaponHelpLines>[0][],
  ui: UiFn,
): HelpLine[] {
  const present = new Set(weapons.flatMap((w) => weaponHelpLines(w, ui)).map((l) => l.label));
  // a weapon with every stat gives the lines in column order
  const every = { accuracy: "1", damage: "1", ap: "1", rc: "1", mode: "1", ammo: "1", reach: "1" };
  return weaponHelpLines(every, ui).filter((l) => present.has(l.label));
}

/**
 * Where a weapon's Accuracy or DV came from, when the engine worked it out
 * from a formula in the data (`Physical` for a melee weapon, `({STR}+2)P`).
 * The sheet gives these under the weapon table's "?" rather than a "?" in
 * each cell, which would squeeze the name column to a letter on a phone.
 * Three of the same spur give the line once.
 */
export function weaponFormulaLines(
  weapons: { name: string; accuracy_formula?: string; damage_formula?: string }[],
  tr: Tr,
  ui: UiFn,
): HelpLine[] {
  const lines = weapons.flatMap((w) =>
    (
      [
        [ui("sheet.col.accuracy"), w.accuracy_formula],
        ["DV", w.damage_formula],
      ] as const
    )
      .filter(([, formula]) => formula)
      .map(([stat, formula]) =>
        ui("help.weapon.formula", { name: tr(w.name), stat, formula: formula! }),
      ),
  );
  return [...new Set(lines)].map((label) => ({ label }));
}
