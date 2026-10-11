import { render, screen, fireEvent } from "@testing-library/react";
import { vi } from "vitest";
import { LifeModulesPanel } from "./LifeModulesPanel";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";
import type { LifeModuleCatalogItem } from "@/lib/types/catalog";

const historyModule: LifeModuleCatalogItem = {
  id: "hunter",
  name: "Bounty Hunter",
  parent: "",
  story: "",
  stage: "Real Life",
  karma: 100,
  nuyen: 0,
  free_positive_qualities: 0,
  free_negative_qualities: 0,
  specialization_grants: [],
  quality_choice_grants: [],
  quality_levels: [],
  source: "RF",
  page: "80",
  unsupported: [],
  grants: [],
  choices: [{ key: "0", kind: "knowledge_skills", options: ["Seattle", "Denver"] }],
};
function setup(over: Parameters<typeof makeCharacter>[0] = {}) {
  const patch = vi.fn();
  const props = panelProps(
    makeCharacter({
      build_method: "LifeModule",
      life_modules: ["hunter", "hunter"],
      life_module_choices: { "0:0": "Seattle", "1:0": "Denver" },
      settings: { books: ["RF"] },
      ...over,
    }),
    {
      catalog: makeCatalog({
        life_modules: [
          historyModule,
          {
            ...historyModule,
            id: "unsupported",
            name: "Complex module",
            unsupported: ["qualitylevel"],
          },
          {
            ...historyModule,
            id: "trog",
            name: "Trog Life",
            required: [
              {
                tag: "oneof",
                children: [
                  { tag: "metatype", name: "Ork" },
                  { tag: "metatype", name: "Troll" },
                ],
              },
            ],
          },
          {
            ...historyModule,
            id: "magic",
            name: "Magical Education",
            required: [{ tag: "quality", name: "Magician" }],
          },
        ],
        karma_talents: [
          { name: "Magician", label: "Magician", magic: 1, resonance: 0, quality: "Magician" },
        ],
      }),
      patch,
    },
  );
  render(<LifeModulesPanel {...props} />);
  return patch;
}
it("removes the second occurrence and keeps the first occurrence's choices", () => {
  const patch = setup();
  fireEvent.click(screen.getAllByRole("button", { name: /Bounty Hunter:.*削除/ })[1]);
  expect(patch).toHaveBeenCalledWith({
    life_modules: ["hunter"],
    life_module_choices: { "0:0": "Seattle" },
  });
});
it("shifts later choices when removing an earlier occurrence", () => {
  const patch = setup();
  fireEvent.click(screen.getAllByRole("button", { name: /Bounty Hunter:.*削除/ })[0]);
  expect(patch).toHaveBeenCalledWith({
    life_modules: ["hunter"],
    life_module_choices: { "0:0": "Denver" },
  });
});
it("patches the second occurrence's selection without changing the first", () => {
  const patch = setup();
  fireEvent.change(screen.getAllByRole("combobox", { name: /Bounty Hunter:/ })[1], {
    target: { value: "Seattle" },
  });
  expect(patch).toHaveBeenCalledWith({
    life_module_choices: { "0:0": "Seattle", "1:0": "Seattle" },
  });
});
it("keeps unsupported candidates visible and disabled", () => {
  setup();
  expect(
    (screen.getByRole("option", { name: /Complex module/ }) as HTMLOptionElement).disabled,
  ).toBe(true);
});
it("prevents changing history in career mode", () => {
  setup({ career: true });
  for (const control of [...screen.getAllByRole("combobox"), ...screen.getAllByRole("button")])
    expect((control as HTMLSelectElement | HTMLButtonElement).disabled).toBe(true);
});
it("shows English requirements and disables candidates whose metatype does not match", () => {
  setup({ metatype: "Human" });
  const option = screen.getByRole("option", { name: /Trog Life.*前提条件:.*Ork.*Troll/ });
  expect((option as HTMLOptionElement).disabled).toBe(true);
});
it("allows an alternative metatype and the quality provided by the selected talent", () => {
  setup({ metatype: "Troll", talent: "Magician" });
  expect((screen.getByRole("option", { name: /Trog Life/ }) as HTMLOptionElement).disabled).toBe(
    false,
  );
  expect(
    (screen.getByRole("option", { name: /Magical Education/ }) as HTMLOptionElement).disabled,
  ).toBe(false);
});
it("warns about selected histories after their prerequisites stop matching", () => {
  setup({ metatype: "Human", life_modules: ["trog"] });
  expect(
    screen.getByText(/前提条件:.*Ork.*Troll.*前提条件を満たしていません/, { selector: "p" })
      .className,
  ).toBe("error");
});

it("labels quality details in English and saves their separate choice slot", () => {
  const patch = vi.fn();
  const props = panelProps(makeCharacter({ life_modules: [historyModule.id] }), {
    catalog: makeCatalog({
      life_modules: [
        {
          ...historyModule,
          choices: [{ key: "q0", kind: "qualities", name: "Flashbacks I", options: [] }],
        },
      ],
    }),
    patch,
  });
  render(<LifeModulesPanel {...props} />);
  fireEvent.change(screen.getByRole("textbox", { name: "Bounty Hunter: Flashbacks Iの選択" }), {
    target: { value: "Street violence" },
  });
  expect(patch).toHaveBeenCalledWith({ life_module_choices: { "0:q0": "Street violence" } });
});

it("keeps knowledge categories in English and saves category and specialization slots", () => {
  const patch = vi.fn();
  const props = panelProps(
    makeCharacter({ life_modules: [historyModule.id], life_module_choices: { "0:s1": "Desert" } }),
    {
      catalog: makeCatalog({
        life_modules: [
          {
            ...historyModule,
            choices: [
              { key: "k8", kind: "knowledge_categories", options: ["Academic", "Professional"] },
              {
                key: "s1",
                kind: "specializations",
                name: "Navigation: Specialization",
                options: [],
              },
            ],
          },
        ],
      }),
      patch,
    },
  );
  render(<LifeModulesPanel {...props} />);
  expect(screen.getByRole("option", { name: "Academic" })).toBeTruthy();
  fireEvent.change(screen.getByRole("combobox", { name: "Bounty Hunter: 知識カテゴリの選択" }), {
    target: { value: "Professional" },
  });
  expect(patch).toHaveBeenCalledWith({
    life_module_choices: { "0:k8": "Professional", "0:s1": "Desert" },
  });
  expect(
    (
      screen.getByRole("textbox", {
        name: "Bounty Hunter: Navigation: Specializationの選択",
      }) as HTMLInputElement
    ).value,
  ).toBe("Desert");
});

it("suggests English place names while allowing a custom city for repeated modules", () => {
  const patch = vi.fn();
  const props = panelProps(makeCharacter({ life_modules: [historyModule.id, historyModule.id] }), {
    catalog: makeCatalog({
      life_modules: [
        {
          ...historyModule,
          choices: [
            { key: "8", kind: "knowledge_skills", options: ["New Hlobane"], allow_custom: true },
          ],
        },
      ],
    }),
    patch,
  });
  render(<LifeModulesPanel {...props} />);
  const inputs = screen.getAllByRole("combobox", {
    name: "Bounty Hunter: 知識技能の選択",
  }) as HTMLInputElement[];
  expect(inputs[0].list?.options[0].value).toBe("New Hlobane");
  expect(inputs[0].getAttribute("list")).not.toBe(inputs[1].getAttribute("list"));
  fireEvent.change(inputs[1], { target: { value: "Durban" } });
  expect(patch).toHaveBeenCalledWith({ life_module_choices: { "1:8": "Durban" } });
});

it("asks for the quality level and then that level's own free text", () => {
  const patch = vi.fn();
  const props = panelProps(makeCharacter({ life_modules: [historyModule.id] }), {
    catalog: makeCatalog({
      life_modules: [
        {
          ...historyModule,
          choices: [
            {
              key: "2",
              kind: "qualities",
              name: "Corporate Pariah I / Corporate Pariah II",
              options: ["Corporate Pariah I", "Corporate Pariah II"],
            },
            { key: "x2", kind: "qualities", name: "Corporate Pariah", options: [] },
          ],
          grants: [
            {
              kind: "qualities",
              name: "",
              value: 1,
              choice: "2",
              category: "",
              extra_choice: "x2",
            },
          ],
        },
      ],
    }),
    patch,
  });
  render(<LifeModulesPanel {...props} />);
  fireEvent.change(
    screen.getByRole("combobox", {
      name: "Bounty Hunter: Corporate Pariah I / Corporate Pariah IIの選択",
    }),
    { target: { value: "Corporate Pariah II" } },
  );
  expect(patch).toHaveBeenCalledWith({ life_module_choices: { "0:2": "Corporate Pariah II" } });
  fireEvent.change(screen.getByRole("textbox", { name: "Bounty Hunter: Corporate Pariahの選択" }), {
    target: { value: "Ares Macrotechnology" },
  });
  expect(patch).toHaveBeenCalledWith({ life_module_choices: { "0:x2": "Ares Macrotechnology" } });
});

it("names the life stage in English, because the stage is Run Faster data", () => {
  setup();
  // The picker label and the section heading both read from the data, so the
  // Japanese UI says "Real Life", not 実生活.
  expect(screen.getByRole("heading", { name: "Real Life" })).toBeTruthy();
  expect(screen.getByRole("combobox", { name: "Real Life: 経歴を選択" })).toBeTruthy();
  expect(screen.queryByText("実生活")).toBeNull();
});
