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

    render(
      <ExportReview ed={makeEd({ exportReview: differences, exportReviewFormat: "chum5" })} />,
    );
    expect(screen.getByRole("alertdialog").textContent).toContain(".chum5");
  });

  const pendingRow = { name: "VI・スチームパンク", qty: 1, rating: 0, note: "", suggestions: [] };

  it("names Foundry and shows the omitted power with its fixed selection and reference", () => {
    render(
      <ExportReview
        ed={makeEd({
          exportReviewFormat: "fvtt",
          exportReview: [
            {
              key: "engine.export.fvttInnatePower",
              params: {
                name: { tr: "Natural Weapon" },
                selection: "Kick: DV ({STR} + 2)P, AP +1, +1 Reach",
                source: "SR5",
                page: "399",
              },
            },
          ],
        })}
      />,
    );
    const text = screen.getByRole("alertdialog").textContent;
    expect(text).toContain("Foundry向けJSONに含まれない");
    expect(text).toContain("Natural Weapon");
    expect(text).toContain("Kick: DV ({STR} + 2)P, AP +1, +1 Reach");
    expect(text).toContain("SR5 p.399");
    expect(text).toContain("別途追加");
  });

  it("counts the equipment rows still waiting, beside what the file would lose", () => {
    render(
      <ExportReview
        ed={makeEd({
          exportReview: [
            { key: "engine.export.lost", params: { kind: { ui: "engine.kind.weapon" }, count: 1 } },
          ],
          pendingGear: [pendingRow, { ...pendingRow, name: "アレス・サンダートラック" }],
        })}
      />,
    );
    const panel = screen.getByRole("alertdialog").textContent ?? "";
    expect(panel).toContain("武器が 1 件失われます"); // what the round trip found
    expect(panel).toContain("確認待ちの装備行が 2 件");
  });

  it("says so even when the round trip found nothing to lose", () => {
    // The rows were never sent, so the round-trip check cannot see them: this
    // is the case that used to write the file in silence.
    render(<ExportReview ed={makeEd({ exportReview: [], pendingGear: [pendingRow] })} />);
    expect(screen.getByRole("alertdialog").textContent).toContain("確認待ちの装備行が 1 件");
    // This is the first panel that opens with nothing to list, and a list of no
    // items is still announced as a list.
    expect(screen.queryByRole("list")).toBeNull();
  });

  it("says nothing about waiting rows when there are none", () => {
    render(
      <ExportReview
        ed={makeEd({
          exportReview: [
            { key: "engine.export.lost", params: { kind: { ui: "engine.kind.weapon" }, count: 1 } },
          ],
          pendingGear: [],
        })}
      />,
    );
    expect(screen.getByRole("alertdialog").textContent).not.toContain("確認待ち");
  });
});
