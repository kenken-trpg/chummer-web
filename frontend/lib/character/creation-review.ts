import type { Character } from "@/lib/types";
import type { MsgKey } from "@/lib/i18n";
import type { Tab } from "./constants";

export type CreationBudget = { label: MsgKey; remaining: number; tab: Tab };

/** Display the engine's remaining budgets without introducing creation rules. */
export function creationBudgets(ch: Character): CreationBudget[] {
  const d = ch.derived;
  const budgets: CreationBudget[] = [];
  const points: Array<[keyof typeof d.points, MsgKey, Tab]> = [
    ["attributes", "check.points.attributes", "attrs"],
    ["special", "check.points.special", "attrs"],
    ["skills", "check.points.skills", "skills"],
    ["skill_groups", "check.points.skillGroups", "skills"],
    ["knowledge", "check.points.knowledge", "skills"],
  ];
  for (const [key, label, tab] of points) {
    const point = d.points?.[key];
    if (point && (point.max || point.used))
      budgets.push({ label, remaining: point.max - point.used, tab });
  }
  budgets.push({
    label: "app.creationReview.karma",
    remaining: d.karma.remaining,
    tab: "qualities",
  });
  budgets.push({ label: "app.creationReview.nuyen", remaining: d.nuyen, tab: "gear" });
  if (d.contact_points)
    budgets.push({
      label: "app.creationReview.contacts",
      remaining: Math.max(0, d.contact_points.free - d.contact_points.used),
      tab: "contacts",
    });
  if (d.enabled_tabs.includes("adept") && d.power_points)
    budgets.push({
      label: "app.creationReview.power",
      remaining: d.power_points.max - d.power_points.used,
      tab: "adept",
    });
  if (d.enabled_tabs.includes("spells") && d.spell_points)
    budgets.push({
      label: "app.creationReview.spells",
      remaining: Math.max(
        0,
        d.spell_points.free - d.spell_points.used + (d.spell_points.paid ?? 0),
      ),
      tab: "spells",
    });
  if (d.enabled_tabs.includes("complexforms") && d.complex_form_points)
    budgets.push({
      label: "app.creationReview.forms",
      remaining: Math.max(
        0,
        d.complex_form_points.free - d.complex_form_points.used + (d.complex_form_points.paid ?? 0),
      ),
      tab: "complexforms",
    });
  return budgets;
}
