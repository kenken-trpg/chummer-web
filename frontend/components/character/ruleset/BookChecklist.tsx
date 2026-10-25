"use client";

import type { BookInfo } from "@/lib/types";
import { HelpTip } from "@/components/help/HelpTip";
import { useLocale, type UiFn } from "@/lib/i18n";

/** The core rulebook, which "all off" keeps. */
const CORE_BOOK = "SR5";

/** `BookInfo.group` -> the folded list's title. A magazine's issues are one
 *  book each, up to 29 of them, so they fold away under its name. */
const GROUP_TITLES: Record<string, string> = { RR: "Role&Roll" };

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
  /** Called with how to get the new list from the saved one, not with the new
   *  list: ticks that land while another is being saved stack up. */
  onSet: (next: (books: string[]) => string[]) => void;
  tr: (name: string) => string;
  ui: UiFn;
}) {
  const [locale] = useLocale();
  // By id, not `tr(name)`: that table also holds the program ロックダウン, which
  // turned the untranslated supplement Lockdown into katakana.
  const bookTitle = (book: BookInfo) =>
    locale === "ja" && book.name_ja ? book.name_ja : tr(book.name);
  const check = (book: BookInfo) => (
    <label key={book.code} className="book-check">
      <input
        type="checkbox"
        checked={books.includes(book.code)}
        onChange={(e) => {
          const on = e.target.checked;
          onSet((saved) =>
            on
              ? [...saved.filter((c) => c !== book.code), book.code]
              : saved.filter((c) => c !== book.code),
          );
        }}
      />
      <span>
        {bookTitle(book)} <span className="muted">({book.code})</span>
      </span>
    </label>
  );
  const grouped = new Map<string, BookInfo[]>();
  for (const book of allBooks) {
    if (book.group) grouped.set(book.group, [...(grouped.get(book.group) || []), book]);
  }
  const groups = [...grouped];
  return (
    <>
      <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
        <HelpTip
          label={ui("help.open", { label: ui("help.settings.booksBulkLabel") })}
          lines={[
            { label: ui("help.settings.booksAllOn") },
            { label: ui("help.settings.booksAllOff") },
          ]}
        >
          <button className="btn" onClick={() => onSet(() => allBooks.map((book) => book.code))}>
            {ui("settings.booksAllOn")}
          </button>
          <button className="btn" onClick={() => onSet(() => [CORE_BOOK])}>
            {ui("settings.booksAllOff")}
          </button>
        </HelpTip>
      </div>
      <div className="book-grid" style={{ marginTop: 8 }}>
        {allBooks.filter((book) => !book.group).map(check)}
      </div>
      {groups.map(([group, members]) => (
        <details key={group} className="book-group">
          <summary>
            {GROUP_TITLES[group] || group}{" "}
            <span className="muted">
              ({members.filter((book) => books.includes(book.code)).length}/{members.length})
            </span>
          </summary>
          <div className="book-grid">{members.map(check)}</div>
        </details>
      ))}
      <p className="muted">{ui("settings.booksNote")}</p>
    </>
  );
}
