import { fireEvent, render, screen } from "@testing-library/react";
import { ExportReview } from "@/components/character/ExportReview";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { identityTr } from "@/tests/fixtures";

function makeEd(over: Partial<CharacterEditor> = {}): CharacterEditor {
  return {
    tr: identityTr,
    exportReview: null,
    confirmExport: vi.fn().mockResolvedValue(undefined),
    cancelExport: vi.fn(),
    ...over,
  } as unknown as CharacterEditor;
}

describe("<ExportReview>", () => {
  it("renders nothing while no export is waiting", () => {
    const { container } = render(<ExportReview ed={makeEd()} />);
    expect(container.innerHTML).toBe("");
  });

  it("lists what the file would lose and wires both answers", () => {
    const ed = makeEd({
      exportReview: [
        { key: "engine.export.lost", params: { kind: { ui: "engine.kind.weapon" }, count: 1 } },
      ],
    });
    render(<ExportReview ed={ed} />);

    expect(screen.getByRole("alertdialog").textContent).toContain("1 件");
    screen.getByText("武器が 1 件失われます");
    fireEvent.click(screen.getByRole("button", { name: "このまま書き出す" }));
    expect(ed.confirmExport).toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "やめる" }));
    expect(ed.cancelExport).toHaveBeenCalled();
  });

  it("names the format that was asked for, not whichever came first", () => {
    // The panel is shared, and the heading used to say chum5 whatever was being
    // written — so an .xlsx export told the player about a file it was not.
    const differences = [
      { key: "engine.export.changed", params: { kind: { ui: "engine.kind.other" } } },
    ];
    const { unmount } = render(
      <ExportReview ed={makeEd({ exportReview: differences, exportReviewFormat: "xlsx" })} />,
    );
    expect(screen.getByRole("alertdialog").textContent).toContain(".xlsx");
    expect(screen.getByRole("alertdialog").textContent).not.toContain("chum5");
    unmount();

    render(<ExportReview ed={makeEd({ exportReview: differences, exportReviewFormat: "chum5" })} />);
    expect(screen.getByRole("alertdialog").textContent).toContain(".chum5");
  });
});
