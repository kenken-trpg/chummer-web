import { fireEvent, render, screen } from "@testing-library/react";
import { Menu } from "@/components/character/Menu";

/** The panel's box as the browser would lay it out; happy-dom lays out nothing. */
function placePanel(right: number) {
  return vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue({
    right,
    left: right - 300,
    top: 0,
    bottom: 0,
    width: 300,
    height: 0,
    x: 0,
    y: 0,
    toJSON: () => ({}),
  });
}

function panel() {
  return screen.getByRole("button", { name: "item" }).parentElement!;
}

describe("Menu", () => {
  afterEach(() => vi.restoreAllMocks());

  it("hangs the panel from the button's right edge when the left one would run off the window", () => {
    const width = document.documentElement.clientWidth;
    placePanel(width + 40);
    render(
      <Menu label="書き出し">
        <button className="btn">item</button>
      </Menu>,
    );
    fireEvent.click(screen.getByRole("button", { name: "書き出し ▾" }));
    expect(panel().classList.contains("menu-body-end")).toBe(true);
  });

  it("keeps the panel on the left edge when it fits, and starts over on the next open", () => {
    const width = document.documentElement.clientWidth;
    const spy = placePanel(width + 40);
    render(
      <Menu label="書き出し">
        <button className="btn">item</button>
      </Menu>,
    );
    const toggle = screen.getByRole("button", { name: "書き出し ▾" });
    fireEvent.click(toggle);
    fireEvent.click(toggle);
    // the toolbar wrapped, say, and the button is no longer at the edge
    spy.mockReturnValue({
      right: width - 100,
      left: width - 400,
      top: 0,
      bottom: 0,
      width: 300,
      height: 0,
      x: 0,
      y: 0,
      toJSON: () => ({}),
    });
    fireEvent.click(toggle);
    expect(panel().classList.contains("menu-body-end")).toBe(false);
  });
});
