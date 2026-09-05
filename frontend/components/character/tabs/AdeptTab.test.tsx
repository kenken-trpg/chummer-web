import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { AdeptTab } from "@/components/character/tabs/AdeptTab";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

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
      catalog={over.catalog ?? makeCatalog({ powers: [power, power2] as any })}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      trGroup={identityTr}
      t={(k) => k}
      ui={testUi}
      patch={over.patch ?? (() => {})}
      setCharacter={() => {}}
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
        powers: [power] as any,
        enhancements: [{ id: "e1", name: "Critical Strike", source: "SR5" }] as any,
      }),
      patch,
    });
    const enhList = [...document.querySelectorAll(".quality-list")].find((l) =>
      l.textContent?.includes("Critical Strike"),
    ) as HTMLElement;
    fireEvent.click(rowButton(enhList, "Critical Strike"));
    expect(patch).toHaveBeenCalledWith({ adept_enhancements: ["e1"] });
  });
});
