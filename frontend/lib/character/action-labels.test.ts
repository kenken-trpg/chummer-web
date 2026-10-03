import { actionLabel } from "@/lib/character/action-labels";
import { testUi } from "@/tests/fixtures";

const tr = (name: string) => ({ Hack: "ハック" })[name] ?? name;

describe("actionLabel", () => {
  it("reads the Matrix actions in Japanese, not as the data names them", () => {
    expect(actionLabel("Brute Force", testUi, tr)).toBe("強行アクセス");
    expect(actionLabel("Matrix Perception", testUi, tr)).toBe("マトリックス知覚");
    expect(actionLabel("Full Matrix Defense", testUi, tr)).toBe("マトリックス全力防御");
    expect(actionLabel("Spoof Command", testUi, tr)).toBe("コマンド偽装");
  });

  it("covers the non-Matrix action a dice-pool bonus can name", () => {
    expect(actionLabel("Threading", testUi, tr)).toBe("スレッディング");
  });

  it("falls back to the name translator, not to the English name", () => {
    // the player types into the same field, and a data update could name an
    // action this table has never heard of
    expect(actionLabel("Hack", testUi, tr)).toBe("ハック");
    expect(actionLabel("何かした", testUi, tr)).toBe("何かした");
  });
});
