import type { Catalog, QualityRestriction, TalentTerm } from "@/lib/types/catalog";

type Limited = { forbidden?: readonly TalentTerm[]; required?: readonly TalentTerm[] };

/**
 * Whether a character of `metatype` may take this talent — the server's
 * `talent_allowed`, so the pulldown offers what the check accepts.
 *
 * `<forbidden>` and `<required>` name a metatype or the *base* metatype's
 * category, as Chummer's `MetatypeCategory` is: an A.I. takes only the A.I.
 * talent, and a Technomancer must be a metahuman. A talent without the lists
 * (an older catalog, the synthesized Mundane) allows anyone.
 */
export function talentAllowed(talent: Limited, metatype: string, catalog: Catalog): boolean {
  const category = catalog.metatypes.find((m) => m.name === metatype)?.category ?? "";
  const hits = (term: TalentTerm) =>
    term.kind === "metatypecategory" ? term.name === category : term.name === metatype;
  if ((talent.forbidden ?? []).some(hits)) return false;
  const required = talent.required ?? [];
  return required.length === 0 || required.some(hits);
}

/**
 * The talents to list: those `metatype` may take, and the current one even if
 * it may not, so the pulldown still shows what the character has while the
 * check says why it is wrong.
 */
export function talentsFor<T extends Limited & { name: string }>(
  talents: readonly T[],
  metatype: string,
  current: string | undefined,
  catalog: Catalog,
): T[] {
  return talents.filter((t) => t.name === current || talentAllowed(t, metatype, catalog));
}

/**
 * The metatype's `<qualityrestriction>`, or `null` when it takes any quality.
 * Only the A.I. and its metavariants have one; the metavariant's own list
 * wins, as the server reads the metavariant.
 */
export function qualityRestriction(
  catalog: Catalog,
  metatype: string,
  metavariant: string | null | undefined,
): QualityRestriction | null {
  const base = catalog.metatypes.find((m) => m.name === metatype);
  const variant = metavariant ? base?.metavariants.find((v) => v.name === metavariant) : undefined;
  return variant?.quality_restriction ?? base?.quality_restriction ?? null;
}
