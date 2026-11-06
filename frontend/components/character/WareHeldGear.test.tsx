import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { WareHeldGear } from "@/components/character/WareHeldGear";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";
import type { InstalledWare } from "@/lib/types";

const housing = {
  id: "head",
  ware_id: "commlink-ware",
  name: "Commlink",
  category: "Headware",
  rating: 1,
  grade: "Standard",
  wireless: true,
  essence: 0.2,
  nuyen: 2000,
  allow_gear: ["Commlinks"],
} as InstalledWare;

const catalog = makeCatalog({
  commlinks: [{ id: "ikon", name: "Hermes Ikon", category: "Commlinks", cost: "3000" }],
} as never);

function renderHeld(implanted: boolean, patch = vi.fn()) {
  const ch = makeCharacter({
    commlinks: implanted ? [{ id: "link", gear_id: "ikon", parent_id: "head" }] : [],
    derived: {
      commlinks: implanted
        ? [{ id: "link", gear_id: "ikon", name: "Hermes Ikon", parent_id: "head" }]
        : [],
    },
  } as never);
  render(
    <WareHeldGear
      item={housing}
      catalog={catalog}
      character={ch}
      tr={identityTr}
      ui={testUi}
      patch={patch}
    />,
  );
  return patch;
}

describe("<WareHeldGear> with a headware Commlink", () => {
  it("puts a commlink in from the commlink list", () => {
    const patch = renderHeld(false);
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "ikon" } });
    fireEvent.click(screen.getByRole("button", { name: "Commlink: 入れる" }));
    expect(patch).toHaveBeenCalledWith({
      commlinks: [{ gear_id: "ikon", parent_id: "head", rating: 1, qty: 1 }],
    });
  });

  it("lists the implanted commlink and takes it out, offering no second one", () => {
    const patch = renderHeld(true);
    expect(screen.getByText("Hermes Ikon")).toBeTruthy();
    expect(screen.queryByRole("combobox")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "取り出す" }));
    expect(patch).toHaveBeenCalledWith({
      commlinks: [{ id: "link", gear_id: "ikon", parent_id: null }],
    });
  });
});

const jack = {
  id: "dj",
  ware_id: "datajack-plus",
  name: "Datajack Plus",
  category: "Headware",
  rating: 2,
  grade: "Standard",
  wireless: true,
  essence: 0.15,
  nuyen: 7000,
  allow_gear: ["Common Programs", "Hacking Programs"],
  program_max: 2,
} as InstalledWare;

const programCatalog = makeCatalog({
  programs: [
    {
      id: "armor",
      name: "Armor",
      category: "Common Programs",
      cost: "250",
      program_host: "cyberdecks",
    },
    {
      id: "exploit",
      name: "Exploit",
      category: "Hacking Programs",
      cost: "250",
      program_host: "cyberdecks",
    },
    { id: "clear", name: "Clearsight", category: "Autosofts", cost: "500", program_host: "rccs" },
  ],
} as never);

function renderJack(stored: string[], patch = vi.fn()) {
  const ch = makeCharacter({
    programs: stored.map((id) => ({ id: `p-${id}`, gear_id: id, parent_id: "dj" })),
    derived: {
      programs: stored.map((id) => ({
        id: `p-${id}`,
        gear_id: id,
        name: id === "armor" ? "Armor" : "Exploit",
        category: "Common Programs",
        rating: 1,
        rating_max: 0,
        parent_id: "dj",
        nuyen: 250,
      })),
    },
  } as never);
  render(
    <WareHeldGear
      item={jack}
      catalog={programCatalog}
      character={ch}
      tr={identityTr}
      ui={testUi}
      patch={patch}
    />,
  );
  return patch;
}

describe("<WareHeldGear> with a Datajack Plus", () => {
  it("offers the program categories it stores and puts one in", () => {
    const patch = renderJack([]);
    const options = [...screen.getByRole("combobox").querySelectorAll("option")].map(
      (o) => o.textContent,
    );
    expect(options.some((o) => o?.includes("Armor"))).toBe(true);
    expect(options.some((o) => o?.includes("Clearsight"))).toBe(false);
    fireEvent.change(screen.getByRole("combobox"), { target: { value: "exploit" } });
    fireEvent.click(screen.getByRole("button", { name: "Datajack Plus: 入れる" }));
    expect(patch).toHaveBeenCalledWith({
      programs: [{ gear_id: "exploit", rating: 1, parent_id: "dj", running: false }],
    });
  });

  it("lists what it stores and stops offering once it is full", () => {
    const patch = renderJack(["armor", "exploit"]);
    expect(screen.getByText("入っているプログラム 2/2")).toBeTruthy();
    expect(screen.getByText("Armor")).toBeTruthy();
    expect(screen.queryByRole("combobox")).toBeNull();
    fireEvent.click(screen.getAllByRole("button", { name: "外す" })[0]);
    expect(patch).toHaveBeenCalledWith({
      programs: [{ id: "p-exploit", gear_id: "exploit", parent_id: "dj" }],
    });
  });
});
