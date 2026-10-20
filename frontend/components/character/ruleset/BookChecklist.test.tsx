import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { describe, expect, it, vi } from "vitest";
import { BookChecklist } from "@/components/character/ruleset/BookChecklist";
import { identityTr, testUi } from "@/tests/fixtures";

const allBooks = [
  { code: "SR5", name: "Shadowrun 5th Edition" },
  { code: "SRCX", name: "Shadowrun Codex" },
  { code: "RR213", name: "Role&Roll Vol.213", group: "RR" },
  { code: "RR214", name: "Role&Roll Vol.214", group: "RR" },
];

function renderList(books: string[], onSet = vi.fn()) {
  render(
    <BookChecklist books={books} allBooks={allBooks} onSet={onSet} tr={identityTr} ui={testUi} />,
  );
  return onSet;
}

describe("BookChecklist groups", () => {
  it("folds the Role&Roll issues under one title, with how many are ticked", () => {
    renderList(["SR5", "RR214"]);
    const group = screen.getByText("Role&Roll").closest("details");
    expect(group).not.toBeNull();
    expect(group?.open).toBe(false);
    expect(group?.textContent).toContain("(1/2)");
    // the issues are inside it, the books outside
    expect(group?.textContent).toContain("Role&Roll Vol.213");
    expect(group?.textContent).not.toContain("Shadowrun Codex");
  });

  it("ticks an issue like any other book", () => {
    const onSet = renderList(["SR5"]);
    fireEvent.click(screen.getByRole("checkbox", { name: /Vol\.213/ }));
    expect(onSet).toHaveBeenCalledWith(["SR5", "RR213"]);
  });

  it("counts the issues in all on", () => {
    const onSet = renderList(["SR5"]);
    fireEvent.click(screen.getByRole("button", { name: testUi("settings.booksAllOn") }));
    expect(onSet).toHaveBeenCalledWith(["SR5", "SRCX", "RR213", "RR214"]);
  });
});
