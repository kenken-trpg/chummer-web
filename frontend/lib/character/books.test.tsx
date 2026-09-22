import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import {
  BooksProvider,
  filterByBooks,
  isBookEnabled,
  sourceText,
  useAllowedBooks,
} from "@/lib/character/books";

const rows = [{ id: "a", source: "SR5" }, { id: "b", source: "RG" }, { id: "c" }];

describe("filterByBooks", () => {
  it("passes everything through when nothing is enabled", () => {
    // an empty book list is "unrestricted", not "no books"
    expect(filterByBooks(null, rows)).toBe(rows);
  });

  it("keeps only the enabled books", () => {
    expect(filterByBooks(new Set(["SR5"]), rows).map((r) => r.id)).toEqual(["a", "c"]);
  });

  it("keeps rows that belong to no book", () => {
    // a custom drug or a knowledge skill has no source; dropping those would
    // read as the settings being broken
    expect(filterByBooks(new Set(["RG"]), rows).map((r) => r.id)).toEqual(["b", "c"]);
  });
});

describe("isBookEnabled", () => {
  it("allows anything while unrestricted, and a sourceless row always", () => {
    expect(isBookEnabled(null, "HT")).toBe(true);
    expect(isBookEnabled(new Set(["SR5"]), undefined)).toBe(true);
    expect(isBookEnabled(new Set(["SR5"]), "HT")).toBe(false);
  });
});

describe("BooksProvider", () => {
  function Probe() {
    const allowed = useAllowedBooks();
    return <span>{allowed ? [...allowed].sort().join(",") : "unrestricted"}</span>;
  }

  it("treats an empty list as unrestricted", () => {
    const { unmount } = render(
      <BooksProvider books={[]}>
        <Probe />
      </BooksProvider>,
    );
    expect(screen.getByText("unrestricted")).toBeDefined();
    unmount();

    render(
      <BooksProvider books={["SR5", "RG"]}>
        <Probe />
      </BooksProvider>,
    );
    expect(screen.getByText("RG,SR5")).toBeDefined();
  });
});

describe("also_in (the Shadowrun Codex reprints)", () => {
  const reprinted = [{ id: "cf", source: "CF", also_in: [{ source: "SRCX", page: "198" }] }];

  it("lets a row in when only the book that reprints it is on", () => {
    expect(filterByBooks(new Set(["SR5", "SRCX"]), reprinted)).toEqual(reprinted);
    expect(filterByBooks(new Set(["SR5"]), reprinted)).toEqual([]);
    expect(isBookEnabled(new Set(["SRCX"]), "CF", reprinted[0].also_in)).toBe(true);
  });

  it("names the reprint's page beside the original book", () => {
    expect(sourceText(reprinted[0])).toBe("CF / SRCX p.198");
    expect(sourceText({ source: "SR5" })).toBe("SR5");
  });
});
