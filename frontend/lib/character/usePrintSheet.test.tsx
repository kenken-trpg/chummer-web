import { useState } from "react";
import { fireEvent, render, waitFor } from "@testing-library/react";
import { usePrintSheet } from "@/lib/character/usePrintSheet";
import type { SheetLayout } from "@/lib/character/sheet-data";

function Harness({ start }: { start: SheetLayout }) {
  const [layout, setLayout] = useState<SheetLayout>(start);
  const printSheet = usePrintSheet(layout, setLayout);
  return (
    <>
      <span data-testid="layout">{layout}</span>
      <button onClick={printSheet}>印刷実行</button>
    </>
  );
}

describe("usePrintSheet", () => {
  it("switches to the print layout, prints, then restores the previous layout", async () => {
    const printMock = vi.spyOn(window, "print").mockImplementation(() => {});
    const { getByText, getByTestId } = render(<Harness start="standard" />);

    fireEvent.click(getByText("印刷実行"));
    expect(getByTestId("layout").textContent).toBe("print");

    await waitFor(() => expect(printMock).toHaveBeenCalledTimes(1));
    fireEvent(window, new Event("afterprint"));
    await waitFor(() => expect(getByTestId("layout").textContent).toBe("standard"));

    printMock.mockRestore();
  });

  it("just prints (no layout churn) when already on the print layout", async () => {
    const printMock = vi.spyOn(window, "print").mockImplementation(() => {});
    const { getByText, getByTestId } = render(<Harness start="print" />);

    fireEvent.click(getByText("印刷実行"));
    await waitFor(() => expect(printMock).toHaveBeenCalledTimes(1));
    expect(getByTestId("layout").textContent).toBe("print");

    printMock.mockRestore();
  });
});
