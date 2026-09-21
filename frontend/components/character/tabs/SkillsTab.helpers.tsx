import { useState } from "react";
import { render } from "@testing-library/react";
import { SkillsTab } from "@/components/character/tabs/SkillsTab";
import type { Character } from "@/lib/types";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";

/** Shared by the `SkillsTab.*.test.tsx` files. */

export const blades = {
  id: "blades",
  name: "Blades",
  attribute: "AGI",
  category: "Combat Active",
  skillgroup: "Close Combat",
  source: "SR5",
  specs: ["Swords"],
};
export const exoticSkill = {
  id: "exranged",
  name: "Exotic Ranged Weapon",
  attribute: "AGI",
  category: "Combat Active",
  skillgroup: null,
  source: "SR5",
  exotic: true,
};
export const knowItem = {
  name: "Magic Theory",
  category: "Academic",
  attribute: "LOG",
  source: "SR5",
};

export function skillsCatalog(over: Record<string, unknown> = {}) {
  return makeCatalog({
    skills: { groups: ["Close Combat"], skills: [blades], knowledge: [], ...over },
  } as never);
}

export function renderTab(
  over: {
    character?: Parameters<typeof makeCharacter>[0];
    catalog?: ReturnType<typeof makeCatalog>;
    patch?: (b: Record<string, unknown>) => void;
    setCharacter?: (c: Character) => void;
  } = {},
) {
  const ch = makeCharacter(over.character);
  return render(
    <SkillsTab
      {...panelProps(ch, {
        catalog: over.catalog ?? skillsCatalog(),
        patch: over.patch ?? (() => {}),
        setCharacter: over.setCharacter ?? (() => {}),
      })}
    />,
  );
}

/**
 * The sliders are controlled inputs whose value comes from `character`, so a
 * `fireEvent.change` against a static render is reverted by React before the
 * commit handler ever reads it — the handler sees the old value and the test
 * passes for the wrong reason, or fails for a reason that is not a bug. Any
 * test that changes a slider and then commits has to hold real state.
 */
export function renderStateful(
  patch: (b: Record<string, unknown>) => void,
  init: Parameters<typeof makeCharacter>[0] = {},
  catalog = skillsCatalog(),
) {
  function Harness() {
    const [ch, setCh] = useState<Character>(() => makeCharacter(init));
    return <SkillsTab {...panelProps(ch, { catalog, patch, setCharacter: setCh })} />;
  }
  return render(<Harness />);
}

/** A derived knowledge row, shaped as `d.knowledge_skills` delivers it. */
export const knowRow = (name: string, over: Record<string, unknown> = {}) => ({
  name,
  category: "Academic",
  attribute: "LOG",
  rating: 1,
  native: false,
  ...over,
});

export const language = (name: string, over: Record<string, unknown> = {}) =>
  knowRow(name, { category: "Language", ...over });
