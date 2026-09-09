import type { Catalog, PriorityCategory, PriorityTable } from "@/lib/types";

/**
 * The priority table a character actually builds against.
 *
 * `priorities.xml` carries several tables — Standard, Prime Runner, Street
 * Level — and a settings file picks one. The catalog cannot be built for one
 * character's pick because every character shares it, so it ships the Standard
 * table plus, per other table, only the cells that table replaces. Putting
 * them together is this.
 *
 * An unknown name falls back to Standard, which is what the engine does too:
 * a settings file naming a table this data does not have still builds a
 * character rather than an empty one.
 */
export function priorityTableFor(catalog: Catalog, table?: string): PriorityTable {
  const overrides = table ? catalog.priority_table_overrides?.[table] : undefined;
  if (!overrides) return catalog.priority_table;
  const merged = {} as PriorityTable;
  for (const [category, rows] of Object.entries(catalog.priority_table)) {
    const cat = category as PriorityCategory;
    merged[cat] = { ...rows, ...(overrides[cat] ?? {}) };
  }
  return merged;
}
