import { expect, test, type Page } from "@playwright/test";
import { freshCharacter, storedCharacters, waitForEditor } from "./helpers";

/** An A.I.'s Core track and home node (DT p.135): with no node it has the
 *  Core track and no Stun one; a deck it lives in lends it the deck's Matrix
 *  monitor; a vehicle lends it the vehicle's damage track as well. One node
 *  at a time, kept across a reload, and cleared by unticking. */
const NAME = "Home node regression";
const DECK = "c3f15a4a-1987-4879-ba74-5b93d602ca8c"; // Shiawase Cyber-5, DR 5
const SCOOTER = "c0d3e7fd-d5fd-48c4-b49d-0c7dea26895d"; // Dodge Scoot: Body 4, Pilot 1

type Stored = {
  home_node?: string;
  derived: {
    condition_monitor: { physical: number; stun: number; core?: boolean; vehicle?: boolean };
    totals: { DEP: number };
  };
};

async function read(page: Page): Promise<Stored> {
  return (await storedCharacters(page)).find((s) => s.name === NAME) as unknown as Stored;
}

async function node(page: Page) {
  const ch = await read(page);
  return { home_node: ch?.home_node ?? "", ...ch?.derived.condition_monitor };
}

test("an A.I. moves into a deck, then a vehicle, and back out", async ({ page, request }) => {
  const state = await freshCharacter(request, NAME);
  Object.assign(state, {
    metatype: "A.I.",
    metavariant: "E-Ghost",
    talent: "A.I.",
    priorities: { Heritage: "A", Attributes: "B", Talent: "C", Skills: "D", Resources: "E" },
    cyberdecks: [{ id: "deck", gear_id: DECK, rating: 1 }],
    vehicles: [{ id: "scooter", gear_id: SCOOTER, rating: 1 }],
  });
  const settings = (state.settings || {}) as { books?: string[] };
  state.settings = { ...settings, books: [...new Set([...(settings.books || []), "DT"])] };
  await page.goto("/");
  await waitForEditor(page);
  await page.getByLabel("読込 (JSON/.chum5/.xlsx)").setInputFiles({
    name: "home-node.json",
    mimeType: "application/json",
    buffer: Buffer.from(JSON.stringify(state)),
  });
  await expect(page.getByRole("textbox", { name: "キャラクター名" })).toHaveValue(NAME);

  // no node: the Core track, 8 + DEP / 2, and no Stun track at all
  await expect.poll(async () => (await node(page)).core).toBe(true);
  const depth = (await read(page)).derived.totals.DEP;
  const core = 8 + Math.ceil(depth / 2);
  const condition = page
    .locator(".stat")
    .filter({ has: page.getByText("コンディション", { exact: true }) })
    .locator(":scope > b");
  await expect(condition).toHaveText(`Core ${core}`);

  // the deck: its Matrix monitor, 8 + DR / 2, stands in for the Stun track
  await page.getByRole("button", { name: "装備", exact: true }).click();
  await page.getByRole("button", { name: "サイバーデッキ", exact: true }).click();
  const deckBox = page.getByRole("checkbox", { name: "Home Node" });
  await deckBox.click();
  await expect
    .poll(() => node(page))
    .toMatchObject({ home_node: "deck", physical: core, stun: 11, vehicle: false });
  await expect(condition).toHaveText(`Core ${core} / マトリックス11`);

  // the scooter: its damage track, 12 + Body / 2, and Pilot 1 as Device Rating
  await page.getByRole("button", { name: "ヴィークル", exact: true }).click();
  await page.getByRole("checkbox", { name: "Home Node" }).click();
  await expect
    .poll(() => node(page))
    .toMatchObject({ home_node: "scooter", physical: 14, stun: 9, vehicle: true });
  await expect(condition).toHaveText("P14 / マトリックス9");
  await expect(page.getByText(/Persona Firmware（DT p\.66）/).first()).toBeVisible();
  await page.getByRole("button", { name: "サイバーデッキ", exact: true }).click();
  await expect(page.getByRole("checkbox", { name: "Home Node" })).not.toBeChecked();

  await page.reload();
  await waitForEditor(page);
  await expect(condition).toHaveText("P14 / マトリックス9");
  await page.getByRole("button", { name: "装備", exact: true }).click();
  await page.getByRole("button", { name: "ヴィークル", exact: true }).click();
  const scooterBox = page.getByRole("checkbox", { name: "Home Node" });
  await expect(scooterBox).toBeChecked();

  // unticking leaves it with its Core track again
  await scooterBox.click();
  await expect.poll(() => node(page)).toMatchObject({ home_node: "", physical: core, stun: 0 });
  await expect(condition).toHaveText(`Core ${core}`);
});
