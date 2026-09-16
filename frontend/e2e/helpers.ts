import { deflateRawSync, inflateRawSync } from "node:zlib";
import { expect, type APIRequestContext, type Page } from "@playwright/test";

/** The editor mints a character on first load; wait for the toolbar it fills. */
export async function waitForEditor(page: Page) {
  await expect(page.getByRole("textbox", { name: "キャラクター名" })).toBeVisible();
}

/**
 * Collect CSP violations. Chromium reports them as console errors, and a
 * blocked script leaves no other trace.
 */
export function watchCsp(page: Page): string[] {
  const violations: string[] = [];
  page.on("console", (msg) => {
    if (msg.type() === "error" && /Content Security Policy/i.test(msg.text())) {
      violations.push(msg.text());
    }
  });
  return violations;
}

/**
 * A share fragment value built the way `lib/character/share.ts` builds one:
 * base64url of deflate-raw JSON. Built here rather than through the UI so a
 * test can hand the receiver exactly what an attacker would.
 */
export function encodeFragment(body: unknown): string {
  return deflateRawSync(Buffer.from(JSON.stringify(body))).toString("base64url");
}

export function decodeFragment(value: string): unknown {
  return JSON.parse(inflateRawSync(Buffer.from(value, "base64url")).toString());
}

/** A valid character straight from the engine, without driving the editor. */
export async function freshCharacter(
  request: APIRequestContext,
  name: string,
): Promise<Record<string, unknown>> {
  const res = await request.post("/api/characters/new", { data: { name } });
  expect(res.ok()).toBe(true);
  return res.json();
}
