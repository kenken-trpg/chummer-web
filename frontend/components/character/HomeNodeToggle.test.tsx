import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { HomeNodeToggle } from "@/components/character/HomeNodeToggle";
import { makeCharacter, testUi } from "@/tests/fixtures";

function renderToggle(core: boolean, homeNode = "", patch = vi.fn()) {
  const ch = makeCharacter({
    home_node: homeNode,
    derived: { condition_monitor: { physical: 10, stun: 0, core } },
  });
  render(<HomeNodeToggle id="deck" ch={ch} d={ch.derived} ui={testUi} patch={patch} />);
  return patch;
}

describe("<HomeNodeToggle>", () => {
  it("is offered to an A.I. only", () => {
    renderToggle(false);
    expect(screen.queryByLabelText("Home Node")).toBeNull();
  });

  it("marks the device, and clears the mark", () => {
    const patch = renderToggle(true);
    fireEvent.click(screen.getByLabelText("Home Node"));
    expect(patch).toHaveBeenCalledWith({ home_node: "deck" });
    document.body.innerHTML = "";
    const again = renderToggle(true, "deck");
    expect((screen.getByLabelText("Home Node") as HTMLInputElement).checked).toBe(true);
    fireEvent.click(screen.getByLabelText("Home Node"));
    expect(again).toHaveBeenCalledWith({ home_node: "" });
  });
});
