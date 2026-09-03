import { render, screen } from "@testing-library/react";
import { TabBar } from "@/components/character/TabBar";

describe("<TabBar>", () => {
  it("hides the awakened / emerged tabs until the engine enables them", () => {
    const { rerender } = render(<TabBar tab="priority" setTab={vi.fn()} enabledTabs={[]} />);
    expect(screen.queryByRole("button", { name: "術式" })).toBeNull();

    rerender(<TabBar tab="priority" setTab={vi.fn()} enabledTabs={["spells"]} />);
    expect(screen.getByRole("button", { name: "術式" })).toBeDefined();
  });

  // The bar is a landmark a screen reader can jump to, and the active tab is
  // marked so it is not just "the one that looks different".
  it("is a named nav landmark whose active tab is aria-current", () => {
    render(<TabBar tab="skills" setTab={vi.fn()} enabledTabs={[]} />);

    expect(screen.getByRole("navigation", { name: "セクション" })).toBeDefined();
    expect(screen.getByRole("button", { name: "技能" }).getAttribute("aria-current")).toBe("true");
    expect(screen.getByRole("button", { name: "能力値" }).getAttribute("aria-current")).toBeNull();
  });
});
