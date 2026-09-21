import { fireEvent, render, screen } from "@testing-library/react";
import { ExportReview } from "@/components/character/ExportReview";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { identityTr } from "@/tests/fixtures";

function makeEd(over: Partial<CharacterEditor> = {}): CharacterEditor {
  return {
    tr: identityTr,
    exportReview: null,
    confirmChum5: vi.fn().mockResolvedValue(undefined),
    cancelChum5: vi.fn(),
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
    expect(ed.confirmChum5).toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "やめる" }));
    expect(ed.cancelChum5).toHaveBeenCalled();
  });
});
