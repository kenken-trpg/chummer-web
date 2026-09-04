import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CatalogPicker, type Pickable } from "./CatalogPicker";

const tr = (name: string) => (name === "Lined Coat" ? "ライナーコート" : name);

type Item = Pickable & { cost: number };

const items: Item[] = [
  { id: "a", name: "Lined Coat", category: "Armor", source: "SR5", cost: 1300 },
  { id: "b", name: "Armor Jacket", category: "Armor", source: "SR5", cost: 1000 },
  { id: "c", name: "Chameleon Suit", category: "Cloaks", source: "RG", cost: 1500 },
];

function setup(props: { limit?: number } = {}) {
  const onAdd = vi.fn();
  render(
    <CatalogPicker
      items={items}
      label="防具を検索"
      tr={tr}
      describe={(item) => `${item.cost}¥`}
      onAdd={onAdd}
      {...props}
    />,
  );
  return { onAdd };
}

describe("CatalogPicker", () => {
  it("lists core-rulebook entries only until you search, and says so", () => {
    setup();
    expect(screen.getByText("ライナーコート")).toBeDefined();
    expect(screen.queryByText("Chameleon Suit")).toBeNull();
    // the SR5-only default used to be invisible: an item was simply "missing"
    expect(screen.getByRole("status").textContent).toContain("SR5 のみ表示中");
  });

  it("searches the translated name as well as the English one", () => {
    setup();
    const box = screen.getByRole("searchbox", { name: "防具を検索" });

    fireEvent.change(box, { target: { value: "ライナー" } });
    expect(screen.getByText("ライナーコート")).toBeDefined();
    expect(screen.queryByText("Armor Jacket")).toBeNull();

    // and a search reaches past SR5 into the supplements
    fireEvent.change(box, { target: { value: "chameleon" } });
    expect(screen.getByText("Chameleon Suit")).toBeDefined();
  });

  it("reports the rows it cut off instead of dropping them silently", () => {
    setup({ limit: 1 });
    expect(screen.getByRole("status").textContent).toContain("他 1 件");
  });

  it("says so when nothing matches", () => {
    setup();
    fireEvent.change(screen.getByRole("searchbox", { name: "防具を検索" }), {
      target: { value: "zzz" },
    });
    expect(screen.getByRole("status").textContent).toContain("該当なし");
  });

  it("filters by category chip, and only offers chips that have rows", () => {
    setup();
    // "Cloaks" holds a single RG item, which the idle list does not show
    expect(screen.getAllByRole("button", { name: /^(すべて|Armor|Cloaks)$/ }).length).toBe(3);
    fireEvent.click(screen.getByRole("button", { name: "Armor" }));
    expect(screen.getByText("ライナーコート")).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: "Cloaks" }));
    expect(screen.getByRole("status").textContent).toContain("該当なし");
  });

  it("names each buy button after its row", () => {
    const { onAdd } = setup();
    // not twenty buttons all called "購入"
    fireEvent.click(screen.getByRole("button", { name: "ライナーコート を購入" }));
    expect(onAdd).toHaveBeenCalledWith(items[0]);
  });
});
