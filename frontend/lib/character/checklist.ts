import type { Tab } from "@/lib/character/constants";
import type { Character } from "@/lib/types";

/**
 * Character-creation legality check. The backend engine already validates the
 * hard rules and drops human-readable messages into `derived.errors` /
 * `derived.warnings`; this module consolidates those and adds the *soft*
 * checks the engine deliberately omits — unspent points, leftover karma /
 * nuyen, unused budgets — so the "作成チェック" tab is a single place to see
 * whether a build is finished and legal. Rule text stays Japanese here (it
 * mirrors the engine); only the panel chrome is localised.
 */

export type CheckSeverity = "error" | "warn" | "info";

export interface CheckItem {
  id: string;
  severity: CheckSeverity;
  message: string;
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

const POINT_ROWS: { key: string; label: string; tab: Tab; ref: string }[] = [
  { key: "attributes", label: "能力値点", tab: "attrs", ref: "SR5 p.65" },
  { key: "special", label: "特殊能力値点", tab: "attrs", ref: "SR5 p.65" },
  { key: "skills", label: "技能点", tab: "skills", ref: "SR5 p.87" },
  { key: "skill_groups", label: "技能グループ点", tab: "skills", ref: "SR5 p.90" },
  { key: "knowledge", label: "知識技能点", tab: "skills", ref: "SR5 p.107" },
];

const TAB_RULES: [RegExp, Tab][] = [
  [/自然上限|エッセンス|能力値/, "attrs"],
  [/技能/, "skills"],
  [/資質|メンター|カルマが不足|不利な資質/, "qualities"],
  [/ニューエン|容量超過|入手|アベイラ|デバイス.?レーティング|グレード/, "gear"],
  [/バイオウェア|サイバーウェア|装着できません/, "cyber"],
  [/パワー点/, "adept"],
  [/術式|スペル|式典/, "spells"],
  [/精霊/, "spirits"],
  [/複合体/, "complexforms"],
  [/優先度|メタ(?!ジェネ)/, "meta"],
];

/** Best-effort routing of an engine message to the tab that fixes it. */
export function guessTab(message: string): Tab | undefined {
  for (const [re, tab] of TAB_RULES) if (re.test(message)) return tab;
  return undefined;
}

export function buildChecklist(ch: Character): CheckItem[] {
  const d = ch.derived;
  const career = Boolean(ch.career || d.career);
  const items: CheckItem[] = [];

  (d.errors ?? []).forEach((message, i) => {
    items.push({ id: `err-${i}`, severity: "error", message, tab: guessTab(message) });
  });
  (d.warnings ?? []).forEach((message, i) => {
    items.push({ id: `warn-${i}`, severity: "warn", message, tab: guessTab(message) });
  });

  if (d.needs_mentor) {
    items.push({
      id: "needs-mentor",
      severity: "error",
      message: "メンター精霊／イディオットが未選択です",
      ref: "SR5 p.78",
      tab: "qualities",
    });
  }
  if (d.metagenic && !d.metagenic.balanced) {
    items.push({
      id: "metagenic-unbalanced",
      severity: "warn",
      message: `メタジェネティック資質のカルマ収支が不均衡です（＋${d.metagenic.positive} / −${d.metagenic.negative}）`,
      ref: "RF p.107",
      tab: "qualities",
    });
  }

  if (!career) {
    for (const row of POINT_ROWS) {
      const p = d.points?.[row.key];
      if (!p) continue;
      const left = p.max - p.used;
      if (left > 0) {
        items.push({
          id: `left-${row.key}`,
          severity: "info",
          message: `${row.label}が ${left} 点余っています（使用 ${p.used} / ${p.max}）`,
          ref: row.ref,
          tab: row.tab,
        });
      }
    }

    if (d.karma.remaining > 0) {
      items.push({
        id: "left-karma",
        severity: "info",
        message: `カルマが ${d.karma.remaining} 点余っています`,
        ref: "SR5 p.98",
        tab: "qualities",
      });
    }
    const neg = d.karma.negative;
    if (neg && neg.max != null && neg.used < neg.max) {
      items.push({
        id: "left-neg-karma",
        severity: "info",
        message: `不利な資質であと ${neg.max - neg.used} カルマ分を取得できます`,
        ref: "SR5 p.72",
        tab: "qualities",
      });
    }
    if (d.nuyen > 0) {
      items.push({
        id: "left-nuyen",
        severity: "info",
        message: `ニューエンが ${d.nuyen.toLocaleString("en-US")}¥ 残っています`,
        ref: "SR5 p.98",
        tab: "gear",
      });
    }

    const cp = d.contact_points;
    if (cp && cp.free - cp.used > 0) {
      items.push({
        id: "left-contacts",
        severity: "info",
        message: `コンタクト値が ${cp.free - cp.used} 点未使用です`,
        ref: "SR5 p.388",
        tab: "contacts",
      });
    }

    const tabs = d.enabled_tabs ?? [];
    const pp = d.power_points;
    if (tabs.includes("adept") && pp && pp.max - pp.used > 1e-6) {
      items.push({
        id: "left-power",
        severity: "info",
        message: `パワー点が ${Number((pp.max - pp.used).toFixed(2))} 点未使用です`,
        ref: "SR5 p.309",
        tab: "adept",
      });
    }
    const sp = d.spell_points;
    if (tabs.includes("spells") && sp && sp.free - sp.used > 0) {
      items.push({
        id: "left-spells",
        severity: "info",
        message: `術式／式典／錬成の無料枠が ${sp.free - sp.used} 残っています`,
        ref: "SR5 p.70",
        tab: "spells",
      });
    }
    const cf = d.complex_form_points;
    if (tabs.includes("complexforms") && cf && cf.free - cf.used > 0) {
      items.push({
        id: "left-cf",
        severity: "info",
        message: `複合体の無料枠が ${cf.free - cf.used} 残っています`,
        ref: "SR5 p.251",
        tab: "complexforms",
      });
    }
  }

  (d.unimplemented_bonuses ?? []).forEach((b, i) => {
    items.push({
      id: `unimpl-${i}`,
      severity: "info",
      message: `未実装のボーナス: ${b.source}（${b.tag}）`,
      tab: guessTab(b.source),
    });
  });

  return items;
}

export function checklistSummary(items: CheckItem[]): ChecklistSummary {
  const errors = items.filter((i) => i.severity === "error").length;
  const warns = items.filter((i) => i.severity === "warn").length;
  const infos = items.filter((i) => i.severity === "info").length;
  return { errors, warns, infos, ok: errors === 0 };
}
