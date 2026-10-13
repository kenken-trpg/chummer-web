import type { Catalog, Character, QualityReqNode } from "@/lib/types";

/** Match the input requirements checked before the engine applies module grants. */
export function lifeModuleRequirementsMet(
  tree: QualityReqNode[],
  ch: Character,
  catalog: Catalog,
): boolean {
  const qualities = new Set(
    catalog.qualities.filter((q) => ch.quality_ids.includes(q.id)).map((q) => q.name),
  );
  const talentQuality = catalog.karma_talents?.find((t) => t.name === ch.talent)?.quality;
  if (talentQuality) qualities.add(talentQuality);
  const metatypes = new Set([ch.metatype, ch.metavariant || ""]);
  function matches(node: QualityReqNode): boolean {
    const children = node.children || [];
    if (node.tag === "oneof") return children.some(matches);
    if (node.tag === "allof" || node.tag === "group") return children.every(matches);
    if (node.tag === "quality") return qualities.has(node.name || "");
    if (node.tag === "metatype") return metatypes.has(node.name || "");
    return false;
  }
  return tree.every(matches);
}

/** Keep source names in English, including in Japanese UI. Parentheses preserve grouping. */
export function lifeModuleRequirementText(tree: QualityReqNode[]): string {
  function describe(node: QualityReqNode): string {
    if (node.tag === "quality" || node.tag === "metatype") return node.name || "";
    return `(${(node.children || []).map(describe).join(node.tag === "oneof" ? " / " : " + ")})`;
  }
  return tree.map(describe).join(" + ");
}

/** Versions of a parent share its single acquisition slot. */
export function lifeModuleAlreadyTaken(
  row: NonNullable<Catalog["life_modules"]>[number],
  ch: Character,
  catalog: Catalog,
): boolean {
  const family = row.family_id || row.parent || row.id;
  return (ch.life_modules || []).some((id) => {
    const taken = catalog.life_modules?.find((item) => item.id === id);
    return taken && (taken.family_id || taken.parent || taken.id) === family;
  });
}

/** Atomically keep acquisitions, stable IDs, and positional choices together. */
export function lifeModuleOrderPatch(ch: Character, order: number[]) {
  const modules = ch.life_modules || [];
  const positions = new Map(order.map((old, next) => [old, next]));
  const choices: Record<string, string> = {};
  for (const [key, value] of Object.entries(ch.life_module_choices || {})) {
    const colon = key.indexOf(":");
    const old = Number(key.slice(0, colon));
    if (colon < 0 || !Number.isInteger(old)) {
      choices[key] = value;
      continue;
    }
    const next = positions.get(old);
    if (next !== undefined) choices[`${next}${key.slice(colon)}`] = value;
  }
  const base = { life_modules: order.map((i) => modules[i]), life_module_choices: choices };
  if (ch.life_module_rules_version !== 2) return base;
  const ids = order.map((i) => ch.life_module_entry_ids![i]);
  return {
    ...base,
    life_module_entry_ids: ids,
    life_module_transfers: (ch.life_module_transfers || []).filter((row) =>
      ids.includes(row.entry_id),
    ),
  };
}

export function lifeModuleAppendPatch(ch: Character, moduleId: string) {
  const base = { life_modules: [...(ch.life_modules || []), moduleId] };
  return ch.life_module_rules_version === 2
    ? { ...base, life_module_entry_ids: [...(ch.life_module_entry_ids || []), crypto.randomUUID()] }
    : base;
}
