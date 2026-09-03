import type { MsgKey } from "@/lib/i18n/messages";

/**
 * A one-way channel for "this degraded but did not fail" reports from the
 * plumbing (`lib/api`, `lib/character/local-store`) up to whatever is on
 * screen. Those layers must not swallow a failed save or a stale compute in
 * silence, but they also have no locale and no React — so they publish a
 * message *key* and the editor turns it into a sentence.
 *
 * One listener, because there is one editor per app. Registering replaces the
 * previous one; pass `null` to clear (React strict mode mounts twice).
 */
export type NoticeListener = (key: MsgKey) => void;

let listener: NoticeListener | null = null;

export function onNotice(cb: NoticeListener | null): void {
  listener = cb;
}

/** Report a degraded operation. A no-op when nothing is listening. */
export function notify(key: MsgKey): void {
  listener?.(key);
}
