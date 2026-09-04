import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AddonSelect } from "./AddonSelect";

const options = [
  { id: "m1", name: "Smartgun System", cost: 200 },
  { id: "m2", name: "Silencer", cost: 500 },
];

describe("AddonSelect", () => {
  it("names the control after the row it modifies", () => {
    render(
      <AddonSelect
        rowName="Ares Predator V"
        prompt="改造を追加"
        options={options}
        onAdd={vi.fn()}
        tr={(n) => n}
      />,
    );
    // without rowName this is one of a dozen bare "combobox"es on the panel
    expect(screen.getByRole("combobox", { name: "Ares Predator V: 改造を追加" })).toBeDefined();
    expect(screen.getByRole("button", { name: "Ares Predator V: 装着" })).toBeDefined();
  });

  it("stays disabled until something is picked, then reports and resets", () => {
    const onAdd = vi.fn();
    render(
      <AddonSelect
        rowName="Ares Predator V"
        prompt="改造を追加"
        options={options}
        onAdd={onAdd}
        tr={(n) => n}
      />,
    );
    const select = screen.getByRole("combobox") as HTMLSelectElement;
    const add = screen.getByRole("button") as HTMLButtonElement;
    expect(add.disabled).toBe(true);

    fireEvent.change(select, { target: { value: "m2" } });
    expect(add.disabled).toBe(false);
    fireEvent.click(add);

    // the second argument is the optional `extra` target, unused here
    expect(onAdd).toHaveBeenCalledWith(options[1], undefined);
    // the selection is the component's own, and clears itself after the add
    expect(select.value).toBe("");
    expect(add.disabled).toBe(true);
  });

  it("asks for a target only for the options that need one", () => {
    const onAdd = vi.fn();
    render(
      <AddonSelect
        rowName="Erika MCD-1"
        prompt="アプリを追加"
        options={options}
        tr={(n) => n}
        extraFor={(o) => (o.id === "m1" ? { label: "技能", values: ["Pistols"] } : null)}
        onAdd={onAdd}
      />,
    );
    const select = screen.getByRole("combobox", { name: "Erika MCD-1: アプリを追加" });

    fireEvent.change(select, { target: { value: "m2" } });
    expect(screen.queryByRole("combobox", { name: /技能/ })).toBeNull();

    fireEvent.change(select, { target: { value: "m1" } });
    const extra = screen.getByRole("combobox", { name: "Erika MCD-1: 技能" });
    fireEvent.change(extra, { target: { value: "Pistols" } });
    fireEvent.click(screen.getByRole("button", { name: "Erika MCD-1: 装着" }));

    expect(onAdd).toHaveBeenCalledWith(options[0], "Pistols");
  });

  it("renders nothing when the row takes no addons", () => {
    const { container } = render(
      <AddonSelect
        rowName="Colt America L36"
        prompt="改造を追加"
        options={[]}
        onAdd={vi.fn()}
        tr={(n) => n}
      />,
    );
    expect(container.innerHTML).toBe("");
  });
});
