import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { CritterPowersTab } from "@/components/character/tabs/CritterPowersTab";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";
import type { BuyableCritterPower, InstalledCritterPower } from "@/lib/types";

const power = (name: string, extra: Partial<BuyableCritterPower> = {}): BuyableCritterPower => ({
  id: name.toLowerCase(),
  name,
  category: "Infected",
  type: "P",
  action: "Auto",
  range: "Self",
  duration: "Always",
  karma: 9,
  has_rating: false,
  needs_extra: false,
  source: "DTR",
  page: "170",
  ...extra,
});

const catalog = makeCatalog({
  buyable_critter_powers: [
    power("Evolved Reflexes", { karma: 12 }),
    power("Mimicry"),
    power("Silence"),
    power("Mystic Armor (Infected)", { karma: 6, has_rating: true }),
  ],
});

const owned = (
  name: string,
  extra: Partial<InstalledCritterPower> = {},
): InstalledCritterPower => ({
  ...power(name),
  id: `own-${name}`,
  power_id: name.toLowerCase(),
  label: name,
  rating: null,
  extra: "",
  ...extra,
});

function renderTab(
  powers: InstalledCritterPower[] = [],
  patch: (b: Record<string, unknown>) => void = () => {},
  offer = ["evolved reflexes", "mimicry", "mystic armor (infected)"],
) {
  const ch = makeCharacter({
    critter_powers: powers.map((p) => ({ id: p.id, power_id: p.power_id, rating: p.rating })),
    derived: {
      enabled_tabs: ["critter"],
      critter_powers: powers,
      critter_power_offer: offer,
      critter_power_categories: ["Infected"],
    },
  });
  return render(<CritterPowersTab {...panelProps(ch, { catalog, patch })} />);
}

const pickerNames = () =>
  [...document.querySelectorAll(".quality-list .quality-item b")].map((el) => el.textContent);

describe("CritterPowersTab", () => {
  it("offers only what the engine says the character can buy", () => {
    renderTab();
    // Silence is a Banshee's: in the stock, not in the offer
    expect(pickerNames()).toEqual(["Evolved Reflexes", "Mimicry", "Mystic Armor (Infected)"]);
    expect(screen.getByText(/Infected/, { selector: "p" })).toBeTruthy();
  });

  it("adds a power, at rating 1 when it is bought at a rating", () => {
    const patch = vi.fn();
    renderTab([], patch);
    const row = (name: string) =>
      [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
        el.querySelector("b")?.textContent?.includes(name),
      ) as HTMLElement;
    fireEvent.click(row("Mimicry").querySelector("button.btn")!);
    expect(patch).toHaveBeenLastCalledWith({ critter_powers: [{ power_id: "mimicry" }] });
    fireEvent.click(row("Mystic Armor").querySelector("button.btn")!);
    expect(patch).toHaveBeenLastCalledWith({
      critter_powers: [{ power_id: "mystic armor (infected)", rating: 1 }],
    });
  });

  it("lists what was bought with its karma, and edits a rating", () => {
    const patch = vi.fn();
    renderTab(
      [
        owned("Evolved Reflexes", { karma: 12 }),
        owned("Mystic Armor (Infected)", { has_rating: true, rating: 2, karma: 6 }),
      ],
      patch,
    );
    expect(screen.getByText(/2 個 \/ 18 カルマ/)).toBeTruthy();
    fireEvent.change(screen.getByRole("spinbutton"), { target: { value: "4" } });
    expect(patch).toHaveBeenLastCalledWith({
      critter_powers: [
        { id: "own-Evolved Reflexes", power_id: "evolved reflexes", rating: null },
        { id: "own-Mystic Armor (Infected)", power_id: "mystic armor (infected)", rating: 4 },
      ],
    });
  });

  it("says so when nothing can be bought", () => {
    renderTab([], () => {}, []);
    expect(screen.getByText("今の資質で買えるクリッター・パワーはありません")).toBeTruthy();
  });
});
