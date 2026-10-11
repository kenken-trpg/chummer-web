import { beforeEach, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { fireEvent } from "@testing-library/dom";
import { makeCatalog, makeCharacter } from "@/tests/fixtures";
import { encodeShare, SHARE_PREFIX } from "@/lib/character/share";
import { MESSAGES } from "@/lib/i18n/messages";

const push = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

const preview = vi.fn();
const importFn = vi.fn();
const loadCatalog = vi.fn();
vi.mock("@/lib/api", () => ({
  api: {
    catalog: (settings: unknown) => loadCatalog(settings),
    preview: (p: unknown) => preview(p),
    import: (p: unknown) => importFn(p),
  },
}));

import SharePage from "@/app/share/page";

function setHash(value: string) {
  window.location.hash = value;
}

beforeEach(() => {
  push.mockReset();
  preview.mockReset();
  importFn.mockReset();
  loadCatalog.mockReset();
  loadCatalog.mockResolvedValue(makeCatalog());
  setHash("");
});

it("decodes the fragment, computes it and renders the sheet read-only", async () => {
  const shared = makeCharacter({ id: "src", name: "夜叉" });
  preview.mockResolvedValue(makeCharacter({ id: "fresh", name: "夜叉" }));
  setHash(SHARE_PREFIX + (await encodeShare(shared)));

  render(<SharePage />);

  await waitFor(() => expect(preview).toHaveBeenCalledTimes(1));
  // the payload posted for compute carries no id and no derived
  const sent = preview.mock.calls[0][0] as Record<string, unknown>;
  expect("id" in sent).toBe(false);
  expect("derived" in sent).toBe(false);
  expect(sent.name).toBe("夜叉");

  await screen.findByText("共有ビュー（読み取り専用）");
  // read-only: none of the editor's mutating controls are present
  expect(screen.queryByText("削除")).toBeNull();
  expect(screen.queryByText("JSON保存")).toBeNull();
  expect(screen.getByText("自分のロースターに取り込む")).toBeTruthy();
});

it("adopting reissues an id, remembers it and leaves the share view", async () => {
  preview.mockResolvedValue(makeCharacter({ id: "fresh", name: "夜叉" }));
  importFn.mockResolvedValue(makeCharacter({ id: "mine", name: "夜叉" }));
  setHash(SHARE_PREFIX + (await encodeShare(makeCharacter({ id: "src", name: "夜叉" }))));

  render(<SharePage />);
  fireEvent.click(await screen.findByText("自分のロースターに取り込む"));

  await waitFor(() => expect(push).toHaveBeenCalledWith("/"));
  const adopted = importFn.mock.calls[0][0] as Record<string, unknown>;
  expect(adopted.id).toBeUndefined();
  expect(adopted.derived).toBeUndefined();
  expect(localStorage.getItem("lastCharacterId")).toBe("mine");
});

it("reports a corrupt fragment instead of calling the backend", async () => {
  setHash(SHARE_PREFIX + "not-real-deflate-data");

  render(<SharePage />);

  await screen.findByText(MESSAGES.ja["share.err.corrupt"]);
  expect(screen.getByRole("alert").textContent).toBe(MESSAGES.ja["share.err.corrupt"]);
  expect(preview).not.toHaveBeenCalled();
});

it("loads the display catalog for the validated shared character's custom data", async () => {
  const shared = makeCharacter({
    metatype: "Centaur",
    settings: { name: "Shared", dataset: "incoming", customdata: ["table>1"] },
  });
  const validated = makeCharacter({
    ...shared,
    settings: { name: "Shared", dataset: "validated", customdata: ["table>2"] },
  });
  preview.mockResolvedValue(validated);
  setHash(SHARE_PREFIX + (await encodeShare(shared)));
  render(<SharePage />);
  await screen.findByText("共有ビュー（読み取り専用）");
  expect(loadCatalog).toHaveBeenCalledExactlyOnceWith(validated.settings);
});

it("does not show a sheet with a different catalog when the shared catalog fails", async () => {
  preview.mockResolvedValue(makeCharacter({ metatype: "Centaur" }));
  loadCatalog.mockRejectedValue(new Error("catalog unavailable"));
  setHash(SHARE_PREFIX + (await encodeShare(makeCharacter({ metatype: "Centaur" }))));
  render(<SharePage />);
  expect((await screen.findByRole("alert")).textContent).toContain("catalog unavailable");
  expect(screen.queryByText("共有ビュー（読み取り専用）")).toBeNull();
  expect(importFn).not.toHaveBeenCalled();
});

it("reports a link with no payload", async () => {
  setHash("#nothing");

  render(<SharePage />);

  await screen.findByText(MESSAGES.ja["share.empty"]);
  expect(preview).not.toHaveBeenCalled();
});
