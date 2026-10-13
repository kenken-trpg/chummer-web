import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { LifeModuleSkillOverflow } from "./LifeModuleSkillOverflow";
import { makeCharacter, testUi } from "@/tests/fixtures";
import type { LifeModuleSkillPool } from "@/lib/types/life-modules";

const pool: LifeModuleSkillPool = {
  key: "entry:perception",
  entry_id: "entry",
  source_skill_id: "perception",
  source_name: "Perception",
  stage: "Real Life",
  before: 6,
  grant: 3,
  kept: 1,
  total: 2,
  allocated: 0,
  remaining: 2,
  unallocatable: 0,
  grant_fingerprint: "a".repeat(64),
  status: "pending",
  provisional: false,
  candidates: [
    {
      skill_id: "navigation",
      name: "Navigation",
      attribute: "INT",
      specific_required: false,
      capacity: 2,
      unavailable_reason: "",
    },
    {
      skill_id: "exotic",
      name: "Exotic",
      attribute: "INT",
      specific_required: true,
      capacity: 7,
      unavailable_reason: "",
    },
    {
      skill_id: "blocked",
      name: "Blocked",
      attribute: "INT",
      specific_required: false,
      capacity: 0,
      unavailable_reason: "unavailable",
    },
  ],
};

function setup(over: Partial<LifeModuleSkillPool> = {}, career = false, patch = vi.fn()) {
  render(
    <LifeModuleSkillOverflow
      character={makeCharacter({ career, life_module_transfers: [] })}
      pool={{ ...pool, ...over }}
      ui={testUi}
      patch={patch}
    />,
  );
  return patch;
}

it("shows overflow and only saves an explicit legal allocation", async () => {
  const patch = setup();
  expect(screen.getByText(/付与前 6.*付与 3.*移し替え 2/)).toBeTruthy();
  fireEvent.change(screen.getByRole("combobox", { name: "移し替え先の技能" }), {
    target: { value: "navigation" },
  });
  fireEvent.change(screen.getByRole("spinbutton"), { target: { value: "2" } });
  expect(patch).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "この配分を追加" }));
  expect(patch).toHaveBeenCalledWith({
    life_module_transfers: [
      expect.objectContaining({
        entry_id: "entry",
        source_skill_id: "perception",
        grant_fingerprint: pool.grant_fingerprint,
        destination_skill_id: "navigation",
        destination_specific: "",
        ranks: 2,
      }),
    ],
  });
  await waitFor(() => expect((screen.getByRole("combobox") as HTMLSelectElement).value).toBe(""));
});

it("blocks amounts beyond the remaining source and fractional levels", () => {
  setup({ remaining: 1 });
  fireEvent.change(screen.getByRole("combobox"), { target: { value: "navigation" } });
  for (const value of ["2", "1.5", "0"]) {
    fireEvent.change(screen.getByRole("spinbutton"), { target: { value } });
    expect(
      (screen.getByRole("button", { name: "この配分を追加" }) as HTMLButtonElement).disabled,
    ).toBe(true);
  }
});

it("requires an actual Exotic target and rejects placeholders", () => {
  setup();
  fireEvent.change(screen.getByRole("combobox"), { target: { value: "exotic" } });
  const add = screen.getByRole("button", { name: "この配分を追加" }) as HTMLButtonElement;
  expect(add.disabled).toBe(true);
  fireEvent.change(screen.getByRole("textbox"), { target: { value: "[Weapon]" } });
  expect(add.disabled).toBe(true);
  fireEvent.change(screen.getByRole("textbox"), { target: { value: "Drone interface" } });
  expect(add.disabled).toBe(false);
});

it("retains the draft after a failed save", async () => {
  const patch = vi.fn().mockRejectedValue(new Error("offline"));
  setup({}, false, patch);
  fireEvent.change(screen.getByRole("combobox"), { target: { value: "navigation" } });
  fireEvent.click(screen.getByRole("button", { name: "この配分を追加" }));
  await waitFor(() => expect(screen.getByRole("alert")).toBeTruthy());
  expect((screen.getByRole("combobox") as HTMLSelectElement).value).toBe("navigation");
});

it("keeps invalid rows repairable and career history read-only", () => {
  const transfer = {
    id: "transfer",
    entry_id: pool.entry_id,
    source_skill_id: pool.source_skill_id,
    grant_fingerprint: pool.grant_fingerprint,
    destination_skill_id: "navigation",
    ranks: 3,
  };
  render(
    <LifeModuleSkillOverflow
      character={makeCharacter({ career: true, life_module_transfers: [transfer] })}
      pool={{ ...pool, status: "invalid" }}
      ui={testUi}
      patch={vi.fn()}
    />,
  );
  expect(screen.getByText(/Navigation: \+3/)).toBeTruthy();
  const remove = screen.getByRole("button", { name: "配分を削除" });
  expect(remove.closest("fieldset")?.disabled).toBe(true);
  expect(screen.queryByRole("combobox")).toBeNull();
});
