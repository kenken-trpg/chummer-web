import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { SheetUrlImport } from "@/components/character/SheetUrlImport";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";

function makeEd(importSheetUrl = vi.fn().mockResolvedValue(undefined)): CharacterEditor {
  return { importSheetUrl } as unknown as CharacterEditor;
}

const URL_OK = "https://docs.google.com/spreadsheets/d/abc123/edit";

describe("<SheetUrlImport>", () => {
  it("is folded away until asked for, and says what sharing it needs", () => {
    render(<SheetUrlImport ed={makeEd()} />);
    expect(screen.queryByRole("textbox")).toBeNull();

    fireEvent.click(screen.getByRole("button", { name: "URLから読込" }));
    screen.getByRole("textbox", { name: "URLから読込" });
    // what may be pasted, and the sharing it needs: both have to be on screen
    screen.getByText(
      "貼れるのは https://docs.google.com/spreadsheets/d/… の URL で、「リンクを知っている全員」で共有されたシートだけ読めます",
    );
  });

  it("reads the URL it was given and folds away again", async () => {
    const read = vi.fn().mockResolvedValue(undefined);
    render(<SheetUrlImport ed={makeEd(read)} />);
    fireEvent.click(screen.getByRole("button", { name: "URLから読込" }));

    fireEvent.change(screen.getByRole("textbox"), { target: { value: URL_OK } });
    fireEvent.click(screen.getByRole("button", { name: "読み込む" }));

    await waitFor(() => expect(read).toHaveBeenCalledWith(URL_OK));
    await waitFor(() => expect(screen.queryByRole("textbox")).toBeNull());
  });

  it("keeps a refused URL on screen to be corrected", async () => {
    // The editor puts the reason up; what this must not do is throw the address
    // away, because correcting it is the whole of what to do next.
    const read = vi.fn().mockRejectedValue(new Error("not shared"));
    render(<SheetUrlImport ed={makeEd(read)} />);
    fireEvent.click(screen.getByRole("button", { name: "URLから読込" }));

    fireEvent.change(screen.getByRole("textbox"), { target: { value: URL_OK } });
    fireEvent.click(screen.getByRole("button", { name: "読み込む" }));

    await waitFor(() => expect(read).toHaveBeenCalled());
    await waitFor(() => expect(screen.getByRole("textbox")).toHaveProperty("value", URL_OK));
  });

  it("does not ask for an empty address", () => {
    const read = vi.fn();
    render(<SheetUrlImport ed={makeEd(read)} />);
    fireEvent.click(screen.getByRole("button", { name: "URLから読込" }));

    expect(screen.getByRole("button", { name: "読み込む" })).toHaveProperty("disabled", true);
    fireEvent.change(screen.getByRole("textbox"), { target: { value: "   " } });
    expect(screen.getByRole("button", { name: "読み込む" })).toHaveProperty("disabled", true);
    expect(read).not.toHaveBeenCalled();
  });
});
