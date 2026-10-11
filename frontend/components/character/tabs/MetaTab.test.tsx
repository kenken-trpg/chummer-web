import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { BooksProvider } from "@/lib/character/books";
import { MetaTab } from "@/components/character/tabs/MetaTab";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";
import type { PriorityTable } from "@/lib/types";

const priorityTable = {
  Heritage: {
    E: {
      metatypes: [
        { name: "Human", special: 0, variants: [] },
        { name: "Elf", special: 0, variants: [] },
      ],
    },
  },
  Talent: { E: { talents: [{ name: "Mundane", label: "Mundane", value: 0 }] } },
} as unknown as PriorityTable;

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    catalog?: ReturnType<typeof makeCatalog>;
    books?: string[];
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(
    <BooksProvider books={over.books}>
      <MetaTab
        {...panelProps(ch, {
          catalog: over.catalog ?? makeCatalog({ priority_table: priorityTable }),
          patch: over.patch ?? (() => {}),
        })}
      />
    </BooksProvider>,
  );
}

describe("<MetaTab>", () => {
  it.each(["Priority", "SumToTen", "Karma"])(
    "offers Centaur in %s with RF, charges the displayed cost and retains it when RF is disabled",
    (build_method) => {
      const patch = vi.fn();
      const catalog = makeCatalog({
        priority_table: {
          ...priorityTable,
          Heritage: {
            E: { metatypes: [{ name: "Centaur", special: 3, karma: 25, variants: [] }] },
          },
        } as unknown as PriorityTable,
        metatypes: [{ name: "Centaur", source: "RF", karma: 60, metavariants: [] }] as never,
      });
      const view = renderTab({ catalog, character: { build_method }, books: ["SR5", "RF"], patch });
      const button = screen.getByRole("button", { name: /Centaur/ });
      expect(button.textContent).toContain(build_method === "Karma" ? "60カルマ" : "25カルマ");
      if (build_method !== "Karma") expect(button.textContent).toContain("特殊点 3");
      fireEvent.click(button);
      expect(patch).toHaveBeenCalledWith({ metatype: "Centaur", metavariant: null });
      view.unmount();
      patch.mockClear();
      renderTab({
        catalog,
        character: { build_method, metatype: "Centaur" },
        books: ["SR5"],
        patch,
      });
      expect(screen.queryByRole("button", { name: /Centaur/ })).toBeNull();
      expect(screen.getByRole("status").textContent).toContain("別の種族を選ぶまで保持");
      expect(patch).not.toHaveBeenCalled();
    },
  );

  it.each(["Priority", "SumToTen", "Karma"])(
    "identifies an imported metatype outside the %s candidates without making it selectable",
    (build_method) => {
      const patch = vi.fn();
      renderTab({
        patch,
        character: {
          metatype: "Centaur",
          build_method,
          derived: {
            metatype_info: { name: "Centaur", source: "RF", parent: null, attributes: {} },
          },
        },
      });
      expect(screen.getByRole("status").textContent).toContain("現在の種族「Centaur」");
      expect(screen.getByRole("status").textContent).toContain("別の種族を選ぶまで保持");
      expect(screen.getByRole("status").textContent).toContain("RF");
      expect(screen.queryByRole("button", { name: /Centaur/ })).toBeNull();
      expect(patch).not.toHaveBeenCalled();
    },
  );

  it("does not show the retained-metatype note for a normal candidate", () => {
    renderTab({ character: { metatype: "Human" } });
    expect(screen.queryByRole("status")).toBeNull();
  });

  it("lets the player explicitly replace a retained metatype with an available choice", () => {
    const patch = vi.fn();
    renderTab({ character: { metatype: "Centaur" }, patch });
    fireEvent.click(screen.getByRole("button", { name: /Human/ }));
    expect(patch).toHaveBeenCalledWith({ metatype: "Human", metavariant: null });
  });

  it("shows fixed metatype powers with action, source and the original selection", () => {
    renderTab({
      character: {
        metatype: "Centaur",
        derived: {
          metatype_info: {
            name: "Centaur",
            parent: null,
            source: "RF",
            attributes: {},
            powers: [
              {
                id: "9fc065db-9d63-4e8b-aba9-e19dfba07652",
                name: "Natural Weapon",
                type: "P",
                action: "Complex",
                range: "Touch",
                duration: "Instant",
                source: "SR5",
                page: "399",
                select: "Kick: DV ({STR} + 2)P, AP +1, +1 Reach",
                rating: "",
                origin: "Metatype",
                origin_id: "centaur",
                origin_name: "Centaur",
              },
            ],
          },
        },
      },
    });
    expect(screen.getByRole("heading", { name: "種族パワー" })).toBeDefined();
    expect(screen.getByText("Kick: DV ({STR} + 2)P, AP +1, +1 Reach")).toBeDefined();
    expect(screen.getByText(/SR5 p.399/)).toBeDefined();
    expect(screen.getByText(/複雑/)).toBeDefined();
    expect(screen.getByText("Centaurの生得能力（追加カルマなし）")).toBeDefined();
  });

  it("lists the Heritage-priority metatypes and patches the pick", () => {
    const patch = vi.fn();
    renderTab({ patch });
    expect(screen.getByRole("button", { name: /Human/ })).toBeDefined();
    fireEvent.click(screen.getByRole("button", { name: /Elf/ }));
    expect(patch).toHaveBeenCalledWith({ metatype: "Elf", metavariant: null });
  });

  it("marks the current metatype selected and offers the Talent select", () => {
    renderTab({ character: { metatype: "Human" } });
    expect(screen.getByRole("button", { name: /Human/ }).className).toContain("selected");
    expect(screen.getByRole("combobox")).toBeDefined();
  });

  it("shows the metavariant select when the chosen metatype has variants", () => {
    const patch = vi.fn();
    const catalog = makeCatalog({
      priority_table: priorityTable,
      metatypes: [{ name: "Elf", metavariants: [{ name: "Night One" }] }] as never,
    });
    renderTab({ catalog, character: { metatype: "Elf" }, patch });
    const selects = screen.getAllByRole("combobox");
    const metavariant = selects[0];
    fireEvent.change(metavariant, { target: { value: "Night One" } });
    expect(patch).toHaveBeenCalledWith({ metavariant: "Night One" });
  });

  it("reads the talent options in Japanese", () => {
    const catalog = makeCatalog({
      priority_table: {
        ...priorityTable,
        Talent: {
          B: {
            talents: [
              { name: "Adept", label: "Adept - 6 Magic", value: 6 },
              { name: "Magician", label: "Magician - 4 Magic/7 Spells", value: 4 },
              {
                name: "Technomancer",
                label: "Technomancer - 4 Resonance/4 Complex Forms",
                value: 4,
              },
              { name: "Apprentice", label: "Apprentice - 5 Magic", value: 5 },
            ],
          },
        },
      } as never,
    });
    renderTab({ catalog, character: { priorities: { Heritage: "E", Talent: "B" } } as never });
    expect(
      [...screen.getByRole("combobox").querySelectorAll("option")].map((o) => o.textContent),
    ).toEqual([
      "アデプト - 魔力6",
      "魔法使い - 魔力4/術式7",
      "テクノマンサー - 共振力4/複合体4",
      // Run Faster's, so English — as its metavariants are
      "Apprentice - 魔力5",
    ]);
  });

  it("in Karma build it lists catalog metatypes with a karma cost", () => {
    const patch = vi.fn();
    const catalog = makeCatalog({
      metatypes: [
        { name: "Human", karma: 0, metavariants: [] },
        { name: "Ork", karma: 0, metavariants: [] },
      ] as never,
      karma_talents: [{ name: "Mundane", label: "Mundane" }],
    } as never);
    renderTab({ catalog, character: { build_method: "Karma" }, patch });
    fireEvent.click(screen.getByRole("button", { name: /Ork/ }));
    expect(patch).toHaveBeenCalledWith({ metatype: "Ork", metavariant: null });
  });

  /**
   * The special-point column on the metatype buttons reads "/ 特殊点 2" and
   * nothing on the page says what those buy — the one thing a first character
   * gets wrong here. The tip is the answer; this pins it to the tab.
   */
  it("explains the special points, the metavariants and the talent", () => {
    renderTab();
    const button = screen.getByRole("button", { name: "メタタイプの選び方 の説明" });
    const tip = screen.getByRole("tooltip", { hidden: true });
    expect(button.getAttribute("aria-describedby")).toBe(tip.id);
    expect(tip.textContent).toContain("特殊点はエッジ");
    expect(tip.textContent).toContain("メタバリアント");
  });
});
