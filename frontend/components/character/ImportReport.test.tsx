import { fireEvent, render, screen } from "@testing-library/react";
import { ImportReport } from "@/components/character/ImportReport";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import type { Notice } from "@/lib/engine-notices";
import { identityTr } from "@/tests/fixtures";

function makeEd(over: Partial<CharacterEditor> = {}): CharacterEditor {
  return {
    tr: identityTr,
    importReport: null,
    dismissImportReport: vi.fn(),
    ...over,
  } as unknown as CharacterEditor;
}

const skipped = (name: string): Notice => ({
  key: "engine.import.skippedUnknown",
  params: { kind: { ui: "engine.kind.quality" }, name },
});

describe("<ImportReport>", () => {
  it("renders nothing after a file that lost nothing", () => {
    const { container } = render(<ImportReport ed={makeEd()} />);
    expect(container.innerHTML).toBe("");
  });

  it("lists what the file lost, one line each", () => {
    render(<ImportReport ed={makeEd({ importReport: [skipped("Foo"), skipped("Bar")] })} />);
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    screen.getByText("資質「Foo」はカタログに無いためスキップしました");
    expect(screen.getByRole("alertdialog").textContent).toContain("2");
  });

  it("is closed by the player", () => {
    const ed = makeEd({ importReport: [skipped("Foo")] });
    render(<ImportReport ed={ed} />);
    fireEvent.click(screen.getByRole("button", { name: "閉じる" }));
    expect(ed.dismissImportReport).toHaveBeenCalled();
  });

  it("counts the whole list while showing the head of it", () => {
    // 40 lines is a wall, so the list stops — but the number in the heading is
    // what the file really lost, and the rest is said to be there.
    const many = Array.from({ length: 40 }, (_, i) => skipped(`w${i}`));
    render(<ImportReport ed={makeEd({ importReport: many })} />);

    expect(screen.getByRole("alertdialog").textContent).toContain("40");
    screen.getByText("資質「w19」はカタログに無いためスキップしました");
    expect(screen.queryByText("資質「w20」はカタログに無いためスキップしました")).toBeNull();
    screen.getByText("ほか 20 件");
  });
});
