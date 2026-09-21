import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { beforeEach } from "vitest";
import { CyberTab } from "@/components/character/tabs/CyberTab";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";
import type { Character, Derived } from "@/lib/types";

const wired = {
  id: "wired1",
  name: "Wired Reflexes",
  category: "Cyberware",
  ess: "2",
  cost: "39000",
  minrating: 1,
  maxrating: 3,
  plugin: false,
  has_wireless: true,
  source: "SR5",
  page: "",
};
const datajack = {
  id: "datajack",
  name: "Datajack",
  category: "Cyberware",
  ess: "0.1",
  cost: "1000",
  minrating: 1,
  maxrating: 1,
  plugin: true,
  has_wireless: true,
  source: "SR5",
  page: "",
};

function cyberCatalog(items: object[] = [wired, datajack]) {
  return makeCatalog({
    cyberware: {
      items,
      grades: [
        { name: "Standard", ess: 1, ess_adapsin: 0.9, cost: 1 },
        { name: "Alphaware", ess: 0.8, ess_adapsin: 0.7, cost: 1.2 },
      ],
    },
  } as never);
}

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(
    <CyberTab
      {...panelProps(ch, {
        catalog: over.catalog ?? cyberCatalog(),
        patch: over.patch ?? (() => {}),
      })}
    />,
  );
}

describe("<CyberTab>", () => {
  it("renders the essence line, search box and Redliner toggles", () => {
    renderTab();
    expect(screen.getByText(/装着中 0 ・ Essence 6/)).toBeDefined();
    expect(screen.getByPlaceholderText("サイバーウェアを検索")).toBeDefined();
    expect(screen.getByText("胴")).toBeDefined();
    expect(screen.getByText("頭蓋")).toBeDefined();
  });

  it("lists the catalog and adds a piece at the selected grade", () => {
    const patch = vi.fn();
    renderTab({ patch });
    const row = [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
      el.textContent?.includes("Wired Reflexes"),
    )!;
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith({
      cyberware: [
        expect.objectContaining({
          ware_id: "wired1",
          rating: 1,
          grade: "Standard",
          wireless: true,
        }),
      ],
    });
  });

  // The grade dropdown only exists on an owned row, so these two need one.
  function renderOwning(adapsin: boolean) {
    const ch = makeCharacter({
      cyberware: [{ id: "row1", ware_id: "wired1", rating: 1, grade: "Standard", wireless: false }],
    });
    const installed = {
      id: "row1",
      ware_id: "wired1",
      name: "Wired Reflexes",
      category: "Cyberware",
      grade: "Standard",
      rating: 1,
      essence: 2,
      nuyen: 39000,
      source: "SR5",
    };
    const d = { ...ch.derived, adapsin, cyberware: [installed] } as never;
    return render(<CyberTab {...panelProps({ ...ch, derived: d }, { catalog: cyberCatalog() })} />);
  }

  function gradeOptions() {
    const select = [...document.querySelectorAll(".cyber-item select")].find((el) =>
      el.textContent?.includes("ESS×"),
    )!;
    return [...select.querySelectorAll("option")].map((o) => o.textContent);
  }

  it("quotes the Adapsin essence multiplier once Adapsin is installed", () => {
    // Adapsin does not add a grade, it changes what each grade costs. The
    // dropdown has to say the number the engine will actually use, or it
    // contradicts the ESS printed on the row right next to it.
    renderOwning(true);
    expect(gradeOptions()).toEqual(["Standard (ESS×0.9 / ¥×1)", "Alphaware (ESS×0.7 / ¥×1.2)"]);
  });

  it("quotes the plain multiplier without Adapsin", () => {
    renderOwning(false);
    expect(gradeOptions()).toEqual(["Standard (ESS×1 / ¥×1)", "Alphaware (ESS×0.8 / ¥×1.2)"]);
  });

  it("filters the catalog by the search box", () => {
    renderTab();
    fireEvent.change(screen.getByPlaceholderText("サイバーウェアを検索"), {
      target: { value: "datajack" },
    });
    const names = [...document.querySelectorAll(".quality-list .quality-item b")].map(
      (b) => b.textContent,
    );
    expect(names).toEqual(["Datajack"]);
  });

  it("a keyed implant offers only its category and patches the target", () => {
    const patch = vi.fn();
    const hive = { ...wired, id: "hive", name: "Nanohive, Soft", category: "Nanocybernetics" };
    const soft = { ...datajack, id: "soft", name: "Nanotattoos", category: "Soft Nanoware" };
    const ch = makeCharacter({
      cyberware: [{ id: "row1", ware_id: "hive", rating: 1, grade: "Standard", wireless: false }],
    });
    const d = {
      ...ch.derived,
      cyberware: [
        {
          id: "row1",
          ware_id: "hive",
          name: "Nanohive, Soft",
          category: "Nanocybernetics",
          grade: "Standard",
          rating: 1,
          essence: 0.2,
          nuyen: 10000,
          select_ware: true,
          select_ware_category: "Soft Nanoware",
          extra: "",
        },
      ],
    } as never;
    render(
      <CyberTab
        {...panelProps(
          { ...ch, derived: d },
          { catalog: cyberCatalog([hive, soft, datajack]), patch },
        )}
      />,
    );
    const select = screen.getByLabelText("対象") as HTMLSelectElement;
    expect([...select.options].map((o) => o.textContent)).toEqual([
      "選択してください",
      "Nanotattoos",
    ]);
    fireEvent.change(select, { target: { value: "Nanotattoos" } });
    expect(patch).toHaveBeenCalledWith({
      cyberware: [expect.objectContaining({ id: "row1", extra: "Nanotattoos" })],
    });
  });

  it("a quality's implant is labelled and has neither grade box nor delete", () => {
    const ch = makeCharacter();
    const d = {
      ...ch.derived,
      cyberware: [
        {
          id: "granted:0",
          ware_id: "busted",
          name: "Busted Ware",
          category: "Bodyware",
          grade: "None",
          rating: 1,
          essence: 0.5,
          nuyen: 0,
          granted_by: "Busted Cyberware",
        },
      ],
    } as unknown as Derived;
    render(<CyberTab {...panelProps({ ...ch, derived: d }, { catalog: cyberCatalog() })} />);
    expect(screen.getByText(/Busted Cyberware/)).toBeTruthy();
    expect(screen.queryByLabelText("グレード")).toBeNull();
    expect(screen.queryByRole("button", { name: "削除" })).toBeNull();

    // …where a bought row of the same shape has both.
    const bought = {
      ...d,
      cyberware: [{ ...d.cyberware[0], id: "row1", granted_by: "" }],
    };
    render(<CyberTab {...panelProps({ ...ch, derived: bought }, { catalog: cyberCatalog() })} />);
    expect(screen.getByLabelText("グレード")).toBeTruthy();
    expect(screen.getByRole("button", { name: "削除" })).toBeTruthy();
  });

  it("toggles a Redliner option through patch", () => {
    const patch = vi.fn();
    renderTab({ patch });
    fireEvent.click(screen.getByLabelText("胴"));
    expect(patch).toHaveBeenCalledWith({
      options: { redliner_torso: true, redliner_skull: false },
    });
  });
});

describe("<CyberTab> compact view", () => {
  beforeEach(() => localStorage.clear());

  function renderInstalled(patch = vi.fn(), extra: Record<string, unknown> = {}) {
    const ch = makeCharacter({
      cyberware: [
        { id: "row1", ware_id: "wired1", rating: 2, grade: "Standard", wireless: false },
        { id: "row2", ware_id: "datajack", rating: 1, grade: "Standard", parent_id: "row1" },
      ],
    } as never);
    const base = { category: "Cyberware", grade: "Standard", nuyen: 1000, source: "SR5" };
    const d = {
      ...ch.derived,
      cyberware: [
        { ...base, id: "row1", ware_id: "wired1", name: "Wired Reflexes", rating: 2, essence: 2 },
        {
          ...base,
          id: "row2",
          ware_id: "datajack",
          name: "Datajack",
          rating: 1,
          essence: 0.1,
          parent_id: "row1",
        },
      ],
      ...extra,
    } as never;
    return render(
      <CyberTab {...panelProps({ ...ch, derived: d }, { catalog: cyberCatalog(), patch })} />,
    );
  }

  it("folds each installed row down to its name, and remembers it", () => {
    const patch = vi.fn();
    const first = renderInstalled(patch);
    expect(document.querySelectorAll(".cyber-item .cyber-controls").length).toBeGreaterThan(0);

    fireEvent.click(screen.getByLabelText("簡易表示（名称のみ）"));
    expect(document.querySelectorAll(".cyber-item .cyber-controls")).toHaveLength(0);
    expect(document.querySelector(".cyber-item .slot-picker")).toBeNull();
    expect(document.querySelector(".cyber-item")!.textContent).not.toContain("ESS −2");
    expect(screen.getByText("Wired Reflexes R2")).toBeDefined();
    // the plug-in stays, as a name under its parent
    expect(document.querySelector(".cyber-item.compact.nested")!.textContent).toContain("Datajack");
    expect(localStorage.getItem("wareCompact")).toBe("1");

    // the delete button is still there
    fireEvent.click(document.querySelector(".cyber-item.compact.nested .btn.danger")!);
    expect(patch).toHaveBeenCalledWith(
      expect.objectContaining({ cyberware: [expect.objectContaining({ id: "row1" })] }),
    );

    first.unmount();
    renderInstalled();
    expect((screen.getByLabelText("簡易表示（名称のみ）") as HTMLInputElement).checked).toBe(true);
    expect(document.querySelectorAll(".cyber-item .cyber-controls")).toHaveLength(0);
  });

  it("says 同梱 once on a folded bundled row", () => {
    localStorage.setItem("wareCompact", "1");
    const ch = makeCharacter({} as never);
    const base = { category: "Cyberware", grade: "Standard", nuyen: 0, source: "SR5", rating: 1 };
    const d = {
      ...ch.derived,
      cyberware: [
        { ...base, id: "eyes", ware_id: "wired1", name: "Cybereyes", essence: 0.2 },
        {
          ...base,
          id: "link",
          ware_id: "datajack",
          name: "Image Link",
          essence: 0,
          parent_id: "eyes",
          included: true,
        },
      ],
    } as never;
    render(<CyberTab {...panelProps({ ...ch, derived: d }, { catalog: cyberCatalog() })} />);
    const nested = document.querySelector(".cyber-item.compact.nested")!;
    expect(nested.textContent).toBe("Image Link（同梱）");
  });

  it("flags a folded row whose skill pick is still empty", () => {
    localStorage.setItem("wareCompact", "1");
    const slot = {
      key: "k1",
      source: "Wired Reflexes",
      source_kind: "cyberware",
      source_id: "row1",
      picked: "",
      bonus: 1,
      max: 0,
      rating: 0,
      options: ["Pistols"],
      knowledgeskills: false,
    };
    const first = renderInstalled(vi.fn(), { skill_pick_slots: [slot] });
    const parent = document.querySelector(".cyber-item.compact:not(.nested)")!;
    expect(parent.querySelector(".warn")!.textContent).toContain("未選択あり");
    // only the row that owns the slot
    expect(document.querySelector(".cyber-item.compact.nested .warn")).toBeNull();

    first.unmount();
    renderInstalled(vi.fn(), { skill_pick_slots: [{ ...slot, picked: "Pistols" }] });
    expect(document.querySelector(".cyber-item .warn")).toBeNull();
  });
});

describe("<CyberTab> black market discount", () => {
  // another test in this file leaves the compact view on (localStorage)
  beforeEach(() => localStorage.setItem("wareCompact", "0"));

  const installed = {
    id: "w1",
    ware_id: "wired1",
    name: "Wired Reflexes",
    category: "Cyberware",
    rating: 1,
    rating_max: 3,
    grade: "Standard",
    ess: 2,
    nuyen: 39000,
    wireless: true,
  };
  const character = (extra: Record<string, unknown>) => ({
    cyberware: [{ id: "w1", ware_id: "wired1", rating: 1, grade: "Standard", wireless: true }],
    derived: { cyberware: [installed], ...extra },
  });

  /** The box belongs to whichever kind the quality's category names, and
   *  ticking it marks that one piece. */
  it("shows nothing when the pipeline covers another category", () => {
    renderTab({
      character: character({
        black_market_discount: true,
        black_market_category: "Bioware",
      }) as never,
    });
    expect(screen.queryByLabelText("闇市")).toBeNull();
  });

  it("marks the piece it is ticked on", () => {
    const patch = vi.fn();
    renderTab({
      character: character({
        black_market_discount: true,
        black_market_category: "Cyberware",
      }) as never,
      patch,
    });
    fireEvent.click(screen.getByLabelText("闇市"));
    expect((patch.mock.calls[0][0] as Character).cyberware![0].discounted).toBe(true);
  });
});

describe("<CyberTab> held gear", () => {
  // A piece that holds gear: the held row, the select for more, and a removal
  // that takes only what it held with it.
  function renderHolder(patch: (b: Record<string, unknown>) => void) {
    const injector = { ...datajack, id: "inj", name: "Auto Injector", allow_gear: ["Drugs"] };
    const catalog = makeCatalog({
      ...cyberCatalog([wired, injector]),
      gear: [
        { id: "jazz", name: "Jazz", category: "Drugs", cost: "75", source: "SR5" },
        { id: "rope", name: "Rope", category: "Survival Gear", cost: "50", source: "SR5" },
      ],
    } as never);
    const ch = makeCharacter({
      cyberware: [{ id: "c1", ware_id: "inj", rating: 1, grade: "Standard", wireless: true }],
      weapons: [{ id: "w1", weapon_id: "gun" }] as never,
      weapon_accessories: [{ id: "a1", accessory_id: "scope", parent_id: "w1" }] as never,
      gear: [
        { id: "g1", gear_id: "jazz", parent_id: "c1", qty: 1 },
        { id: "g2", gear_id: "rope", parent_id: "armor1", qty: 1 },
      ] as never,
    });
    const held = {
      id: "g1",
      gear_id: "jazz",
      name: "Jazz",
      parent_id: "c1",
      nuyen: 75,
      rating: 1,
      rating_max: 1,
    };
    const installed = {
      id: "c1",
      ware_id: "inj",
      name: "Auto Injector",
      category: "Cyberware",
      grade: "Standard",
      rating: 1,
      essence: 0.1,
      nuyen: 1000,
      source: "SR5",
      allow_gear: ["Drugs"],
      gear: [held],
    };
    const d = { ...ch.derived, cyberware: [installed] } as never;
    return render(<CyberTab {...panelProps({ ...ch, derived: d }, { catalog, patch })} />);
  }

  it("lists what a piece holds and offers only what it may hold", () => {
    const patch = vi.fn();
    renderHolder(patch);
    expect(screen.getByText(/Jazz/, { selector: ".cyber-item .muted" })).toBeDefined();
    const select = screen.getByRole("combobox", { name: /Auto Injector/ });
    const labels = [...select.querySelectorAll("option")].map((o) => o.textContent);
    expect(labels.some((t) => t?.includes("Jazz"))).toBe(true);
    expect(labels.some((t) => t?.includes("Rope"))).toBe(false);
    fireEvent.change(select, { target: { value: "jazz" } });
    fireEvent.click(screen.getByRole("button", { name: "Auto Injector: 入れる" }));
    expect(patch).toHaveBeenCalledWith({
      gear: expect.arrayContaining([expect.objectContaining({ gear_id: "jazz", parent_id: "c1" })]),
    });
  });

  it("removing a piece takes what it held, and nothing held elsewhere", () => {
    const patch = vi.fn();
    renderHolder(patch);
    fireEvent.click(screen.getByRole("button", { name: "削除" }));
    const body = patch.mock.calls[0][0];
    expect(body.gear.map((row: { id: string }) => row.id)).toEqual(["g2"]);
    expect(body.weapon_accessories.map((row: { id: string }) => row.id)).toEqual(["a1"]);
  });
});
