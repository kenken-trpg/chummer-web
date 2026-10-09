import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { SkillPickSelects } from "@/components/character/SkillPickSelects";
import { identityTr } from "@/tests/fixtures";
import type { SkillPickSlot } from "@/lib/types";

const slot: SkillPickSlot = {
  key: "ware:rr:0",
  source: "Reflex Recorder",
  source_kind: "bioware",
  source_id: "rr",
  picked: "Automatics",
  bonus: 1,
  max: 0,
  rating: 0,
  options: ["Automatics", "Longarms"],
  knowledgeskills: false,
};

describe("SkillPickSelects", () => {
  it("translates an exotic skill and its target while preserving its saved key", () => {
    const onPick = vi.fn();
    const name = "Exotic Ranged Weapon (Lasers)";
    const tr = (value: string) =>
      ({ "Exotic Ranged Weapon": "特殊射撃武器", Lasers: "レーザー" })[value] || value;
    render(
      <SkillPickSelects
        slots={[{ ...slot, picked: "", options: [name] }]}
        tr={tr}
        onPick={onPick}
      />,
    );
    const option = screen.getByRole("option", {
      name: "特殊射撃武器 (レーザー)",
    }) as HTMLOptionElement;
    expect(option.value).toBe(name);
    fireEvent.change(screen.getByRole("combobox"), { target: { value: name } });
    expect(onPick).toHaveBeenCalledWith(slot.key, name);
  });

  it("explains an empty choice and enables it when an eligible skill becomes available", () => {
    const onPick = vi.fn();
    const confidence: SkillPickSlot = {
      ...slot,
      key: "quality:confidence:0",
      source: "自信喪失",
      source_kind: "quality",
      source_id: "confidence",
      picked: "",
      bonus: -2,
      minimum_rating: 4,
      options: [],
    };
    const { rerender } = render(
      <SkillPickSelects slots={[confidence]} tr={identityTr} onPick={onPick} />,
    );
    const select = screen.getByRole("combobox", {
      name: "自信喪失 の技能 -2",
    }) as HTMLSelectElement;
    expect(select.disabled).toBe(true);
    expect(select.options[0].textContent).toBe("条件に合う技能がありません");
    const hint = document.getElementById(select.getAttribute("aria-describedby")!);
    expect(hint?.textContent).toContain("対象はレーティング4以上の技能です。");
    expect(hint?.textContent).toContain(
      "「技能」タブで対象にしたい技能をレーティング4以上にしてください。",
    );

    rerender(
      <SkillPickSelects
        slots={[{ ...confidence, options: ["Gymnastics"] }]}
        tr={identityTr}
        onPick={onPick}
      />,
    );
    expect(select.disabled).toBe(false);
    expect(screen.getByText("対象はレーティング4以上の技能です。")).toBeDefined();
    expect(screen.queryByText(/「技能」タブで対象にしたい技能/)).toBeNull();
    fireEvent.change(select, { target: { value: "Gymnastics" } });
    expect(onPick).toHaveBeenCalledWith("quality:confidence:0", "Gymnastics");
  });

  it("does not invent a rating requirement for an empty choice without one", () => {
    render(
      <SkillPickSelects
        slots={[{ ...slot, picked: "", options: [] }]}
        tr={identityTr}
        onPick={() => undefined}
      />,
    );
    const select = screen.getByRole("combobox") as HTMLSelectElement;
    expect(select.disabled).toBe(true);
    const hint = document.getElementById(select.getAttribute("aria-describedby")!);
    expect(hint?.textContent).toContain("対象技能の条件と「技能」タブの内容を確認してください。");
    expect(hint?.textContent).not.toContain("レーティング");
  });

  it("says the group defaults freely once the recorder is optimized", () => {
    render(
      <SkillPickSelects
        slots={[{ ...slot, default_free: true }]}
        tr={identityTr}
        onPick={() => undefined}
      />,
    );
    expect(screen.getByText(/デフォルト −1 なし/)).toBeTruthy();
  });

  it("says nothing about defaulting for a recorder on its own", () => {
    render(<SkillPickSelects slots={[slot]} tr={identityTr} onPick={() => undefined} />);
    expect(screen.queryByText(/デフォルト −1 なし/)).toBeNull();
  });

  it("labels an Accuracy pick as Accuracy, not dice", () => {
    const { container } = render(
      <SkillPickSelects
        slots={[
          {
            ...slot,
            key: "ware:opt:acc0",
            source: "Cyberlimb Optimization",
            picked: "",
            bonus: 0,
            accuracy: 1,
          },
        ]}
        tr={identityTr}
        onPick={() => undefined}
      />,
    );
    const label = container.querySelector("label")!.textContent!;
    expect(label).toContain("Cyberlimb Optimization の技能 武器の精度+1");
    expect(label).not.toMatch(/\+1 /);
  });
});
