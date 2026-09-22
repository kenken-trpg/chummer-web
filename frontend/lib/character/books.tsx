"use client";

import { createContext, type ReactNode, useContext, useMemo } from "react";

/**
 * Which rulebooks the current character may buy from.
 *
 * Chummer keeps this in the settings file and applies it to every list in the
 * app. Here it rides a context rather than the `Catalog` object for one
 * reason: the catalog is also how an *owned* item is looked up — its name, its
 * stats, its page reference. Narrowing the catalog itself would blank out the
 * gear of a character whose GM later dropped a book, which is exactly the
 * moment they need to still see what they own in order to sell it.
 *
 * So the catalog stays whole and only the pick lists narrow. `CatalogPicker`
 * and `PickerList` do that for every panel that buys from the catalog; nothing
 * else has to know.
 */

/** `null` = unrestricted. Distinct from an empty set, which would be "no books
 *  at all" and is never what the user means. */
export type AllowedBooks = ReadonlySet<string> | null;

const BooksContext = createContext<AllowedBooks>(null);

export function BooksProvider({ books, children }: { books?: string[]; children: ReactNode }) {
  const allowed = useMemo<AllowedBooks>(
    () => (books && books.length > 0 ? new Set(books) : null),
    [books],
  );
  return <BooksContext.Provider value={allowed}>{children}</BooksContext.Provider>;
}

/** The enabled books, or `null` for unrestricted. */
export function useAllowedBooks(): AllowedBooks {
  return useContext(BooksContext);
}

/** The one field the filter reads. Deliberately not a generic constraint: a
 *  type whose properties are all optional is a *weak type*, so constraining to
 *  it would reject every caller whose rows have no `source` at all — exactly
 *  the rows this is meant to wave through. */
type Sourced = { source?: string; also_in?: { source: string; page?: string }[] };

/**
 * `items`, narrowed to the enabled books.
 *
 * An item with no `source` is always kept: house-ruled and generated entries
 * (a custom drug, a knowledge skill) belong to no book, and dropping them
 * would make the settings look broken rather than strict.
 */
export function filterByBooks<T>(allowed: AllowedBooks, items: T[]): T[] {
  if (!allowed) return items;
  return items.filter((item) => {
    const row = item as Sourced | null;
    return isBookEnabled(allowed, row?.source, row?.also_in);
  });
}

/**
 * `filterByBooks` bound to the current settings.
 *
 * For the per-row "pick a mod, press 装着" lists. They buy from the catalog
 * without going through `<CatalogPicker>`, so each of them used to name a book
 * in code instead — `mod.source === "SR5"`, sometimes `|| "R5"` — which is a
 * book list that no setting can reach. With every book enabled that hid 110 of
 * the 136 weapon accessories.
 */
export function useBookFilter(): <T>(items: T[]) => T[] {
  const allowed = useAllowedBooks();
  return useMemo(
    () =>
      <T,>(items: T[]) =>
        filterByBooks(allowed, items),
    [allowed],
  );
}

/** Is this one item buyable? For the panels that test a single row rather
 *  than filter a list. `alsoIn` is the other books that print the item — the
 *  Shadowrun Codex reprints some Chrome Flesh or Data Trails entries, and
 *  either book being on is enough. */
export function isBookEnabled(
  allowed: AllowedBooks,
  source?: string,
  alsoIn?: { source: string }[],
): boolean {
  return (
    !allowed || !source || allowed.has(source) || (alsoIn || []).some((b) => allowed.has(b.source))
  );
}

/** `source`, plus where else the item is printed: "CF / SRCX p.198". */
export function sourceText(item: Sourced): string {
  return [item.source || "", ...(item.also_in || []).map((b) => `${b.source} p.${b.page || ""}`)]
    .filter(Boolean)
    .join(" / ");
}
