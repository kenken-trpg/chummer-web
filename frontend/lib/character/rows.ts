/** `rows` with the one whose `id` is `id` given `fields`; every other row,
 *  and the order, as they were. What an input on an owned item's row patches
 *  with: `patch({ gear: editRow(ch.gear, item.id, { rating }) })`. */
export function editRow<T extends { id?: string | null }>(
  rows: T[] | undefined,
  id: string,
  fields: Partial<T>,
): T[] {
  return (rows || []).map((row) => (row.id === id ? { ...row, ...fields } : row));
}
