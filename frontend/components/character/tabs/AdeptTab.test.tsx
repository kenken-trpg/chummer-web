import { useState } from "react";
import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { AdeptTab } from "@/components/character/tabs/AdeptTab";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";

const power = {
  id: "imprv",
  name: "Improved Reflexes",
  points: 1.5,
  levels: false,
  maxlevels: 0,
  extrapointcost: 0,
  source: "SR5",
  required: [],
};
const power2 = { ...power, id: "combat", name: "Combat Sense" };

/** One installed power carrying every optional column the row can print. */
const installed = {
  id: "p1",
  name: "Improved Reflexes",
  cost: 0.75,
  full_cost: 1.5,
  discounted: true,
  can_discount: true,
  free_levels: 1,
  rating: 2,
  total_rating: 3,
  rating_min: 1,
  rating_max: 3,
  free_only: false,
  select: "attribute",
  extra: "AGI",
  options: ["AGI", "STR"],
  source: "SR5",
  notes: [],
};

const qiFocus = {
  id: "q1",
  name: "Improved Reflexes",
  rating: 6,
  rating_min: 1,
  rating_max: 12,
  power_rating: 1,
  power_rating_max: 3,
  nuyen: 18000,
  karma: 6,
  select: "attribute",
  extra: "AGI",
  options: ["AGI", "STR"],
};

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter({ talent: "Adept", ...over.character });
  return render(
    <AdeptTab
      {...panelProps(ch, {
        catalog: over.catalog ?? makeCatalog({ powers: [power, power2] as never }),
        patch: over.patch ?? (() => {}),
      })}
    />,
  );
}

const firstList = () => document.querySelectorAll(".quality-list")[0] as HTMLElement;
const rowButton = (list: HTMLElement, name: string) =>
  [...list.querySelectorAll(".quality-item")]
    .find((el) => el.textContent?.includes(name))!
    .querySelector("button") as HTMLButtonElement;

describe("<AdeptTab>", () => {
  it("renders the power-point line and the sub-section headings", () => {
    renderTab();
    expect(screen.getByText(/パワー点 0\/0/)).toBeDefined();
    expect(screen.getByRole("heading", { name: "Enhancement" })).toBeDefined();
    expect(screen.getByRole("heading", { name: "気焦点" })).toBeDefined();
  });

  it("adds a power from the catalog via patch", () => {
    const patch = vi.fn();
    renderTab({ patch });
    fireEvent.click(rowButton(firstList(), "Improved Reflexes"));
    expect(patch).toHaveBeenCalledWith({
      adept_powers: [{ power_id: "imprv", rating: 1, discounted: false }],
    });
  });

  it("filters the power catalog by search", () => {
    renderTab();
    fireEvent.change(screen.getByPlaceholderText("アデプトパワーを検索"), {
      target: { value: "combat" },
    });
    const names = [...firstList().querySelectorAll(".quality-item b")].map((b) => b.textContent);
    expect(names).toEqual(["Combat Sense"]);
  });

  it("adds an enhancement via patch", () => {
    const patch = vi.fn();
    renderTab({
      catalog: makeCatalog({
        powers: [power] as never,
        enhancements: [{ id: "e1", name: "Critical Strike", source: "SR5" }] as never,
      }),
      patch,
    });
    const enhList = [...document.querySelectorAll(".quality-list")].find((l) =>
      l.textContent?.includes("Critical Strike"),
    ) as HTMLElement;
    fireEvent.click(rowButton(enhList, "Critical Strike"));
    expect(patch).toHaveBeenCalledWith({ adept_enhancements: ["e1"] });
  });

  /**
   * The installed-power row is where every number the engine worked out shows
   * up — the discounted cost, the free levels a quality paid for, the total
   * rating after bonuses. The catalog row above it shows none of that, so a
   * row that renders the wrong one of these is invisible to the other tests.
   */
  it("shows what the engine worked out for an installed power", () => {
    renderTab({
      character: {
        adept_powers: [{ id: "p1", power_id: "imprv", rating: 2 }] as never,
        derived: { adept_powers: [installed] as never },
      },
    });
    const row = document.querySelector(".cyber-item") as HTMLElement;
    expect(row.textContent).toContain("0.75 PP");
    expect(row.textContent).toContain("（割引前 1.5）");
    expect(row.textContent).toContain("無料Lv 1");
    expect(row.textContent).toContain("合計R3");
  });

  it("edits an installed power's rating, option and Way discount through patch", () => {
    const patch = vi.fn();
    renderTab({
      character: {
        adept_powers: [{ id: "p1", power_id: "imprv", rating: 2 }] as never,
        derived: { adept_powers: [installed] as never },
      },
      patch,
    });

    fireEvent.change(screen.getByLabelText("レーティング"), { target: { value: "3" } });
    expect(patch).toHaveBeenLastCalledWith({
      adept_powers: [{ id: "p1", power_id: "imprv", rating: 3 }],
    });

    fireEvent.change(screen.getByLabelText("能力値"), { target: { value: "STR" } });
    expect(patch).toHaveBeenLastCalledWith({
      adept_powers: [{ id: "p1", power_id: "imprv", rating: 2, extra: "STR" }],
    });

    fireEvent.click(screen.getByLabelText("Way割引"));
    expect(patch).toHaveBeenLastCalledWith({
      adept_powers: [{ id: "p1", power_id: "imprv", rating: 2, discounted: false }],
    });

    fireEvent.click(screen.getByRole("button", { name: "削除" }));
    expect(patch).toHaveBeenLastCalledWith({ adept_powers: [] });
  });

  /**
   * A power a quality granted is not the character's to remove, and the row
   * has to say so rather than offering a delete that the engine would undo.
   */
  it("marks a free power as free and offers no delete", () => {
    renderTab({
      character: {
        derived: {
          adept_powers: [{ ...installed, free_only: true, can_discount: false }] as never,
        },
      },
    });
    const row = document.querySelector(".cyber-item") as HTMLElement;
    expect(row.textContent).toContain("無料");
    expect(row.querySelector("button.danger")).toBeNull();
    expect(screen.queryByLabelText("レーティング")).toBeNull();
  });

  /** The Way line only appears once a Way is actually taken (`max > 0`). */
  it("prints the Way discount line only when there is a Way", () => {
    const { unmount } = renderTab();
    expect(screen.queryByText(/Way割引 0\/2/)).toBeNull();
    unmount();

    renderTab({ character: { derived: { way_discount: { used: 0.5, max: 2 } } as never } });
    expect(screen.getByText(/Way割引 0.5\/2/)).toBeDefined();
  });

  /**
   * The Mystic Adept slider is how MAG is split between spellcasting and
   * power points, and it is the one control on this tab that is not a patch:
   * dragging repaints locally, only letting go writes.
   */
  it("gives the Mystic Adept a slider that drafts locally and commits on release", () => {
    const patch = vi.fn();
    const drafted: number[] = [];
    // The slider is controlled by the character the parent holds, so the draft
    // has to go back in for the thumb to move — a `vi.fn()` alone would leave
    // it at 0 and the release would commit that.
    function Harness() {
      const [ch, setCharacter] = useState(
        makeCharacter({ talent: "Mystic Adept", derived: { totals: { MAG: 5 } } as never }),
      );
      return (
        <AdeptTab
          {...panelProps(ch, {
            patch,
            setCharacter: (next) => {
              drafted.push((next as typeof ch).mystic_pp || 0);
              setCharacter(next as typeof ch);
            },
          })}
        />
      );
    }
    render(<Harness />);

    const slider = screen.getByLabelText("購入したパワー点（1点=5カルマ）");
    expect(slider.getAttribute("max")).toBe("5");
    fireEvent.change(slider, { target: { value: "3" } });
    expect(drafted).toEqual([3]);
    expect(patch).not.toHaveBeenCalled();
    fireEvent.mouseUp(slider);
    expect(patch).toHaveBeenCalledWith({ mystic_pp: 3 });
  });

  it("hides the slider for a plain Adept", () => {
    renderTab();
    expect(screen.queryByLabelText("購入したパワー点（1点=5カルマ）")).toBeNull();
  });

  it("removes an installed enhancement through patch", () => {
    const patch = vi.fn();
    renderTab({
      character: {
        adept_enhancements: ["e1"] as never,
        derived: { enhancements: [{ id: "e1", name: "Critical Strike", source: "SR5" }] as never },
      },
      patch,
    });
    fireEvent.click(screen.getByRole("button", { name: "削除" }));
    expect(patch).toHaveBeenCalledWith({ adept_enhancements: [] });
  });

  /**
   * Binding starts at the Force the power needs — `ceil(points / 0.25)` — not
   * at 1. A qi focus below that Force holds nothing, so a default of 1 would
   * hand the user a focus that cannot work.
   */
  it("binds a qi focus at the Force the power needs", () => {
    const patch = vi.fn();
    renderTab({ patch });
    const qiList = [...document.querySelectorAll(".quality-list")].at(-1) as HTMLElement;
    expect(qiList.textContent).toContain("Force 6〜");
    fireEvent.click(rowButton(qiList, "Improved Reflexes"));
    expect(patch).toHaveBeenCalledWith({
      qi_foci: [{ power_id: "imprv", rating: 6, power_rating: 1 }],
    });
  });

  it("edits and removes a bound qi focus", () => {
    const patch = vi.fn();
    renderTab({
      character: {
        qi_foci: [{ id: "q1", power_id: "imprv", rating: 6, power_rating: 1 }] as never,
        derived: { qi_foci: [qiFocus] as never },
      },
      patch,
    });
    const row = document.querySelector(".cyber-item") as HTMLElement;
    expect(row.textContent).toContain("Qi Focus F6");
    expect(row.textContent).toContain("18,000¥");
    expect(row.textContent).toContain("結合 6カルマ");

    fireEvent.change(screen.getByLabelText("Force"), { target: { value: "8" } });
    expect(patch).toHaveBeenLastCalledWith({
      qi_foci: [{ id: "q1", power_id: "imprv", rating: 8, power_rating: 1 }],
    });

    fireEvent.change(screen.getByLabelText("パワーR"), { target: { value: "2" } });
    expect(patch).toHaveBeenLastCalledWith({
      qi_foci: [{ id: "q1", power_id: "imprv", rating: 6, power_rating: 2 }],
    });

    fireEvent.change(screen.getByLabelText("能力値"), { target: { value: "AGI" } });
    expect(patch).toHaveBeenLastCalledWith({
      qi_foci: [{ id: "q1", power_id: "imprv", rating: 6, power_rating: 1, extra: "AGI" }],
    });

    fireEvent.click(screen.getByRole("button", { name: "削除" }));
    expect(patch).toHaveBeenLastCalledWith({ qi_foci: [] });
  });

  it("filters the qi-focus list by its own search box", () => {
    renderTab();
    fireEvent.change(screen.getByPlaceholderText("気焦点に入れるパワーを検索"), {
      target: { value: "combat" },
    });
    const qiList = [...document.querySelectorAll(".quality-list")].at(-1) as HTMLElement;
    const names = [...qiList.querySelectorAll(".quality-item b")].map((b) => b.textContent);
    expect(names).toEqual(["Combat Sense"]);
  });
});
