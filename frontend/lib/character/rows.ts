/** `rows` with the one whose `id` is `id` given `fields`; every other row,
 *  and the order, as they were. What an input on an owned item's row patches
 *  with: `patch({ gear: editRow(ch.gear, item.id, { rating }) })`.
 *
 *  `id` is compared with `===` as given, so an `undefined` one matches the
 *  rows that have none — what the inline `map` this replaces did. */
export function editRow<T extends { id?: string | null }>(
  rows: T[] | undefined,
  id: T["id"],
  fields: Partial<T>,
): T[] {
  return (rows || []).map((row) => (row.id === id ? { ...row, ...fields } : row));
}
