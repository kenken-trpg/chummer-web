import { useState } from "react";
import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { InitiationTab } from "@/components/character/tabs/InitiationTab";
import type { Character } from "@/lib/types";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";

function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
  } = {},
) {
  const ch = makeCharacter({ talent: "Magician", ...over.character });
  return render(
    <InitiationTab
      {...panelProps(ch, {
        catalog: over.catalog ?? makeCatalog(),
        patch: over.patch ?? (() => {}),
      })}
    />,
  );
}

describe("<InitiationTab>", () => {
  it("renders the grade line and the grade slider", () => {
    renderTab();
    expect(screen.getByText(/等級 0 ・ カルマ 0/)).toBeDefined();
    expect(screen.getByRole("slider")).toBeDefined();
  });

  it("raising the grade patches initiate_grade + one row per grade", () => {
    const patch = vi.fn();
    function Harness() {
      const [ch, setCh] = useState<Character>(() => makeCharacter({ talent: "Magician" }));
      return <InitiationTab {...panelProps(ch, { patch, setCharacter: setCh })} />;
    }
    render(<Harness />);
    const slider = screen.getByRole("slider");
    fireEvent.change(slider, { target: { value: "2" } });
    fireEvent.mouseUp(slider);
    expect(patch).toHaveBeenCalledWith({
      initiate_grade: 2,
      initiations: [
        { grade: 1, kind: "metamagic", option_id: "" },
        { grade: 2, kind: "metamagic", option_id: "" },
      ],
    });
  });

  it("picking a metamagic for a grade choice patches the initiations row", () => {
    const patch = vi.fn();
    renderTab({
      character: {
        initiate_grade: 1,
        initiations: [{ grade: 1, kind: "metamagic", option_id: "" }] as never,
        derived: { initiation: { choices: [{ grade: 1, karma: 13 }] } as never },
      },
      catalog: makeCatalog({
        metamagics: [{ id: "cf", name: "Centering", magician: true, adept: false }] as never,
      }),
      patch,
    });
    const selects = screen.getAllByRole("combobox");
    fireEvent.change(selects[selects.length - 1], { target: { value: "cf" } });
    expect(patch).toHaveBeenCalledWith({
      initiations: [{ grade: 1, kind: "metamagic", option_id: "cf" }],
    });
  });

  it("a grade the tradition scripts only offers the metamagic it names", () => {
    renderTab({
      character: {
        initiate_grade: 1,
        initiations: [{ grade: 1, kind: "metamagic", option_id: "" }] as never,
        derived: {
          initiation: {
            choices: [{ grade: 1, karma: 13, allowed_metamagics: ["Centering"] }],
          } as never,
        },
      },
      catalog: makeCatalog({
        metamagics: [
          { id: "cf", name: "Centering", magician: true, adept: false },
          { id: "qk", name: "Quickening", magician: true, adept: false },
        ] as never,
      }),
    });
    const options = screen.getAllByRole("option").map((el) => el.textContent);
    expect(options).toContain("Centering");
    expect(options).not.toContain("Quickening");
  });
});

it("explains that Masking accepts its art OR an adept quality", () => {
  renderTab({
    character: {
      settings: { books: ["SR5", "SG"] },
      derived: { initiation: { choices: [{ grade: 1, karma: 13 }] } as never },
    },
    catalog: makeCatalog({
      metamagics: [
        {
          id: "mask",
          name: "Masking",
          magician: true,
          adept: true,
          required: ["Masking", "Adept", "Mystic Adept"],
          required_tree: [
            {
              tag: "oneof",
              children: [
                { tag: "art", name: "Masking" },
                { tag: "quality", name: "Adept" },
                { tag: "quality", name: "Mystic Adept" },
              ],
            },
          ],
        },
      ] as never,
    }),
  });
  const option = screen.getByRole("option", { name: /Art（魔術の流派）: Masking/ });
  expect(option.textContent).toContain("または");
  expect(option.textContent).toContain("Adept");
});

it("does not show an Art prerequisite when the character ignores arts", () => {
  renderTab({
    character: {
      settings: { books: ["SR5", "SG"], ignore_art: true },
      derived: { initiation: { choices: [{ grade: 1, karma: 13 }] } as never },
    },
    catalog: makeCatalog({
      metamagics: [
        {
          id: "center",
          name: "Centering",
          magician: true,
          adept: false,
          required: ["Centering"],
          required_tree: [{ tag: "allof", children: [{ tag: "art", name: "Centering" }] }],
        },
      ] as never,
    }),
  });
  expect(screen.getByRole("option", { name: "Centering" }).textContent).not.toContain("要");
});

it("saves a High Art alongside the existing metamagic at the same grade", () => {
  const patch = vi.fn();
  renderTab({
    character: {
      settings: { books: ["SR5", "SG"] },
      initiate_grade: 1,
      initiations: [{ grade: 1, kind: "metamagic", option_id: "mask" }],
      derived: { initiation: { choices: [{ grade: 1, karma: 13, option_id: "mask" }] } as never },
    },
    catalog: makeCatalog({
      metamagics: [{ id: "mask", name: "Masking", magician: true, adept: true }] as never,
      magic_arts: [{ id: "mask-art", name: "Masking", source: "SG", page: "149" }],
    }),
    patch,
  });
  fireEvent.change(screen.getByRole("combobox", { name: "Art 1" }), {
    target: { value: "mask-art" },
  });
  expect(patch).toHaveBeenCalledWith({
    initiations: [{ grade: 1, kind: "metamagic", option_id: "mask", art_ids: ["mask-art"] }],
  });
});
