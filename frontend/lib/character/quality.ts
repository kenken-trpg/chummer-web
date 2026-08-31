import type { Catalog, QualityReqNode, WareInstall } from "@/lib/types";
import { poolRating } from "@/lib/character/format";

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

export function qualityBlockReason(item: Catalog["qualities"][number], ctx: QualityReqCtx) {
  if ((item.required_tree || []).length && !qualityTreeMet(item.required_tree, ctx))
    return "前提を満たしていません";
  if ((item.forbidden_tree || []).length && qualityTreeMet(item.forbidden_tree, ctx))
    return "現在のキャラクターでは取れません";
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
