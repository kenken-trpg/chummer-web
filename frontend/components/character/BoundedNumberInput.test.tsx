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

it("takes any count over the minimum when there is no maximum", () => {
  const onCommit = vi.fn();
  render(<BoundedNumberInput aria-label="months" min={1} value={1} onCommit={onCommit} />);
  const months = screen.getByLabelText("months") as HTMLInputElement;
  expect(months.hasAttribute("max")).toBe(false);
  fireEvent.change(months, { target: { value: "" } });
  fireEvent.change(months, { target: { value: "36" } });
  expect(onCommit).toHaveBeenCalledTimes(1);
  expect(onCommit).toHaveBeenCalledWith(36);
});

it("lets a negative value be typed one key at a time", () => {
  const onCommit = vi.fn();
  render(<BoundedNumberInput aria-label="bonus" min={-999} value={0} onCommit={onCommit} />);
  const bonus = screen.getByLabelText("bonus") as HTMLInputElement;
  // the minus sign alone is not a number yet (the box reads it as ""): the
  // old box sent 0 here, and the 0 that came back wiped the sign out
  fireEvent.change(bonus, { target: { value: "-" } });
  expect(onCommit).not.toHaveBeenCalled();
  fireEvent.change(bonus, { target: { value: "-2" } });
  expect(onCommit).toHaveBeenCalledWith(-2);
});
