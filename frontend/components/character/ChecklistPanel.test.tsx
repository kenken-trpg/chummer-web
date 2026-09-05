import { beforeEach, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { ChecklistPanel } from "@/components/character/ChecklistPanel";
import { identityTr, makeCatalog, makeCharacter, testUi } from "@/tests/fixtures";
import type { TabPanelProps } from "@/components/character/types";

function panelFor(ch: ReturnType<typeof makeCharacter>): TabPanelProps {
  return {
    catalog: makeCatalog(),
    character: ch,
    d: ch.derived,
    tr: identityTr,
    trGroup: identityTr,
    t: (k, f) => f ?? k,
    ui: testUi,
    patch: () => {},
    setCharacter: () => {},
  };
}

beforeEach(() => window.localStorage.clear());

it("shows a pass state with no findings", () => {
  const ch = makeCharacter({ derived: { karma: { pool: 0, spent: 0, remaining: 0 } } });
  render(<ChecklistPanel panel={panelFor(ch)} setTab={() => {}} />);
  expect(screen.getByText("作成チェック")).toBeTruthy();
  expect(screen.getByText(/問題は見つかりませんでした/)).toBeTruthy();
});

it("groups an engine error and jumps to its tab", () => {
  const ch = makeCharacter({
    derived: {
      karma: { pool: 0, spent: 0, remaining: 0 },
      errors: ["技能点が不足しています（使用 5 / 上限 4）"],
    },
  });
  const setTab = vi.fn();
  render(<ChecklistPanel panel={panelFor(ch)} setTab={setTab} />);

  expect(screen.getByText("エラー（作成不可）")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "該当タブへ" }));
  expect(setTab).toHaveBeenCalledWith("skills");
});
