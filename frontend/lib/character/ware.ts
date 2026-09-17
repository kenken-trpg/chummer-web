import type { WareCatalogItem, WareInstall } from "@/lib/types";

export function removeWareTree(items: WareInstall[], id: string): WareInstall[] {
  const drop = new Set<string>([id]);
  let grew = true;
  while (grew) {
    grew = false;
    for (const row of items) {
      // a row the browser just added has no id yet — the server assigns one,
      // and nothing can be hanging off it in the meantime
      if (row.id && row.parent_id && drop.has(row.parent_id) && !drop.has(row.id)) {
        drop.add(row.id);
        grew = true;
      }
    }
  }
  return items.filter((row) => !row.id || !drop.has(row.id));
}

export function wareBounds(
  item: WareCatalogItem,
  ranges?: Record<string, { min: number; max: number }>,
) {
  return ranges?.[item.id] || { min: item.minrating, max: item.maxrating };
}

export function hideFromWareCatalog(item: WareCatalogItem, kind: "cyberware" | "bioware") {
  if (item.requireparent || item.formula_rating) return true;
  const same = item.required?.[kind] || [];
  const other = item.required?.[kind === "bioware" ? "cyberware" : "bioware"] || [];
  return same.length > 0 && other.length === 0;
}

export function sideSlotKey(item: WareCatalogItem) {
  return (item.limbslot || item.id || "").toLowerCase();
}

export function nextFreeSide(
  items: WareInstall[],
  catalogItems: WareCatalogItem[],
  ware: WareCatalogItem,
) {
  if (!ware.selectside) return undefined;
  const slot = sideSlotKey(ware);
  const used = new Set(
    items
      .filter((row) => !row.parent_id && row.side)
      .filter((row) => {
        const spec = catalogItems.find((w) => w.id === row.ware_id);
        return spec?.selectside && sideSlotKey(spec) === slot;
      })
      .map((row) => row.side),
  );
  return used.has("Left") && !used.has("Right") ? "Right" : "Left";
}

/**
 * `rows` minus what hung off the ware a removal took away: the gear a gland
 * held, the accessories on an implanted weapon — and whatever hangs off
 * those in turn. Rows under anything else (a weapon, a piece of armor) stay.
 */
export function dropUnderRemovedWare<T extends { id?: string; parent_id?: string | null }>(
  rows: T[],
  before: WareInstall[],
  after: WareInstall[],
): T[] {
  const kept = new Set(after.map((row) => row.id));
  const drop = new Set(
    before.map((row) => row.id).filter((id): id is string => !!id && !kept.has(id)),
  );
  let grew = true;
  while (grew) {
    grew = false;
    for (const row of rows) {
      if (row.id && row.parent_id && drop.has(row.parent_id) && !drop.has(row.id)) {
        drop.add(row.id);
        grew = true;
      }
    }
  }
  return rows.filter((row) => !row.parent_id || !drop.has(row.parent_id));
}
