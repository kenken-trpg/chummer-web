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
