"use client";

import type { BookInfo } from "@/lib/types";
import { useLocale, type UiFn } from "@/lib/i18n";

/** The core rulebook, which "all off" keeps. */
const CORE_BOOK = "SR5";

/**
 * Which rulebooks the character may buy from, one checkbox each.
 *
 * An empty list means unrestricted, so "all off" leaves the core rulebook:
 * that is the fewest books a character can be built from, and an empty list
 * would mean the opposite of what the button says.
 */
export function BookChecklist({
  books,
  allBooks,
  onSet,
  tr,
  ui,
}: {
  /** The codes currently ticked. Empty means unrestricted. */
  books: string[];
  allBooks: BookInfo[];
  onSet: (next: string[]) => void;
  tr: (name: string) => string;
  ui: UiFn;
}) {
  const [locale] = useLocale();
  // By id, not `tr(name)`: that table also holds the program ロックダウン, which
  // turned the untranslated supplement Lockdown into katakana.
  const bookTitle = (book: BookInfo) =>
    locale === "ja" && book.name_ja ? book.name_ja : tr(book.name);
  return (
    <>
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <button
          className="btn"
          onClick={() => onSet(allBooks.map((book) => book.code))}
          title={ui("settings.booksAllOnHint")}
        >
          {ui("settings.booksAllOn")}
        </button>
        <button
          className="btn"
          onClick={() => onSet([CORE_BOOK])}
          title={ui("settings.booksAllOffHint")}
        >
          {ui("settings.booksAllOff")}
        </button>
      </div>
      <div className="book-grid" style={{ marginTop: 8 }}>
        {allBooks.map((book) => (
          <label key={book.code} className="book-check">
            <input
              type="checkbox"
              checked={books.includes(book.code)}
              onChange={() =>
                onSet(
                  books.includes(book.code)
                    ? books.filter((c) => c !== book.code)
                    : [...books, book.code],
                )
              }
            />
            <span>
              {bookTitle(book)} <span className="muted">({book.code})</span>
            </span>
          </label>
        ))}
      </div>
      <p className="muted">{ui("settings.booksNote")}</p>
    </>
  );
}
