import { useState } from "react";
import { expect, it, vi } from "vitest";
import { act, render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { BoundedNumberInput } from "@/components/character/BoundedNumberInput";

/** The box the way a tab uses it: what is shown is what the server sent back,
 *  clamped to the range, after each commit. */
function Clamped({ onCommit }: { onCommit: (n: number) => void }) {
  const [value, setValue] = useState(1);
  return (
    <BoundedNumberInput
      aria-label="rating"
      min={1}
      max={6}
      value={value}
      onCommit={(n) => {
        onCommit(n);
        setValue(Math.min(6, Math.max(1, n)));
      }}
    />
  );
}

const box = () => screen.getByLabelText("rating") as HTMLInputElement;

it("lets a middle rating be typed over the old one", () => {
  const onCommit = vi.fn();
  render(<Clamped onCommit={onCommit} />);
  fireEvent.focus(box());
  // clear the box, then type the new digit
  fireEvent.change(box(), { target: { value: "" } });
  expect(box().value).toBe("");
  fireEvent.change(box(), { target: { value: "3" } });
  expect(onCommit).toHaveBeenCalledTimes(1);
  expect(onCommit).toHaveBeenCalledWith(3);
  expect(box().value).toBe("3");
});

it("commits a valid value at once, as the spinner sends it", () => {
  const onCommit = vi.fn();
  render(<Clamped onCommit={onCommit} />);
  fireEvent.change(box(), { target: { value: "2" } });
  expect(onCommit).toHaveBeenCalledWith(2);
});

it("holds an out-of-range text until the box is left, then clamps it", () => {
  const onCommit = vi.fn();
  render(<Clamped onCommit={onCommit} />);
  fireEvent.change(box(), { target: { value: "13" } });
  expect(onCommit).not.toHaveBeenCalled();
  expect(box().value).toBe("13");
  act(() => {
    fireEvent.focusOut(box());
  });
  expect(onCommit).toHaveBeenCalledWith(6);
  expect(box().value).toBe("6");
});

it("puts the value back when the box is left empty", () => {
  const onCommit = vi.fn();
  render(<Clamped onCommit={onCommit} />);
  fireEvent.change(box(), { target: { value: "" } });
  act(() => {
    fireEvent.focusOut(box());
  });
  expect(onCommit).not.toHaveBeenCalled();
  expect(box().value).toBe("1");
});
