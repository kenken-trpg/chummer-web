import { expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import Error from "@/app/error";

it("shows the message and calls reset", () => {
  const reset = vi.fn();
  render(
    <Error error={Object.assign(new globalThis.Error("boom"), { digest: "d1" })} reset={reset} />,
  );

  expect(screen.getByText("問題が発生しました")).toBeTruthy();
  expect(screen.getByText("boom")).toBeTruthy();

  fireEvent.click(screen.getByRole("button", { name: "再読み込み" }));
  expect(reset).toHaveBeenCalledOnce();
});
