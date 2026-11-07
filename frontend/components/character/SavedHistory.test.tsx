import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { SavedHistory } from "./SavedHistory";
import { getCharacterSnapshots } from "@/lib/character/local-store";
import type { CharacterEditor } from "@/lib/character/useCharacterEditor";
import { makeCharacter } from "@/tests/fixtures";

vi.mock("@/lib/character/local-store", () => ({ getCharacterSnapshots: vi.fn() }));

afterEach(() => vi.restoreAllMocks());

it("asks before restoring and restores the selected snapshot with undo support", async () => {
  const character = makeCharacter({ id: "a", name: "Earlier" });
  vi.mocked(getCharacterSnapshots).mockResolvedValue([{ savedAt: 1000, character }]);
  const restoreSnapshot = vi.fn().mockResolvedValue(undefined);
  const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
  render(<SavedHistory ed={{ ch: character, restoreSnapshot } as unknown as CharacterEditor} />);
  const button = await screen.findByRole("button", { name: "復元する", hidden: true });
  fireEvent.click(button);
  expect(restoreSnapshot).not.toHaveBeenCalled();
  confirm.mockReturnValue(true);
  fireEvent.click(button);
  await waitFor(() => expect(restoreSnapshot).toHaveBeenCalledWith(character, true));
});
