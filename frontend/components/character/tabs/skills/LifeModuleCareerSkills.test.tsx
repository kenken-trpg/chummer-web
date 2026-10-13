import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { LifeModuleCareerSkills } from "./LifeModuleCareerSkills";
import { makeCharacter, makeCatalog, panelProps } from "@/tests/fixtures";

it("submits a growth request without fabricating a starting value or a price", async () => {
  const patch = vi.fn();
  const ch = makeCharacter({
    career: true,
    life_module_rules_version: 2,
    life_module_skill_advancements: [],
  });
  const catalog = makeCatalog({
    skills: {
      skills: [
        {
          id: "perception",
          name: "Perception",
          attribute: "INT",
          category: "Physical Active",
          skillgroup: null,
          default: true,
          source: "SR5",
        },
      ],
      groups: [],
      knowledge: [],
    },
  });
  render(<LifeModuleCareerSkills {...panelProps(ch, { catalog, patch })} />);
  fireEvent.change(screen.getByRole("combobox", { name: "Skill or group to advance" }), {
    target: { value: "perception" },
  });
  fireEvent.click(screen.getByRole("button", { name: "Buy advancement" }));
  expect(patch).toHaveBeenCalledWith({
    life_module_skill_advancements: [
      expect.objectContaining({ kind: "active", target_id: "perception", levels: 1 }),
    ],
  });
  const row = patch.mock.calls[0][0].life_module_skill_advancements[0];
  expect(row.price).toBeUndefined();
  expect(row.from_ratings).toBeUndefined();
  await waitFor(() =>
    expect(
      screen.getByRole("button", { name: "Buy advancement" }).closest("fieldset")?.disabled,
    ).toBe(false),
  );
});
