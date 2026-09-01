import { useState } from "react";
import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { SkillsTab } from "@/components/character/tabs/SkillsTab";
import type { Character } from "@/lib/types";
import { identityTr, makeCatalog, makeCharacter } from "@/tests/fixtures";

/* eslint-disable @typescript-eslint/no-explicit-any */

const blades = {
  id: "blades",
  name: "Blades",
  attribute: "AGI",
  category: "Combat Active",
  skillgroup: "Close Combat",
  source: "SR5",
  specs: ["Swords"],
};
const exoticSkill = {
  id: "exranged",
  name: "Exotic Ranged Weapon",
  attribute: "AGI",
  category: "Combat Active",
  skillgroup: null,
  source: "SR5",
  exotic: true,
};
const knowItem = {
  name: "Magic Theory",
  category: "Academic",
  attribute: "LOG",
  source: "SR5",
};

function skillsCatalog(over: Record<string, unknown> = {}) {
  return makeCatalog({
    skills: { groups: ["Close Combat"], skills: [blades], knowledge: [], ...over },
  } as any);
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
    <SkillsTab
      catalog={over.catalog ?? skillsCatalog()}
      character={ch}
      d={ch.derived}
      tr={identityTr}
      t={(k) => k}
      patch={over.patch ?? (() => {})}
      setCharacter={() => {}}
    />,
  );
}

describe("<SkillsTab>", () => {
  it("renders the point line and the four sections", () => {
    renderTab();
    expect(screen.getByText(/技能 0\/0 ・ グループ 0\/0 ・ 知識 0\/0/)).toBeDefined();
    for (const h of ["技能グループ", "アクティブ技能", "Exotic技能", "知識技能"]) {
      expect(screen.getByRole("heading", { name: h })).toBeDefined();
    }
  });

  it("commits an active-skill rating via patch on mouseUp", () => {
    const patch = vi.fn();
    function Harness() {
      const [ch, setCh] = useState<Character>(() => makeCharacter());
      return (
        <SkillsTab
          catalog={skillsCatalog()}
          character={ch}
          d={ch.derived}
          tr={identityTr}
          t={(k) => k}
          patch={patch}
          setCharacter={setCh}
        />
      );
    }
    render(<Harness />);
    // group slider is first, then the Blades active-skill slider
    const blade = screen.getAllByRole("slider")[1];
    fireEvent.change(blade, { target: { value: "4" } });
    fireEvent.mouseUp(blade);
    expect(patch).toHaveBeenCalledWith({ skills: { Blades: 4 } });
  });

  it("adds a custom knowledge skill with its category", () => {
    const patch = vi.fn();
    renderTab({ patch });
    fireEvent.change(screen.getByPlaceholderText("カスタム知識名"), {
      target: { value: "Underworld" },
    });
    fireEvent.click(screen.getByRole("button", { name: "カスタム追加" }));
    expect(patch).toHaveBeenCalledWith({
      knowledge_skills: { Underworld: 1 },
      native_languages: [],
      knowledge_categories: { Underworld: "Street" },
    });
  });

  it("adds a catalog knowledge skill from the picker", () => {
    const patch = vi.fn();
    renderTab({ catalog: skillsCatalog({ knowledge: [knowItem] }), patch });
    const row = [...document.querySelectorAll(".quality-list .quality-item")].find((el) =>
      el.textContent?.includes("Magic Theory"),
    )!;
    fireEvent.click(row.querySelector("button")!);
    expect(patch).toHaveBeenCalledWith(
      expect.objectContaining({ knowledge_skills: { "Magic Theory": 1 } }),
    );
  });

  it("adds an exotic skill row via patch", () => {
    const patch = vi.fn();
    renderTab({ catalog: skillsCatalog({ skills: [blades, exoticSkill] }), patch });
    fireEvent.click(screen.getByRole("button", { name: /Exotic Ranged Weapon を追加/ }));
    expect(patch).toHaveBeenCalledWith({
      exotic_skills: [{ skill_name: "Exotic Ranged Weapon", extra: "", rating: 1 }],
    });
  });
});
