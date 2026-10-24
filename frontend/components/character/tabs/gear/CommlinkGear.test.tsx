import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
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

  it("shows a loose Mapsoft and lets the player load it into a commlink", () => {
    const app = {
      id: "mapsoft",
      gear_id: "mapsoft-id",
      name: "Mapsoft",
      label: "Mapsoft (Seattle)",
      parent_id: null,
      nuyen: 100,
    };
    const ch = makeCharacter({
      commlinks: [{ id: "link", gear_id: "ikon" }],
      apps: [app],
      derived: { commlinks: [row], apps: [app] },
    } as never);
    const patch = vi.fn();
    render(<CommlinkGear {...panelProps(ch, { patch })} />);

    expect(screen.getByText(/Mapsoft \(Seattle\) \/ 100¥/)).toBeTruthy();
    fireEvent.change(screen.getByRole("combobox", { name: "入れる先" }), {
      target: { value: "link" },
    });
    expect(patch).toHaveBeenCalledWith({ apps: [{ ...app, parent_id: "link" }] });
  });
});
