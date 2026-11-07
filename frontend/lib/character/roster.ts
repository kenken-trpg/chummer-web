import type { CharacterSummary } from "@/lib/api";

export type RosterFilter = "all" | "creation" | "career";
export type RosterSort = "updated" | "name";

export function selectRoster(
  roster: readonly CharacterSummary[],
  query: string,
  filter: RosterFilter,
  sort: RosterSort,
  locale: string,
): CharacterSummary[] {
  const normalize = (name: string) => name.normalize("NFKC").toLocaleLowerCase(locale);
  const search = normalize(query.trim());
  const collator = new Intl.Collator(locale, { numeric: true, sensitivity: "base" });
  return roster
    .filter(
      (row) =>
        normalize(row.name).includes(search) &&
        (filter === "all" || (filter === "career" ? row.career : !row.career)),
    )
    .sort(
      (a, b) =>
        (sort === "updated" ? b.updated - a.updated : collator.compare(a.name, b.name)) ||
        collator.compare(a.name, b.name) ||
        a.id.localeCompare(b.id),
    );
}
