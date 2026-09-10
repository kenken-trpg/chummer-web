import type { Tab } from "@/lib/character/constants";
import type { MsgKey } from "@/lib/i18n";
import type { Notice, NoticeParam } from "@/lib/engine-notices";
import type { Character } from "@/lib/types";

/**
 * Character-creation legality check. The backend engine already validates the
 * hard rules and drops notices into `derived.errors` / `derived.warnings`;
 * this module consolidates those and adds the *soft* checks the engine
 * deliberately omits — unspent points, leftover karma / nuyen, unused budgets
 * — so the 作成チェック tab is a single place to see whether a build is
 * finished and legal.
 *
 * Nothing here is a sentence: an item carries the dictionary key and the
 * parameters, and `ChecklistPanel` renders it in the reader's locale
 * (`lib/engine-notices.ts`). The engine's own notices pass straight through, which is
 * also why routing an item to the tab that fixes it is now a table lookup on
 * the key rather than a regex over Japanese text.
 */

export type CheckSeverity = "error" | "warn" | "info";

export interface CheckItem {
  id: string;
  severity: CheckSeverity;
  /** Dictionary key + parameters; unknown keys render as themselves. */
  notice: Notice;
  /** Page hint, e.g. "SR5 p.98". */
  ref?: string;
  /** Editor tab this item is actionable on. */
  tab?: Tab;
}

export interface ChecklistSummary {
  errors: number;
  warns: number;
  infos: number;
  ok: boolean;
}

const POINT_ROWS: { key: string; label: MsgKey; tab: Tab; ref: string }[] = [
  { key: "attributes", label: "check.points.attributes", tab: "attrs", ref: "SR5 p.65" },
  { key: "special", label: "check.points.special", tab: "attrs", ref: "SR5 p.65" },
  { key: "skills", label: "check.points.skills", tab: "skills", ref: "SR5 p.87" },
  { key: "skill_groups", label: "check.points.skillGroups", tab: "skills", ref: "SR5 p.90" },
  { key: "knowledge", label: "check.points.knowledge", tab: "skills", ref: "SR5 p.107" },
];

/**
 * Engine notice area -> the tab that fixes it. The area is the second segment
 * of the key (`engine.<area>.<name>`), so a new message lands on the right tab
 * without anyone touching this table. `ware` covers both cyber- and bioware;
 * cyber is the more common half and the two tabs sit next to each other.
 */
const TAB_BY_AREA: Partial<Record<string, Tab>> = {
  priority: "priority",
  settings: "priority",
  meta: "meta",
  attrs: "attrs",
  skills: "skills",
  qualities: "qualities",
  ware: "cyber",
  gear: "gear",
  nuyen: "gear",
  karma: "qualities",
  contacts: "contacts",
  martial: "martial",
  initiation: "initiation",
  submersion: "submersion",
  adept: "adept",
  spells: "spells",
  spirits: "spirits",
  foci: "foci",
  complexforms: "complexforms",
  sprites: "sprites",
};

/** The tab an engine notice is actionable on, from its key. */
export function guessTab(key: string): Tab | undefined {
  const [prefix, area] = key.split(".");
  return prefix === "engine" ? TAB_BY_AREA[area ?? ""] : undefined;
}

function item(
  id: string,
  severity: CheckSeverity,
  key: MsgKey,
  params: Record<string, NoticeParam>,
  extra: { ref?: string; tab?: Tab } = {},
): CheckItem {
  return { id, severity, notice: { key, params }, ...extra };
}

export function buildChecklist(ch: Character): CheckItem[] {
  const d = ch.derived;
  const career = Boolean(ch.career || d.career);
  const items: CheckItem[] = [];

  (d.errors ?? []).forEach((notice, i) => {
    items.push({ id: `err-${i}`, severity: "error", notice, tab: guessTab(notice.key) });
  });
  (d.warnings ?? []).forEach((notice, i) => {
    items.push({ id: `warn-${i}`, severity: "warn", notice, tab: guessTab(notice.key) });
  });

  if (d.needs_mentor) {
    items.push(
      item("needs-mentor", "error", "check.needsMentor", {}, { ref: "SR5 p.78", tab: "qualities" }),
    );
  }
  if (d.needs_paragon) {
    items.push(
      item(
        "needs-paragon",
        "error",
        "check.needsParagon",
        {},
        { ref: "KC p.102", tab: "qualities" },
      ),
    );
  }
  if (d.metagenic && !d.metagenic.balanced) {
    items.push(
      item(
        "metagenic-unbalanced",
        "warn",
        "check.metagenicUnbalanced",
        { positive: d.metagenic.positive, negative: d.metagenic.negative },
        { ref: "RF p.107", tab: "qualities" },
      ),
    );
  }

  if (!career) {
    for (const row of POINT_ROWS) {
      const p = d.points?.[row.key];
      if (!p) continue;
      const left = p.max - p.used;
      if (left > 0) {
        items.push(
          item(
            `left-${row.key}`,
            "info",
            "check.pointsLeft",
            { label: { ui: row.label }, left, used: p.used, max: p.max },
            { ref: row.ref, tab: row.tab },
          ),
        );
      }
    }

    if (d.karma.remaining > 0) {
      items.push(
        item(
          "left-karma",
          "info",
          "check.karmaLeft",
          { left: d.karma.remaining },
          { ref: "SR5 p.98", tab: "qualities" },
        ),
      );
    }
    const neg = d.karma.negative;
    if (neg && neg.max != null && neg.used < neg.max) {
      items.push(
        item(
          "left-neg-karma",
          "info",
          "check.negativeKarmaLeft",
          { left: neg.max - neg.used },
          { ref: "SR5 p.72", tab: "qualities" },
        ),
      );
    }
    if (d.nuyen > 0) {
      items.push(
        item(
          "left-nuyen",
          "info",
          "check.nuyenLeft",
          { nuyen: d.nuyen.toLocaleString("en-US") },
          { ref: "SR5 p.98", tab: "gear" },
        ),
      );
    }

    const cp = d.contact_points;
    if (cp && cp.free - cp.used > 0) {
      items.push(
        item(
          "left-contacts",
          "info",
          "check.contactPointsLeft",
          { left: cp.free - cp.used },
          { ref: "SR5 p.388", tab: "contacts" },
        ),
      );
    }

    const tabs = d.enabled_tabs ?? [];
    const pp = d.power_points;
    if (tabs.includes("adept") && pp && pp.max - pp.used > 1e-6) {
      items.push(
        item(
          "left-power",
          "info",
          "check.powerPointsLeft",
          { left: Number((pp.max - pp.used).toFixed(2)) },
          { ref: "SR5 p.309", tab: "adept" },
        ),
      );
    }
    const sp = d.spell_points;
    if (tabs.includes("spells") && sp && sp.free - sp.used > 0) {
      items.push(
        item(
          "left-spells",
          "info",
          "check.spellSlotsLeft",
          { left: sp.free - sp.used },
          { ref: "SR5 p.70", tab: "spells" },
        ),
      );
    }
    const cf = d.complex_form_points;
    if (tabs.includes("complexforms") && cf && cf.free - cf.used > 0) {
      items.push(
        item(
          "left-cf",
          "info",
          "check.complexFormSlotsLeft",
          { left: cf.free - cf.used },
          { ref: "SR5 p.251", tab: "complexforms" },
        ),
      );
    }
  }

  (d.unimplemented_bonuses ?? []).forEach((b, i) => {
    items.push(
      item(`unimpl-${i}`, "info", "check.unimplementedBonus", {
        source: { tr: b.source },
        tag: b.tag,
      }),
    );
  });

  return items;
}

export function checklistSummary(items: CheckItem[]): ChecklistSummary {
  const errors = items.filter((i) => i.severity === "error").length;
  const warns = items.filter((i) => i.severity === "warn").length;
  const infos = items.filter((i) => i.severity === "info").length;
  return { errors, warns, infos, ok: errors === 0 };
}
