import { render, screen } from "@testing-library/react";
import { CommlinkGear } from "@/components/character/tabs/gear/CommlinkGear";
import { makeCharacter, panelProps } from "@/tests/fixtures";

const row = {
  id: "link",
  gear_id: "ikon",
  name: "Hermes Ikon",
  rating: 1,
  rating_max: 0,
  device_rating: 5,
  dataprocessing: 5,
  firewall: 6,
  nuyen: 3000,
};

describe("<CommlinkGear>", () => {
  it("says which implant a commlink sits in", () => {
    const ch = makeCharacter({
      commlinks: [{ id: "link", gear_id: "ikon", parent_id: "head" }],
      derived: { commlinks: [{ ...row, parent_id: "head", implanted_in: "Commlink" }] },
    } as never);
    render(<CommlinkGear {...panelProps(ch)} />);
    expect(screen.getByText("Commlink に埋め込み")).toBeTruthy();
  });

  it("says nothing of a carried one", () => {
    const ch = makeCharacter({
      commlinks: [{ id: "link", gear_id: "ikon" }],
      derived: { commlinks: [row] },
    } as never);
    render(<CommlinkGear {...panelProps(ch)} />);
    expect(screen.queryByText(/に埋め込み/)).toBeNull();
  });
});
