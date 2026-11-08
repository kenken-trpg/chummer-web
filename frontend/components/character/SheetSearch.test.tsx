import { fireEvent, render, screen } from "@testing-library/react";
import { SheetSearch } from "./SheetSearch";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import type { Catalog } from "@/lib/types";
import { makeCharacter, makeCatalog, identityTr } from "@/tests/fixtures";

it("searches offscreen character data and navigates to the exact selected row", () => {
  const ed = {
    ch: makeCharacter({
      gear: [{ id: "kit", gear_id: "spec", notes: "共有物", nickname: "救急袋" }],
    }),
    catalog: makeCatalog({ gear: [{ id: "spec", name: "Medkit" }] as Catalog["gear"] }),
    tr: identityTr,
  } as unknown as CharacterEditor;
  const onNavigate = vi.fn();
  const { rerender } = render(<SheetSearch ed={ed} onNavigate={onNavigate} />);
  fireEvent.change(screen.getByRole("searchbox", { name: "シート内容を検索" }), {
    target: { value: "共有物" },
  });
  screen.getByText("1件見つかりました。");
  fireEvent.click(screen.getByRole("button", { name: "救急袋 — Medkit" }));
  expect(onNavigate).toHaveBeenCalledWith({ key: "gear/kit", tab: "gear", gearKind: "misc" });
  rerender(<SheetSearch ed={{ ...ed, ch: makeCharacter() }} onNavigate={onNavigate} />);
  screen.getByText("一致する項目がありません。");
});
