import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { BooksProvider } from "@/lib/character/books";
import { CatalogPicker, type Pickable, PickerList } from "./CatalogPicker";

const tr = (name: string) => (name === "Lined Coat" ? "ライナーコート" : name);

type Item = Pickable & { cost: number };

const items: Item[] = [
  { id: "a", name: "Lined Coat", category: "Armor", source: "SR5", cost: 1300 },
  { id: "b", name: "Armor Jacket", category: "Armor", source: "SR5", cost: 1000 },
  { id: "c", name: "Chameleon Suit", category: "Cloaks", source: "RG", cost: 1500 },
];

function setup(props: { limit?: number } = {}, books?: string[]) {
  const onAdd = vi.fn();
  render(
    <BooksProvider books={books}>
      <CatalogPicker
        items={items}
        label="防具を検索"
        tr={tr}
        describe={(item) => `${item.cost}¥`}
        onAdd={onAdd}
        {...props}
      />
    </BooksProvider>,
  );
  return { onAdd };
}

describe("CatalogPicker", () => {
  // The idle list used to be SR5 only whatever the settings said, so enabling
  // a book changed nothing until you typed: 202 armours, 12 on offer.
  it("lists everything the enabled books allow, with no search", () => {
    setup();
    expect(screen.getByText("ライナーコート")).toBeDefined();
    expect(screen.getByText("Chameleon Suit")).toBeDefined();
  });

  it("narrows the idle list to the settings' books", () => {
    setup({}, ["SR5"]);
    expect(screen.getByText("ライナーコート")).toBeDefined();
    expect(screen.queryByText("Chameleon Suit")).toBeNull();

    // and a search does not smuggle the disabled book back in
    fireEvent.change(screen.getByRole("searchbox", { name: "防具を検索" }), {
      target: { value: "chameleon" },
    });
    expect(screen.queryByText("Chameleon Suit")).toBeNull();
  });

  it("searches the translated name as well as the English one", () => {
    setup();
    const box = screen.getByRole("searchbox", { name: "防具を検索" });

    fireEvent.change(box, { target: { value: "ライナー" } });
    expect(screen.getByText("ライナーコート")).toBeDefined();
    expect(screen.queryByText("Armor Jacket")).toBeNull();

    fireEvent.change(box, { target: { value: "chameleon" } });
    expect(screen.getByText("Chameleon Suit")).toBeDefined();
  });

  it("reports the rows it cut off instead of dropping them silently", () => {
    setup({ limit: 1 });
    expect(screen.getByRole("status").textContent).toContain("他 2 件");
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
    expect(screen.getAllByRole("button", { name: /^(すべて|Armor|Cloaks)$/ }).length).toBe(3);
    fireEvent.click(screen.getByRole("button", { name: "Armor" }));
    expect(screen.getByText("ライナーコート")).toBeDefined();
    // "Cloaks" holds a single RG item. The chip used to select an empty list,
    // because the chips came from the enabled books and the rows from SR5.
    fireEvent.click(screen.getByRole("button", { name: "Cloaks" }));
    expect(screen.getByText("Chameleon Suit")).toBeDefined();
  });

  it("drops a chip whose book the settings turned off", () => {
    setup({}, ["SR5"]);
    expect(screen.queryByRole("button", { name: "Cloaks" })).toBeNull();
  });

  it("names each buy button after its row", () => {
    const { onAdd } = setup();
    // not twenty buttons all called "購入"
    fireEvent.click(screen.getByRole("button", { name: "ライナーコート を購入" }));
    expect(onAdd).toHaveBeenCalledWith(items[0]);
  });
});

describe("CatalogPicker under a settings book list", () => {
  it("hides a disabled book even from a search", () => {
    // the idle list is SR5-only anyway; the book filter has to survive the
    // search that normally reaches the supplements
    setup({}, ["SR5"]);
    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "suit" } });
    expect(screen.queryByText("Chameleon Suit")).toBeNull();
    expect(screen.getByRole("status").textContent).toContain("該当なし");
  });

  it("drops the category chip of a book that is off", () => {
    setup({}, ["SR5"]);
    expect(screen.queryByRole("button", { name: "Cloaks" })).toBeNull();
  });

  it("still shows the book once it is enabled", () => {
    setup({}, ["SR5", "RG"]);
    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "suit" } });
    expect(screen.getByText("Chameleon Suit")).toBeDefined();
  });
});

describe("PickerList", () => {
  it("renders up to the limit and names what it left out", () => {
    render(
      <PickerList items={["a", "b", "c"]} limit={2}>
        {(id) => <div key={id}>{id}</div>}
      </PickerList>,
    );
    expect(screen.getByText("a")).toBeDefined();
    expect(screen.queryByText("c")).toBeNull();
    expect(screen.getByRole("status").textContent).toContain("他 1 件");
  });

  it("carries the idle note only while it applies", () => {
    const { unmount } = render(
      <PickerList items={["a"]} note="gear.idleDrugs">
        {(id) => <div key={id}>{id}</div>}
      </PickerList>,
    );
    expect(screen.getByRole("status").textContent).toContain("SR5 とドラッグのみ表示中");
    unmount();

    render(<PickerList items={["a"]}>{(id) => <div key={id}>{id}</div>}</PickerList>);
    expect(screen.getByRole("status").textContent).toBe("");
  });
});
