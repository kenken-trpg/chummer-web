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
  const ess = Number(d.essence || 0);
  return [
    ...parts(
      ui,
      tr,
      ui("help.limit.physical"),
      up((v("BOD") * 2 + v("AGI") + v("REA") + v("STR")) / 3),
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
