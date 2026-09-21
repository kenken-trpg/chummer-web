import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { Character } from "@/lib/types";
import { makeCharacter, panelProps } from "@/tests/fixtures";
import { WeaponGear } from "@/components/character/tabs/gear/WeaponGear";
import { makeCatalog } from "@/tests/fixtures";

/** The Black Market Pipeline takes 10% off one item at a time, in its own
 *  category — so the box shows only where that category reaches. */
function renderWeapons(derivedExtra: Record<string, unknown>, patch = vi.fn()) {
  const weapon = {
    id: "w1",
    weapon_id: "c-w1",
    name: "Ares Predator V",
    category: "Heavy Pistols",
    qty: 1,
    nuyen: 725,
    accessories: [],
  };
  const character = makeCharacter({
    weapons: [{ id: "w1", weapon_id: "c-w1" }],
    derived: { weapons: [weapon], ...derivedExtra },
  } as never) as Character;
  render(<WeaponGear {...panelProps(character, { catalog: makeCatalog({}), patch })} />);
  return patch;
}

describe("<DiscountToggle>", () => {
  it("is absent without the quality, and absent when its category is elsewhere", () => {
    renderWeapons({});
    expect(screen.queryByLabelText("闇市")).toBeNull();
    renderWeapons({ black_market_discount: true, black_market_category: "Armor" });
    expect(screen.queryByLabelText("闇市")).toBeNull();
  });

  it("marks the one item it is ticked on", () => {
    const patch = renderWeapons({
      black_market_discount: true,
      black_market_category: "Weapons",
    });
    fireEvent.click(screen.getByLabelText("闇市"));
    expect(patch.mock.calls[0][0]).toEqual({
      weapons: [{ id: "w1", weapon_id: "c-w1", discounted: true }],
    });
  });
});
