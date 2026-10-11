import { render, screen, within } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { QualitiesTab } from "@/components/character/tabs/QualitiesTab";
import { BooksProvider } from "@/lib/character/books";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";

const pickerCatalog = makeCatalog({
  qualities: [
    { id: "amb", name: "Ambidextrous", karma: 4, category: "Positive", source: "SR5" },
    { id: "dist", name: "Distinctive Style", karma: -5, category: "Negative", source: "SR5" },
  ] as never,
});

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
    books?: string[];
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(
    <BooksProvider books={over.books}>
      <QualitiesTab
        {...panelProps(ch, {
          catalog: over.catalog ?? makeCatalog(),
          patch: over.patch ?? (() => {}),
        })}
      />
    </BooksProvider>,
  );
}

describe("<QualitiesTab>", () => {
  it("labels innate qualities and provides no delete button even for a purchased overlap", () => {
    renderTab({
      character: {
        metatype: "Centaur",
        quality_ids: ["magic-sense"],
        derived: {
          qualities: [
            {
              id: "magic-sense",
              name: "Magic Sense",
              category: "Positive",
              source: "RF",
              karma: 0,
              free: true,
              origin: "Metatype",
              origin_id: "centaur",
              origin_name: "Centaur",
              removable: false,
            },
          ],
        },
      },
    });
    const row = document.querySelector<HTMLElement>(".card > .quality-item")!;
    expect(within(row).getByText(/Centaurの生得能力（追加カルマなし）/)).toBeDefined();
    expect(within(row).getByText("生得付与・削除不可")).toBeDefined();
    expect(within(row).queryByRole("button", { name: "削除" })).toBeNull();
  });

  it("puts each skill choice in its owned quality row and preserves other choices on save", () => {
    const patch = vi.fn();
    const qualities = [
      { id: "confidence", name: "自信喪失", karma: -10, category: "Negative", source: "SR5" },
      { id: "aptitude", name: "天賦の才", karma: 14, category: "Positive", source: "SR5" },
    ];
    const slot = {
      key: "quality:confidence:0",
      source: "自信喪失",
      source_kind: "quality",
      source_id: "confidence",
      picked: "",
      bonus: -2,
      max: 0,
      rating: 0,
      minimum_rating: 4,
      options: ["Gymnastics"],
      knowledgeskills: false,
    };
    renderTab({
      patch,
      catalog: makeCatalog({ qualities: qualities as never }),
      character: {
        quality_ids: ["confidence", "aptitude"],
        skill_picks: { "ware:recorder:0": "Pistols" },
        derived: {
          qualities: qualities as never,
          skill_pick_slots: [
            slot,
            {
              ...slot,
              key: "quality:aptitude:0",
              source: "天賦の才",
              source_id: "aptitude",
              bonus: 0,
              max: 1,
              minimum_rating: 0,
            },
            {
              ...slot,
              key: "ware:recorder:0",
              source: "Reflex Recorder",
              source_kind: "bioware",
              source_id: "recorder",
            },
          ],
        },
      },
    });
    const rows = [...document.querySelectorAll<HTMLElement>(".card > .quality-item")];
    expect(rows).toHaveLength(2);
    const confidence = within(rows[0]).getByRole("combobox", { name: "自信喪失 の技能 -2" });
    expect(within(rows[0]).getByText("対象はレーティング4以上の技能です。")).toBeDefined();
    expect(within(rows[1]).getByRole("combobox", { name: /天賦の才 の技能/ })).toBeDefined();
    expect(screen.getAllByRole("combobox")).toHaveLength(2);
    fireEvent.change(confidence, { target: { value: "Gymnastics" } });
    expect(patch).toHaveBeenCalledWith({
      skill_picks: { "ware:recorder:0": "Pistols", "quality:confidence:0": "Gymnastics" },
    });
  });

  it("renders the search box + karma line for an empty character", () => {
    renderTab();
    expect(screen.getByPlaceholderText("資質を検索")).toBeDefined();
    expect(screen.getByText(/カルマ 25 \/ 25/)).toBeDefined();
    expect(screen.queryByRole("heading", { name: "取得済み" })).toBeNull();
  });

  it("explains what positive and negative qualities cost", () => {
    const { container } = renderTab();
    const button = container.querySelector("p.muted button") as HTMLElement;
    const tip = document.getElementById(button.getAttribute("aria-describedby")!);
    expect(tip?.textContent).toContain("有利な資質はカルマで買う");
    expect(tip?.textContent).toContain("カルマ 2 倍");
  });

  it("shows the owned list + a text extra-editor for a needs_extra quality", () => {
    renderTab({
      character: {
        derived: {
          qualities: [
            {
              id: "q1",
              name: "Distinctive Style",
              karma: -5,
              category: "Negative",
              source: "SR5",
              needs_extra: true,
              extra_kind: "text",
            },
          ] as never,
        },
      },
    });
    expect(screen.getByRole("heading", { name: "取得済み" })).toBeDefined();
    expect(screen.getByText("Distinctive Style")).toBeDefined();
    // Distinctive Style is in no listed family, so it gets the plain prompt
    expect(screen.getByPlaceholderText("内容を入力")).toBeDefined();
  });

  it("lists SR5 catalog qualities and filters by the category tabs", () => {
    renderTab({ catalog: pickerCatalog });
    const list = document.querySelector(".quality-list") as HTMLElement;
    const names = () => [...list.querySelectorAll("b")].map((b) => b.textContent);
    expect(names()).toEqual(["Ambidextrous", "Distinctive Style"]);

    fireEvent.click(screen.getByRole("button", { name: "不利" }));
    expect(names()).toEqual(["Distinctive Style"]);
  });

  // This tab writes its own list instead of using <CatalogPicker>, so it used
  // to be the one place the settings' book list did not reach: a search found
  // qualities out of books the GM had switched off, and bought them.
  it("keeps qualities out of disabled books off the list, search included", () => {
    const catalog = makeCatalog({
      qualities: [
        { id: "amb", name: "Ambidextrous", karma: 4, category: "Positive", source: "SR5" },
        {
          id: "pt",
          name: "Prototype Transhuman",
          karma: 1,
          category: "Positive",
          source: "CF",
        },
      ] as never,
    });
    renderTab({ catalog, books: ["SR5"] });
    fireEvent.change(screen.getByPlaceholderText("資質を検索"), { target: { value: "proto" } });

    expect(screen.queryByText("Prototype Transhuman")).toBeNull();

    // …and is still reachable when the book is on
    renderTab({ catalog, books: ["SR5", "CF"] });
    fireEvent.change(screen.getAllByPlaceholderText("資質を検索")[1], {
      target: { value: "proto" },
    });
    expect(screen.getByText("Prototype Transhuman")).toBeDefined();
  });

  it("filters by the search box", () => {
    renderTab({ catalog: pickerCatalog });
    fireEvent.change(screen.getByPlaceholderText("資質を検索"), { target: { value: "ambi" } });
    const list = document.querySelector(".quality-list") as HTMLElement;
    expect([...list.querySelectorAll("b")].map((b) => b.textContent)).toEqual(["Ambidextrous"]);
  });

  it("'追加' patches quality_ids with the picked id", () => {
    const patch = vi.fn();
    renderTab({ catalog: pickerCatalog, patch });
    const row = [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
      el.textContent?.includes("Ambidextrous"),
    )!;
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith(expect.objectContaining({ quality_ids: ["amb"] }));
  });
});

describe("<QualitiesTab> a limit shared between siblings", () => {
  // Indomitable (SR5 p.75): three kinds, 3 takes across all of them
  const kinds = ["Physical", "Mental", "Social"].map((k) => `Indomitable (${k})`);
  const catalog = makeCatalog({
    qualities: kinds.map((name, i) => ({
      id: `ind${i}`,
      name,
      karma: 8,
      category: "Positive",
      source: "SR5",
      max_takes: 3,
      include_in_limit: kinds.filter((other) => other !== name),
    })) as never,
  });
  const row = (name: string) =>
    [...document.querySelectorAll(".quality-list .quality-item")].find(
      (el) => el.querySelector("b")?.textContent === name,
    )!;

  it("says the limit is shared", () => {
    renderTab({ catalog });
    expect(row("Indomitable (Social)").textContent).toContain(
      "Indomitable (Physical)、Indomitable (Mental) と合わせて最大3",
    );
  });

  it("stops the add once the siblings hold the whole limit", () => {
    const patch = vi.fn();
    renderTab({ catalog, patch, character: { quality_ids: ["ind0", "ind0", "ind1"] } });
    const social = row("Indomitable (Social)").querySelector("button")!;
    expect(social.disabled).toBe(true);
    fireEvent.click(social);
    expect(patch).not.toHaveBeenCalled();
  });

  it("still adds while the shared count is under it", () => {
    const patch = vi.fn();
    renderTab({ catalog, patch, character: { quality_ids: ["ind0"] } });
    fireEvent.click(row("Indomitable (Social)").querySelector("button")!);
    expect(patch).toHaveBeenCalledWith(expect.objectContaining({ quality_ids: ["ind0", "ind2"] }));
  });
});

describe("<QualitiesTab> a cost moved by a condition", () => {
  it("shows the table karma beside the one charged", () => {
    renderTab({
      character: {
        quality_ids: ["blind"],
        derived: {
          qualities: [
            {
              id: "blind",
              name: "Blind",
              karma: -5,
              karma_base: -15,
              category: "Negative",
              source: "RF",
            },
          ] as never,
        },
      },
    });
    const owned = [...document.querySelectorAll(".quality-item")].find((el) =>
      el.textContent?.includes("Blind"),
    )!;
    expect(owned.textContent).toContain("カルマ -5（条件で変動・表では -15）");
  });
});

describe("<QualitiesTab> career prices (SR5 p.107)", () => {
  const catalog = makeCatalog({
    qualities: [
      { id: "amb", name: "Ambidextrous", karma: 4, category: "Positive", source: "SR5" },
      { id: "dist", name: "Distinctive Style", karma: -5, category: "Negative", source: "SR5" },
      {
        id: "way",
        name: "The Artist's Way",
        karma: 20,
        category: "Positive",
        source: "SR5",
        double_career: false,
      },
    ] as never,
  });
  const itemText = (scope: string, name: string) =>
    [...document.querySelectorAll(`${scope} .quality-item`)].find(
      (el) => el.querySelector("b")?.textContent === name,
    )!.textContent;

  it("prices the catalog at the career rate", () => {
    renderTab({ catalog, character: { derived: { quality_career_pricing: true } as never } });
    expect(itemText(".quality-list", "Ambidextrous")).toContain("キャリアでは 8カルマ");
    expect(itemText(".quality-list", "The Artist's Way")).toContain("キャリアでは 20カルマ");
    expect(itemText(".quality-list", "Distinctive Style")).toContain("キャリアではカルマなし");
  });

  it("says what a taken one cost and what a held negative would take to buy off", () => {
    renderTab({
      catalog,
      character: {
        quality_ids: ["amb", "dist"],
        derived: {
          quality_career_pricing: true,
          qualities: [
            {
              id: "amb",
              name: "Ambidextrous",
              karma: 4,
              category: "Positive",
              source: "SR5",
              career_cost: 8,
            },
            {
              id: "dist",
              name: "Distinctive Style",
              karma: -5,
              category: "Negative",
              source: "SR5",
            },
          ],
        } as never,
      },
    });
    expect(itemText(".card", "Ambidextrous")).toContain("キャリアで取得（8カルマ）");
    expect(itemText(".card", "Distinctive Style")).toContain("外すと買い戻し 10カルマ");
  });

  it("lists the qualities dropped in career", () => {
    renderTab({
      catalog,
      character: {
        derived: {
          quality_career_pricing: true,
          qualities_removed: [
            { id: "dist", name: "Distinctive Style", category: "Negative", karma: 10 },
          ],
        } as never,
      },
    });
    expect(screen.getByText("キャリアで外した資質")).toBeTruthy();
    expect(document.body.textContent).toContain("買い戻し 10カルマ");
  });

  it("stays quiet outside career", () => {
    renderTab({ catalog });
    expect(document.body.textContent).not.toContain("キャリアでは");
  });
});

describe("<QualitiesTab> karma overspent", () => {
  const line = () => document.querySelector(".card > p.muted")!;

  it("turns the karma line red and says so", () => {
    renderTab({
      character: { derived: { karma: { pool: 25, spent: 29, remaining: -4 } } as never },
    });
    expect(line().className).toContain("errors");
    expect(line().textContent).toContain("カルマが不足しています（残り -4）");
  });

  it("leaves it plain while there is karma left", () => {
    renderTab();
    expect(line().className).not.toContain("errors");
    expect(line().textContent).not.toContain("不足");
  });
});

describe("<QualitiesTab> undoing career changes", () => {
  const removed = [{ id: "dist", name: "Distinctive Style", category: "Negative", karma: 10 }];

  it("restores a dropped quality with one click", () => {
    const patch = vi.fn();
    renderTab({
      patch,
      character: {
        quality_ids: ["amb"],
        derived: { quality_career_pricing: true, qualities_removed: removed } as never,
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "戻す" }));
    expect(patch).toHaveBeenCalledWith({ quality_ids: ["amb", "dist"] });
  });

  it("takes today's qualities as the chargen ones after asking", () => {
    const patch = vi.fn();
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    renderTab({
      patch,
      character: {
        quality_ids: ["amb"],
        career_baseline: { skills: { Pistols: 3 }, quality_ids: ["dist"] },
        derived: { quality_career_pricing: true, qualities_removed: removed } as never,
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "今の資質を作成時のものとして扱う" }));
    expect(confirm).toHaveBeenCalled();
    expect(patch).toHaveBeenCalledWith({
      career_baseline: { skills: { Pistols: 3 }, quality_ids: ["amb"] },
    });
    confirm.mockRestore();
  });

  it("does nothing when the question is declined", () => {
    const patch = vi.fn();
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    renderTab({
      patch,
      character: {
        career_baseline: { quality_ids: ["dist"] },
        derived: { quality_career_pricing: true, qualities_removed: removed } as never,
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "今の資質を作成時のものとして扱う" }));
    expect(patch).not.toHaveBeenCalled();
    confirm.mockRestore();
  });

  it("offers the reset only once something changed in career", () => {
    renderTab({ character: { derived: { quality_career_pricing: true } as never } });
    expect(screen.queryByRole("button", { name: "今の資質を作成時のものとして扱う" })).toBeNull();
  });
});

describe("<QualitiesTab> a quality switched off by ware", () => {
  it("names the ware that switched it off", () => {
    renderTab({
      character: {
        quality_ids: ["lr"],
        derived: {
          qualities: [
            {
              id: "lr",
              name: "Lightning Reflexes",
              karma: 20,
              category: "Positive",
              source: "RF",
              disabled_by: "Wired Reflexes",
            },
          ],
        } as never,
      },
    });
    expect(document.querySelector(".quality-item")!.textContent).toContain(
      "Wired Reflexes があるので無効",
    );
  });
});

describe("<QualitiesTab> an Infected quality's critter powers", () => {
  const banshee = (over: Record<string, unknown> = {}) => ({
    id: "inf",
    name: "Infected: Banshee",
    karma: 30,
    category: "Positive",
    source: "RF",
    critter_powers: [
      { name: "Dual Natured", type: "P", action: "Auto", range: "Self", duration: "Always" },
      { name: "Vulnerability (Wood)" },
    ],
    optional_powers: ["Immunity (Toxins)", "Enhanced Senses (Hearing)"],
    optional_power: "",
    ...over,
  });

  it("lists the powers the quality grants", () => {
    renderTab({ character: { derived: { qualities: [banshee()] as never } } });
    expect(screen.getByText(/Dual Natured/)).toBeDefined();
    expect(screen.getByText(/Vulnerability \(Wood\)/)).toBeDefined();
  });

  it("picks the optional power into its own extra, keeping the others", () => {
    const patch = vi.fn();
    renderTab({
      character: {
        quality_extras: { inf: "BOD" },
        derived: { qualities: [banshee()] as never },
      } as never,
      patch,
    });

    const picker = screen.getByRole("combobox", { name: "Infected: Banshee: 任意パワーを選択" });
    expect([...picker.querySelectorAll("option")].map((o) => o.textContent)).toEqual([
      "任意パワーを選択",
      "Immunity (Toxins)",
      "Enhanced Senses (Hearing)",
    ]);
    fireEvent.change(picker, { target: { value: "Immunity (Toxins)" } });

    expect(patch).toHaveBeenCalledWith({
      quality_extras: { inf: "BOD", "inf:optionalpower": "Immunity (Toxins)" },
    });
  });

  it("offers no picker for a quality without optional powers", () => {
    renderTab({
      character: { derived: { qualities: [banshee({ optional_powers: undefined })] as never } },
    });
    expect(screen.queryByRole("combobox", { name: /任意パワー/ })).toBeNull();
  });
});

describe("<QualitiesTab> leveled qualities", () => {
  const spec = {
    id: "magic",
    name: "Magic Resistance",
    karma: 6,
    category: "Positive",
    source: "SR5",
    max_takes: 4,
    has_levels: true,
  };
  const catalog = makeCatalog({
    qualities: [
      spec,
      { ...spec, id: "restricted", name: "Restricted Gear", max_takes: 3, has_levels: false },
    ] as never,
  });
  const owned = { ...spec, extra: "" };

  it("buys the selected level once and displays its total price", () => {
    const patch = vi.fn();
    renderTab({ catalog, patch });
    fireEvent.change(screen.getByRole("combobox", { name: "Magic Resistanceの取得Lv" }), {
      target: { value: "3" },
    });
    const row = document.querySelector(".quality-list .quality-item")!;
    expect(row.textContent).toContain("カルマ 18");
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith(
      expect.objectContaining({ quality_ids: ["magic", "magic", "magic"] }),
    );
    expect(screen.queryByRole("combobox", { name: "Restricted Gearの取得Lv" })).toBeNull();
  });

  it("shows a single owned row, changes levels, and deletes all levels with their picks", () => {
    const patch = vi.fn();
    renderTab({
      catalog,
      patch,
      character: {
        quality_ids: ["magic", "magic", "magic", "other"],
        quality_extras: {
          magic: "pick",
          "magic:contact": "c",
          "magic:optionalpower": "p",
          other: "keep",
        },
        skill_picks: { "quality:magic:0": "Pistols", "quality:other:0": "Blades" },
        derived: { qualities: [owned, owned, owned] as never },
      },
    });
    expect(screen.getByText("Magic Resistance Lv3")).toBeDefined();
    const row = document.querySelector(".card > .quality-item")!;
    expect(row.textContent).toContain("カルマ 18");
    fireEvent.change(screen.getByRole("combobox", { name: "Magic Resistanceの所持Lv" }), {
      target: { value: "2" },
    });
    expect(patch).toHaveBeenCalledWith({ quality_ids: ["magic", "magic", "other"] });
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith({
      quality_ids: ["other"],
      quality_extras: { other: "keep" },
      skill_picks: { "quality:other:0": "Blades" },
    });
  });

  it("changes a full quality without using the catalog button to delete it", () => {
    const patch = vi.fn();
    renderTab({
      catalog,
      patch,
      character: {
        quality_ids: Array(4).fill("magic"),
        derived: { qualities: Array(4).fill(owned) as never },
      },
    });
    const row = document.querySelector(".quality-list .quality-item")!;
    expect(row.querySelector("button")!.textContent).toBe("Lv変更");
    expect(row.querySelector("button")!.disabled).toBe(true);
    fireEvent.change(screen.getByRole("combobox", { name: "Magic Resistanceの取得Lv" }), {
      target: { value: "2" },
    });
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith(
      expect.objectContaining({ quality_ids: ["magic", "magic"] }),
    );
  });

  it("limits both pickers by other kinds of Indomitable", () => {
    const physical = {
      ...spec,
      id: "physical",
      name: "Indomitable (Physical)",
      max_takes: 3,
      include_in_limit: ["Indomitable (Mental)"],
    };
    const mental = {
      ...spec,
      id: "mental",
      name: "Indomitable (Mental)",
      max_takes: 3,
      include_in_limit: ["Indomitable (Physical)"],
    };
    renderTab({
      catalog: makeCatalog({ qualities: [physical, mental] as never }),
      character: {
        quality_ids: ["physical", "mental", "mental"],
        derived: { qualities: [physical, mental, mental] as never },
      },
    });
    for (const name of ["Indomitable (Physical)の取得Lv", "Indomitable (Physical)の所持Lv"]) {
      expect(screen.getByRole("combobox", { name }).querySelectorAll("option")).toHaveLength(1);
    }
  });

  it("sums only the newly purchased career levels", () => {
    renderTab({
      catalog,
      character: {
        quality_ids: ["magic", "magic", "magic"],
        derived: {
          quality_career_pricing: true,
          qualities: [owned, { ...owned, career_cost: 12 }, { ...owned, career_cost: 12 }] as never,
        },
      },
    });
    const row = document.querySelector(".card > .quality-item")!;
    expect(row.textContent).toContain("キャリアで取得（24カルマ）");
    fireEvent.change(screen.getByRole("combobox", { name: "Magic Resistanceの取得Lv" }), {
      target: { value: "4" },
    });
    expect(document.querySelector(".quality-list .quality-item")!.textContent).toContain(
      "キャリアでは 12カルマ",
    );
  });
});
