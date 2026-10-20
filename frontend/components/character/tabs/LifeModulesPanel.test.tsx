import { render, screen, fireEvent, within, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { LifeModulesPanel } from "./LifeModulesPanel";
import { LifeModulePicker } from "./LifeModulePicker";
import { makeCatalog, makeCharacter, panelProps } from "@/tests/fixtures";
import type { LifeModuleCatalogItem } from "@/lib/types/catalog";

const historyModule: LifeModuleCatalogItem = {
  id: "hunter",
  name: "Bounty Hunter",
  parent: "",
  story: "You track fugitives for a living.",
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
  fireEvent.click(screen.getAllByRole("button", { name: /Bounty Hunter:.*Remove this module/ })[1]);
  expect(patch).toHaveBeenCalledWith({
    life_modules: ["hunter"],
    life_module_choices: { "0:0": "Seattle" },
  });
});
it("shifts later choices when removing an earlier occurrence", () => {
  const patch = setup();
  fireEvent.click(screen.getAllByRole("button", { name: /Bounty Hunter:.*Remove this module/ })[0]);
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
it("lets users inspect unsupported candidates but prevents adding them", () => {
  const patch = setup();
  fireEvent.click(screen.getByRole("radio", { name: /Complex module/ }));
  const preview = document.querySelector(".life-preview")!;
  expect(within(preview as HTMLElement).getByText(/contains unsupported effects/)).toBeTruthy();
  const add = screen.getByRole("button", { name: "Add this module" }) as HTMLButtonElement;
  expect(add.disabled).toBe(true);
  fireEvent.click(add);
  expect(patch).not.toHaveBeenCalled();
});
it("prevents changing history in career mode", () => {
  setup({ career: true });
  for (const control of [
    ...screen.getAllByRole("combobox"),
    ...screen.getAllByRole("radio"),
    // a "?" only reads, so it stays open to a career character
    ...screen
      .getAllByRole("button")
      .filter((b) => !b.getAttribute("aria-label")?.endsWith("の説明")),
  ])
    expect((control as HTMLInputElement).disabled || control.closest("fieldset")?.disabled).toBe(
      true,
    );
  expect(screen.getByRole("button", { name: "Module karma の説明" })).toHaveProperty(
    "disabled",
    false,
  );
});
it("shows English requirements while inspecting a candidate whose metatype does not match", () => {
  const patch = setup({ metatype: "Human" });
  fireEvent.click(screen.getByRole("radio", { name: /Trog Life.*Requires:.*Ork.*Troll/ }));
  expect(screen.getByText(/Requires:.*Ork.*Troll.*Requirements are not met/).className).toBe(
    "error",
  );
  expect(
    (screen.getByRole("button", { name: "Add this module" }) as HTMLButtonElement).disabled,
  ).toBe(true);
  expect(patch).not.toHaveBeenCalled();
});
it("allows an alternative metatype and the quality provided by the selected talent", () => {
  setup({ metatype: "Troll", talent: "Magician" });
  for (const name of [/Trog Life/, /Magical Education/]) {
    fireEvent.click(screen.getByRole("radio", { name }));
    expect(
      (screen.getByRole("button", { name: "Add this module" }) as HTMLButtonElement).disabled,
    ).toBe(false);
  }
});
it("warns about selected histories after their prerequisites stop matching", () => {
  setup({ metatype: "Human", life_modules: ["trog"] });
  expect(
    screen.getByText(/Requires:.*Ork.*Troll.*Requirements are not met/, { selector: "p" })
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
  fireEvent.change(screen.getByRole("textbox", { name: "Bounty Hunter: choose Flashbacks I" }), {
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
  fireEvent.change(screen.getByRole("combobox", { name: "Bounty Hunter: choose 知識カテゴリー" }), {
    target: { value: "Professional" },
  });
  expect(patch).toHaveBeenCalledWith({
    life_module_choices: { "0:k8": "Professional", "0:s1": "Desert" },
  });
  expect(
    (
      screen.getByRole("textbox", {
        name: "Bounty Hunter: choose Navigation: Specialization",
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
    name: "Bounty Hunter: choose 知識技能",
  }) as HTMLInputElement[];
  expect(inputs[0].list?.options[0].value).toBe("New Hlobane");
  expect(inputs[0].getAttribute("list")).not.toBe(inputs[1].getAttribute("list"));
  fireEvent.change(inputs[1], { target: { value: "Durban" } });
  expect(patch).toHaveBeenCalledWith({ life_module_choices: { "1:8": "Durban" } });
});

it("asks for the quality level and then that level's own free text", async () => {
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
      name: "Bounty Hunter: choose Corporate Pariah I / Corporate Pariah II",
    }),
    { target: { value: "Corporate Pariah II" } },
  );
  expect(patch).toHaveBeenCalledWith({ life_module_choices: { "0:2": "Corporate Pariah II" } });
  await waitFor(() =>
    expect(
      screen
        .getByRole("textbox", { name: "Bounty Hunter: choose Corporate Pariah" })
        .closest("fieldset")?.disabled,
    ).toBe(false),
  );
  fireEvent.change(
    screen.getByRole("textbox", { name: "Bounty Hunter: choose Corporate Pariah" }),
    {
      target: { value: "Ares Macrotechnology" },
    },
  );
  expect(patch).toHaveBeenCalledWith({ life_module_choices: { "0:x2": "Ares Macrotechnology" } });
});

it("names the life stage in English, because the stage is Run Faster data", () => {
  setup();
  // The picker label and the section heading both read from the data, so the
  // Japanese UI says "Real Life", not 実生活.
  expect(screen.getByRole("heading", { name: "Real Life" })).toBeTruthy();
  expect(screen.getByRole("group", { name: "Real Life: Choose a module" })).toBeTruthy();
  expect(screen.queryByText("実生活")).toBeNull();
});

it("filters candidates by description without hiding selected modules or their choices", () => {
  setup();
  fireEvent.change(screen.getByRole("searchbox", { name: /Search modules/ }), {
    target: { value: "  FUGITIVES  " },
  });
  expect(screen.getByRole("radio", { name: /Bounty Hunter/ })).toBeTruthy();
  fireEvent.change(screen.getByRole("searchbox"), { target: { value: "no such history" } });
  expect(screen.queryByRole("radio", { name: /Bounty Hunter/ })).toBeNull();
  expect(screen.getByText(/No modules match your search/)).toBeTruthy();
  expect(screen.getAllByText(historyModule.story)).toHaveLength(2);
  expect(screen.getAllByRole("combobox", { name: /Bounty Hunter:/ })).toHaveLength(2);
  fireEvent.change(screen.getByRole("searchbox"), { target: { value: "" } });
  expect(screen.getByRole("radio", { name: /Bounty Hunter/ })).toBeTruthy();
});

it("keeps book restrictions when searching and distinguishes an empty catalog from no matches", () => {
  setup({ settings: { books: ["SR5"] } });
  fireEvent.change(screen.getByRole("searchbox"), { target: { value: "hunter" } });
  expect(screen.queryByRole("radio", { name: /Bounty Hunter/ })).toBeNull();
  expect(screen.queryByText(/No modules match your search/)).toBeNull();
  expect(screen.getAllByText(/No modules for this stage/)).toHaveLength(5);
});

it("lets users remove an unknown module while preserving later modules' choice positions", () => {
  const patch = setup({
    life_modules: ["missing-id", "hunter"],
    life_module_choices: { "0:0": "obsolete", "1:0": "Denver" },
  });
  expect(screen.getByText("Unknown Life Module: missing-id")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "missing-id: Remove this module" }));
  expect(patch).toHaveBeenCalledWith({
    life_modules: ["hunter"],
    life_module_choices: { "0:0": "Denver" },
  });
});

it("keeps unknown modules read-only in career mode", () => {
  setup({ life_modules: ["missing-id"], career: true });
  expect(
    (screen.getByRole("button", { name: "missing-id: Remove this module" }) as HTMLButtonElement)
      .disabled,
  ).toBe(true);
});

it("collapses descriptions while keeping the module's choices available", () => {
  setup();
  const description = screen.getAllByText("Module description")[0];
  const details = description.closest("details")!;
  expect(details.open).toBe(false);
  expect(details.textContent).toContain(historyModule.story);
  expect(screen.getAllByRole("combobox", { name: /Bounty Hunter:/ })).toHaveLength(2);
  expect(screen.getAllByText("Not selected")).toHaveLength(4);
  expect(screen.getByText("Selected")).toBeTruthy();
});

it("browses candidates without saving and adds only the explicitly confirmed candidate", async () => {
  const patch = setup({ life_modules: [] });
  fireEvent.click(screen.getByRole("radio", { name: /Bounty Hunter/ }));
  expect(patch).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("radio", { name: /Magical Education/ }));
  expect(patch).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("radio", { name: /Bounty Hunter/ }));
  fireEvent.click(screen.getByRole("button", { name: "Add this module" }));
  expect(patch).toHaveBeenCalledExactlyOnceWith({ life_modules: ["hunter"] });
  await waitFor(() =>
    expect(
      (screen.getByRole("button", { name: "Add this module" }) as HTMLButtonElement).disabled,
    ).toBe(true),
  );
});

it("does not add a preview hidden by search", () => {
  const patch = setup();
  fireEvent.click(screen.getByRole("radio", { name: /Bounty Hunter/ }));
  fireEvent.change(screen.getByRole("searchbox"), { target: { value: "Magical" } });
  expect(screen.queryByRole("radio", { name: /Bounty Hunter/ })).toBeNull();
  const add = screen.getByRole("button", { name: "Add this module" }) as HTMLButtonElement;
  expect(add.disabled).toBe(true);
  fireEvent.click(add);
  expect(patch).not.toHaveBeenCalled();
});

it("rechecks requirements, stage capacity, and rulebooks when a preview is open", () => {
  const patch = vi.fn();
  const candidate = { ...historyModule, required: [{ tag: "metatype", name: "Troll" }] };
  const props = {
    ...panelProps(makeCharacter({ metatype: "Troll", life_modules: [] }), { patch }),
    stage: "Nationality",
    candidates: [candidate],
    taken: false,
    repeatable: false,
  };
  const view = render(<LifeModulePicker {...props} />);
  fireEvent.click(screen.getByRole("radio", { name: /Bounty Hunter/ }));
  const add = () => screen.getByRole("button", { name: "Add this module" }) as HTMLButtonElement;
  expect(add().disabled).toBe(false);
  view.rerender(<LifeModulePicker {...props} character={makeCharacter({ metatype: "Human" })} />);
  expect(add().disabled).toBe(true);
  view.rerender(<LifeModulePicker {...props} taken />);
  expect(screen.getByText(/This stage already has a module/)).toBeTruthy();
  expect(add().disabled).toBe(true);
  view.rerender(<LifeModulePicker {...props} candidates={[]} />);
  expect(screen.queryByRole("heading", { name: "Bounty Hunter" })).toBeNull();
  expect(add().disabled).toBe(true);
  fireEvent.click(add());
  expect(patch).not.toHaveBeenCalled();
});

it("prevents repeated submissions while adding a candidate", async () => {
  let finish!: () => void;
  const patch = vi.fn(
    () =>
      new Promise<void>((resolve) => {
        finish = resolve;
      }),
  );
  const props = panelProps(makeCharacter({ life_modules: [] }), { patch });
  render(
    <LifeModulePicker
      {...props}
      stage="Real Life"
      candidates={[historyModule]}
      taken={false}
      repeatable
    />,
  );
  fireEvent.click(screen.getByRole("radio", { name: /Bounty Hunter/ }));
  const add = screen.getByRole("button", { name: "Add this module" });
  fireEvent.click(add);
  fireEvent.click(add);
  expect(patch).toHaveBeenCalledTimes(1);
  finish();
  await waitFor(() =>
    expect((screen.getByRole("radio", { name: /Bounty Hunter/ }) as HTMLInputElement).checked).toBe(
      false,
    ),
  );
});

it("prevents adding a selected adult module again", () => {
  const patch = setup({ life_modules: ["hunter"] });
  fireEvent.click(screen.getByRole("radio", { name: /Bounty Hunter/ }));
  const add = screen.getByRole("button", { name: "Add this module" }) as HTMLButtonElement;
  expect(add.disabled).toBe(true);
  expect(screen.getByText("This module or one of its versions is already taken")).toBeTruthy();
  fireEvent.click(add);
  expect(patch).not.toHaveBeenCalled();
});

it("prevents a second Corporate version but allows a different career", () => {
  const patch = vi.fn();
  const corporate = {
    ...historyModule,
    id: "hacker",
    name: "Hacker/Decker",
    parent: "Corporate",
    family_id: "corporate",
  };
  const rigger = { ...corporate, id: "rigger", name: "Security Rigger" };
  const props = panelProps(makeCharacter({ life_modules: ["hacker"] }), {
    catalog: makeCatalog({ life_modules: [corporate, rigger, historyModule] }),
    patch,
  });
  render(<LifeModulesPanel {...props} />);
  fireEvent.click(screen.getByRole("radio", { name: /Security Rigger/ }));
  expect(
    (screen.getByRole("button", { name: "Add this module" }) as HTMLButtonElement).disabled,
  ).toBe(true);
  fireEvent.click(screen.getByRole("radio", { name: /Bounty Hunter/ }));
  fireEvent.click(screen.getByRole("button", { name: "Add this module" }));
  expect(patch).toHaveBeenCalledWith({ life_modules: ["hacker", "hunter"] });
});

it("explains the module karma, and the free quality points only when a module gives some", () => {
  setup();
  fireEvent.click(screen.getByRole("button", { name: "Module karma の説明" }));
  expect(screen.getByText(/same creation karma as everything else/)).toBeDefined();
  expect(screen.queryByText(/Free quality points: positive qualities cost no karma/)).toBeNull();
});

it("explains the skill caps beside the line that names them", () => {
  setup({
    derived: {
      life_module_skills: {
        version: 2,
        policy: { version: "2", active_cap: 7, knowledge_cap: 9 },
        free_active: {},
        free_knowledge: {},
        native_languages: [],
        groups: [],
        pools: [],
        losses: [],
      },
    } as never,
  });
  expect(screen.getByRole("button", { name: "経歴付与の上限 の説明" })).toBeDefined();
  expect(screen.getByText(/この値までしか数えない/)).toBeDefined();
  expect(screen.getByText(/同じ関連能力値の別の技能へ移せる/)).toBeDefined();
});
