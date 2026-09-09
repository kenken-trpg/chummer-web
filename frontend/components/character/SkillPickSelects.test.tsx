import { render, screen } from "@testing-library/react";
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
});
