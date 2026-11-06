/** The attribute selects of a Fuchi Cyber-N / Cyber-Ex (KC p.60). */
import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";
import { CustomDeckAttributes } from "./CustomDeckAttributes";

const part = (id: string, attr: string, decks = ["Fuchi Cyber-N", "Fuchi Cyber-Ex"]) => ({
  id,
  name: `[Custom Cyberdeck] ${attr}`,
  category: "Custom Cyberdeck Attributes",
  required_names: decks,
});

const catalog = {
  gear: [
    part("atk", "Attack"),
    part("slz", "Sleaze"),
    part("dp", "Data Processing"),
    part("fw-ex", "Firewall", ["Fuchi Cyber-Ex"]),
    part("fw-n", "Firewall", ["Fuchi Cyber-N"]),
  ],
};

function renderAttrs(saved: Record<string, unknown>[], deckName = "Fuchi Cyber-Ex") {
  const patch = vi.fn<(body: Record<string, unknown>) => void>();
  const derived = saved.map((row) => ({ ...row, nuyen: 13500, name: "x" }));
  const ch = makeCharacter({ gear: saved, derived: { gear: derived } } as never);
  render(
    <CustomDeckAttributes
      {...panelProps(ch, { catalog: makeCatalog(catalog as never), patch })}
      deckId="deck"
      deckName={deckName}
      deckRating={4}
    />,
  );
  return patch;
}

it("offers each attribute from 0 to the deck's rating", () => {
  renderAttrs([]);
  const atk = screen.getByLabelText("Fuchi Cyber-Ex: ATK") as HTMLSelectElement;
  expect([...atk.options].map((o) => o.value)).toEqual(["0", "1", "2", "3", "4"]);
  expect(atk.value).toBe("0");
  expect(screen.getByLabelText("Fuchi Cyber-Ex: FW")).toBeDefined();
});

it("buys an attribute as a part in the deck", () => {
  const patch = renderAttrs([]);
  fireEvent.change(screen.getByLabelText("Fuchi Cyber-Ex: FW"), { target: { value: "3" } });
  expect(patch).toHaveBeenCalledWith({
    gear: [{ gear_id: "fw-ex", parent_id: "deck", qty: 1, rating: 3 }],
  });
});

it("changes the rating of one already bought, and 0 takes it out", () => {
  const bought = { id: "a1", gear_id: "atk", parent_id: "deck", qty: 1, rating: 2 };
  const patch = renderAttrs([bought]);
  const atk = screen.getByLabelText("Fuchi Cyber-Ex: ATK") as HTMLSelectElement;
  expect(atk.value).toBe("2");
  fireEvent.change(atk, { target: { value: "4" } });
  expect(patch).toHaveBeenLastCalledWith({ gear: [{ ...bought, rating: 4 }] });
  fireEvent.change(atk, { target: { value: "0" } });
  expect(patch).toHaveBeenLastCalledWith({ gear: [] });
});

it("shows nothing on a deck whose attributes are fixed", () => {
  renderAttrs([], "Fuchi Cyber-4");
  expect(screen.queryByLabelText("Fuchi Cyber-4: ATK")).toBeNull();
});
