import type { Catalog, Character, QualityReqNode, WareInstall } from "@/lib/types";
import { poolRating } from "@/lib/character/format";
import type { UiFn } from "@/lib/i18n";

type QualitySpec = Catalog["qualities"][number];
type QualityRow = Character["derived"]["qualities"][number];
export type QualityDisplayRow = QualityRow & { level?: number };

/** Keep the engine's per-level rows intact; combine only leveled qualities for display. */
export function qualityDisplayRows(
  rows: QualityRow[],
  specs: QualitySpec[] = [],
): QualityDisplayRow[] {
  const byId = new Map(specs.map((q) => [q.id, q]));
  const groups = new Map<string, QualityDisplayRow>();
  const result: QualityDisplayRow[] = [];
  for (const row of rows) {
    if (!(row.has_levels ?? byId.get(row.id)?.has_levels)) {
      result.push({ ...row });
      continue;
    }
    // Distinct targets and grants must not become levels of a purchased quality.
    const key = JSON.stringify([
      row.id,
      row.extra || "",
      row.spirit_extra || "",
      row.side || "",
      row.category,
      row.source,
      !!row.free,
      row.disabled_by || "",
    ]);
    const group = groups.get(key);
    if (group) {
      group.level = (group.level || 1) + 1;
      group.karma += row.karma;
      if (row.karma_base != null) group.karma_base = (group.karma_base ?? 0) + row.karma_base;
      if (row.career_cost != null) group.career_cost = (group.career_cost ?? 0) + row.career_cost;
    } else {
      const next = { ...row, level: 1 };
      groups.set(key, next);
      result.push(next);
    }
  }
  return result;
}

/** Own cap and shared cap (Indomitable / Tough as Nails), excluding this quality's levels. */
export function qualityLevelMax(q: QualitySpec, ids: string[], specs: QualitySpec[]): number {
  const ownMax = q.max_takes ?? 1;
  const siblings = new Set(q.include_in_limit || []);
  if (!siblings.size) return ownMax;
  const byId = new Map(specs.map((item) => [item.id, item.name]));
  const otherLevels = ids.filter((id) => id !== q.id && siblings.has(byId.get(id) || "")).length;
  return Math.max(0, Math.min(ownMax, (q.limit_with_inclusions || ownMax) - otherLevels));
}

/** Retain repeated IDs for save compatibility, and remove later levels first in career. */
export function setQualityLevel(ids: string[], id: string, level: number): string[] {
  const owned = ids.filter((item) => item === id).length;
  if (level >= owned) return [...ids, ...Array<string>(level - owned).fill(id)];
  let kept = 0;
  return ids.filter((item) => item !== id || ++kept <= level);
}

export type QualityReqCtx = {
  qualities: Set<string>;
  metatypes: Set<string>;
  magenabled: boolean;
  resenabled: boolean;
  skills: Record<string, number>;
  knowledge: Record<string, number>;
  powers: Set<string>;
  spells: Set<string>;
  cyberware: Set<string>;
  bioware: Set<string>;
  tradition: string;
  essence: number;
  essLost: number;
};

export function reqNodeMet(node: QualityReqNode, ctx: QualityReqCtx): boolean {
  const tag = node.tag;
  const children = node.children || [];
  if (tag === "oneof")
    return children.length ? children.some((child) => reqNodeMet(child, ctx)) : true;
  if (tag === "allof" || tag === "group")
    return children.length ? children.every((child) => reqNodeMet(child, ctx)) : true;
  const name = node.name || "";
  if (tag === "quality") return ctx.qualities.has(name);
  if (tag === "metatype") return ctx.metatypes.has(name);
  if (tag === "magenabled") return ctx.magenabled;
  if (tag === "resenabled") return ctx.resenabled;
  if (tag === "power") return ctx.powers.has(name);
  if (tag === "cyberware") return ctx.cyberware.has(name);
  if (tag === "bioware") return ctx.bioware.has(name);
  if (tag === "spell") return ctx.spells.has(name);
  if (tag === "tradition") return ctx.tradition === name;
  if (tag === "skill") {
    const rating = node.val || 1;
    const pool = (node.type || "").toLowerCase() === "knowledge" ? ctx.knowledge : ctx.skills;
    return poolRating(pool, name) >= rating;
  }
  if (tag === "ess") {
    const value = node.value || 0;
    return value < 0 ? ctx.essLost + 1e-9 >= Math.abs(value) : ctx.essence + 1e-9 >= value;
  }
  return false;
}

export function qualityTreeMet(tree: QualityReqNode[] | undefined, ctx: QualityReqCtx) {
  const nodes = tree || [];
  if (!nodes.length) return true;
  return nodes.every((node) => reqNodeMet(node, ctx));
}

export function qualityBlockReason(
  item: Catalog["qualities"][number],
  ctx: QualityReqCtx,
  ui: UiFn,
) {
  if ((item.required_tree || []).length && !qualityTreeMet(item.required_tree, ctx))
    return ui("qual.blockPrereq");
  if ((item.forbidden_tree || []).length && qualityTreeMet(item.forbidden_tree, ctx))
    return ui("qual.blockForbidden");
  return "";
}

export function dropSkillPicksForPrefix(
  picks: Record<string, string> | undefined,
  prefixes: string[],
) {
  const next = { ...(picks || {}) };
  for (const key of Object.keys(next)) {
    if (prefixes.some((prefix) => key.startsWith(prefix))) delete next[key];
  }
  return next;
}

export function dropRemovedWarePicks(
  picks: Record<string, string> | undefined,
  remaining: WareInstall[],
) {
  const keep = new Set(remaining.map((row) => row.id));
  const next = { ...(picks || {}) };
  for (const key of Object.keys(next)) {
    const match = key.match(/^ware:([^:]+):/);
    if (match && !keep.has(match[1])) delete next[key];
  }
  return next;
}
