import { expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { RangeInput } from "@/components/character/RangeInput";

function setup(props: Partial<Parameters<typeof RangeInput>[0]> = {}) {
  const onDraft = vi.fn();
  const onCommit = vi.fn();
  render(
    <RangeInput
      min={0}
      max={6}
      value={2}
      label="技能"
      onDraft={onDraft}
      onCommit={onCommit}
      {...props}
    />,
  );
  return { onDraft, onCommit };
}

it("draws one numbered stop per step", () => {
  setup();
  for (const n of ["0", "1", "2", "3", "4", "5", "6"]) {
    expect(screen.getByText(n)).toBeTruthy();
  }
});

it("marks the current value so the thumb's position is readable", () => {
  const { container } = render(
    <RangeInput min={0} max={6} value={4} onDraft={() => {}} onCommit={() => {}} />,
  );
  const here = container.querySelectorAll(".range-tick.here");
  expect(here.length).toBe(1);
  expect(here[0].textContent).toBe("4");
});

it("marks the floor separately from the current value", () => {
  const { container } = render(
    <RangeInput min={1} max={6} value={3} floor={1} onDraft={() => {}} onCommit={() => {}} />,
  );
  expect(container.querySelector(".range-tick.floor")?.textContent).toBe("1");
});

it("labels only every Nth stop once the numbers would collide", () => {
  const { container } = render(
    <RangeInput min={0} max={40} value={0} onDraft={() => {}} onCommit={() => {}} />,
  );
  // 41 stops are all drawn as ticks, but far fewer carry a number
  expect(container.querySelectorAll(".range-tick").length).toBe(41);
  const labelled = container.querySelectorAll(".range-tick em").length;
  expect(labelled).toBeGreaterThan(2);
  expect(labelled).toBeLessThanOrEqual(15);
});

it("drafts on drag and commits on release", () => {
  const { onDraft, onCommit } = setup();
  const slider = screen.getByRole("slider");
  fireEvent.change(slider, { target: { value: "5" } });
  expect(onDraft).toHaveBeenCalledWith(5);
  expect(onCommit).not.toHaveBeenCalled();
  fireEvent.mouseUp(slider, { target: { value: "5" } });
  expect(onCommit).toHaveBeenCalledWith(5);
});

it("shows a value stranded outside the range at the nearest end", () => {
  // a Human BOD 1 kept after a swap to Troll, whose floor is 5: the input's
  // own value would be off its track, and the thumb would lie about it
  const { container } = render(
    <RangeInput min={5} max={10} value={1} floor={5} onDraft={() => {}} onCommit={() => {}} />,
  );
  expect(screen.getByRole("slider").getAttribute("value")).toBe("5");
  expect(container.querySelector(".range-tick.here")?.textContent).toBe("5");
});

it.each(["keyUp", "mouseUp", "touchEnd"] as const)(
  "does not commit again on blur after %s",
  (release) => {
    const { onCommit } = setup();
    const slider = screen.getByRole("slider");
    fireEvent.change(slider, { target: { value: "4" } });
    fireEvent[release](slider, { target: { value: "4" } });
    fireEvent.blur(slider);
    expect(onCommit).toHaveBeenCalledExactlyOnceWith(4);
  },
);

it("commits a pending draft on blur and accepts a later change", () => {
  const { onCommit } = setup();
  const slider = screen.getByRole("slider");
  fireEvent.change(slider, { target: { value: "3" } });
  fireEvent.blur(slider, { target: { value: "3" } });
  fireEvent.change(slider, { target: { value: "5" } });
  fireEvent.keyUp(slider, { target: { value: "5" } });
  expect(onCommit.mock.calls).toEqual([[3], [5]]);
});

it("does not add history for focus or release without a change", () => {
  const { onCommit } = setup();
  const slider = screen.getByRole("slider");
  fireEvent.focus(slider);
  fireEvent.keyUp(slider);
  fireEvent.mouseUp(slider);
  fireEvent.blur(slider);
  expect(onCommit).not.toHaveBeenCalled();
});
