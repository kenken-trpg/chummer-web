import { fireEvent, render, screen } from "@testing-library/react";
import { CreationReview } from "./CreationReview";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { makeCharacter, panelProps } from "@/tests/fixtures";

function setup() {
  const ch = makeCharacter({
    derived: { errors: [{ key: "engine.skills.pointsOver", params: { used: 6, max: 5 } }] },
  });
  const ed = {
    careerReview: ch,
    confirmCareerReview: vi.fn().mockResolvedValue(undefined),
    cancelCareerReview: vi.fn(),
    pendingGear: [{ name: "Unresolved" }],
    error: null,
  } as unknown as CharacterEditor;
  return { ed, panel: panelProps(ch), setTab: vi.fn() };
}

it("shows creation findings, budgets and unresolved import rows before confirmation", () => {
  const props = setup();
  render(<CreationReview {...props} />);
  screen.getByRole("region", { name: "作成完了前の確認" });
  screen.getByRole("table", { name: "残りポイント・資金" });
  screen.getByText("取り込み後に未確定の装備が1件あります。");
  expect(props.ed.confirmCareerReview).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "確認してキャリアへ移行" }));
  expect(props.ed.confirmCareerReview).toHaveBeenCalledOnce();
});

it("returns to editing without entering career", () => {
  const props = setup();
  render(<CreationReview {...props} />);
  fireEvent.click(screen.getByRole("button", { name: "カルマの編集タブへ" }));
  expect(props.ed.cancelCareerReview).toHaveBeenCalledOnce();
  expect(props.setTab).toHaveBeenCalledWith("qualities");
  expect(props.ed.confirmCareerReview).not.toHaveBeenCalled();
});

it("shows nothing when the character no longer has a pending review", () => {
  const props = setup();
  const { container } = render(
    <CreationReview {...props} ed={{ ...props.ed, careerReview: null }} />,
  );
  expect(container.innerHTML).toBe("");
});
