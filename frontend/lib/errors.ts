import type { MsgKey } from "@/lib/i18n";
import { ShareError, SHARE_ERROR_KEYS } from "@/lib/character/share";

/**
 * An error raised where there is no locale and no React — `lib/api`,
 * `local-store`, the pure helpers. It carries a message *key*; whoever is on
 * screen turns it into a sentence. Same reasoning as `lib/notices`, but for
 * the failure path rather than the degraded one.
 */
export class MessageError extends Error {
  constructor(readonly key: MsgKey) {
    super(key);
    this.name = "MessageError";
  }
}

/**
 * A user-facing sentence for anything thrown. Our own coded errors are
 * translated; anything else (a fetch failure, an engine 422) already carries a
 * message worth showing, and `fallback` covers the rest.
 */
export function errorMessage(
  e: unknown,
  ui: (key: MsgKey, vars?: Record<string, string | number>) => string,
  fallback: MsgKey,
): string {
  if (e instanceof MessageError) return ui(e.key);
  if (e instanceof ShareError) return ui(SHARE_ERROR_KEYS[e.code]);
  if (e instanceof Error && e.message) return e.message;
  return ui(fallback);
}
