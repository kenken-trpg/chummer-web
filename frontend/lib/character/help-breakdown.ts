import type { HelpLine } from "@/components/help/HelpTip";
import type { UiFn } from "@/lib/i18n";
import type { Derived } from "@/lib/types";

/** Base, modifier and total lines for a value the engine computed as
 *  `base + modifiers`: the modifier is whatever the base does not explain. */
function parts(ui: UiFn, formula: string, base: number, total: number, note?: string): HelpLine[] {
  const bonus = total - base;
  const lines: HelpLine[] = [{ label: formula }, { label: ui("help.base"), value: base }];
  if (bonus !== 0) lines.push({ label: ui("help.bonus"), value: bonus > 0 ? `+${bonus}` : bonus });
  lines.push({ label: ui("help.total"), value: total, strong: true });
  if (note) lines.push({ label: note });
  return lines;
}

const up = (n: number) => Math.ceil(n - 1e-9);

export function limitHelp(d: Derived, ui: UiFn): HelpLine[] {
  const t = d.totals || {};
  const v = (k: string) => Number(t[k] || 0);
  const ess = Number(d.essence || 0);
  return [
    ...parts(
      ui,
      ui("help.limit.physical"),
      up((v("BOD") * 2 + v("AGI") + v("REA") + v("STR")) / 3),
      d.limits.physical,
    ),
    ...parts(
      ui,
      ui("help.limit.mental"),
      up((v("LOG") * 2 + v("INT") + v("WIL")) / 3),
      d.limits.mental,
    ),
    ...parts(
      ui,
      ui("help.limit.social"),
      up((v("CHA") * 2 + v("WIL") + ess) / 3),
      d.limits.social,
      ui("help.limit.note"),
    ),
  ];
}

export function conditionHelp(d: Derived, ui: UiFn): HelpLine[] {
  const t = d.totals || {};
  return [
    ...parts(
      ui,
      ui("help.cm.physical"),
      8 + up(Number(t.BOD || 0) / 2),
      d.condition_monitor.physical,
    ),
    ...parts(
      ui,
      ui("help.cm.stun"),
      8 + up(Number(t.WIL || 0) / 2),
      d.condition_monitor.stun,
      ui("help.cm.note"),
    ),
  ];
}

export function initiativeHelp(d: Derived, ui: UiFn): HelpLine[] {
  const t = d.totals || {};
  return [
    ...parts(
      ui,
      ui("help.init.value"),
      Number(t.REA || 0) + Number(t.INT || 0),
      d.initiative.value,
    ),
    ...parts(ui, ui("help.init.dice"), 1, d.initiative.dice, ui("help.init.note")),
  ];
}
