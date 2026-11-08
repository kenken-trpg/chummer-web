import { fireEvent, render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { ActiveMatrixDevice } from "@/components/character/tabs/gear/ActiveMatrixDevice";
import { makeCharacter, panelProps } from "@/tests/fixtures";

const device = (id: string, name: string, dataprocessing: number) => ({
  id,
  gear_id: `${id}-id`,
  name,
  rating: 1,
  rating_max: 0,
  device_rating: dataprocessing,
  dataprocessing,
  firewall: 1,
  nuyen: 100,
});

const meta = device("meta", "Meta Link", 1);
const avalon = device("avalon", "Transys Avalon", 6);
const deck = device("deck", "Erika MCD-1", 2);

function picker() {
  return screen.getByRole("combobox", { name: /マトリックスで使う機器/ });
}

describe("<ActiveMatrixDevice>", () => {
  it("lists automatic and every device, with its Data Processing", () => {
    const ch = makeCharacter({
      derived: { commlinks: [meta, avalon], cyberdecks: [deck] },
    } as never);
    render(<ActiveMatrixDevice {...panelProps(ch)} />);
    const options = Array.from(picker().querySelectorAll("option")).map((o) => o.textContent);
    expect(options).toEqual([
      "自動（データ処理が最大のもの）",
      "Meta Link（データ処理 1）",
      "Transys Avalon（データ処理 6）",
      "Erika MCD-1（データ処理 2）",
    ]);
    expect((picker() as HTMLSelectElement).value).toBe("");
  });

  it("saves the pick, and an empty value goes back to automatic", () => {
    const patch = vi.fn();
    const ch = makeCharacter({ derived: { commlinks: [meta, avalon] } } as never);
    render(<ActiveMatrixDevice {...panelProps(ch, { patch })} />);
    fireEvent.change(picker(), { target: { value: "meta" } });
    expect(patch).toHaveBeenLastCalledWith({ active_matrix_device: "meta" });
    fireEvent.change(picker(), { target: { value: "" } });
    expect(patch).toHaveBeenLastCalledWith({ active_matrix_device: "" });
  });

  it("offers a technomancer their living persona", () => {
    const ch = makeCharacter({
      active_matrix_device: "living_persona",
      derived: {
        commlinks: [meta],
        living_persona: { device_rating: 3, attack: 3, sleaze: 3, dataprocessing: 4, firewall: 3 },
      },
    } as never);
    render(<ActiveMatrixDevice {...panelProps(ch)} />);
    expect((picker() as HTMLSelectElement).value).toBe("living_persona");
    expect(screen.getByRole("option", { name: "生体ペルソナ（データ処理 4）" })).toBeTruthy();
  });

  it("shows a pick of something no longer owned as automatic", () => {
    const ch = makeCharacter({
      active_matrix_device: "sold",
      derived: { commlinks: [meta, avalon] },
    } as never);
    render(<ActiveMatrixDevice {...panelProps(ch)} />);
    expect((picker() as HTMLSelectElement).value).toBe("");
  });

  it("stays hidden with nothing to choose between", () => {
    const ch = makeCharacter({ derived: { commlinks: [meta] } } as never);
    render(<ActiveMatrixDevice {...panelProps(ch)} />);
    expect(screen.queryByRole("combobox")).toBeNull();
  });

  it("stays hidden for an A.I., which runs from its home node", () => {
    const ch = makeCharacter({
      derived: {
        commlinks: [meta, avalon],
        condition_monitor: { physical: 0, stun: 0, overflow: 0, core: 10 },
      },
    } as never);
    render(<ActiveMatrixDevice {...panelProps(ch)} />);
    expect(screen.queryByRole("combobox")).toBeNull();
  });
});
