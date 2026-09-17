/**
 * The Japanese dictionary. `ja` is the reference locale — it mirrors the
 * wording the backend engine emits, so every key is defined here first and
 * `MsgKey` is derived from it.
 *
 * Every other locale must then be *complete*: `Catalog` is typed
 * `Record<MsgKey, string>`, so adding a key to `JA` breaks the build until each
 * locale has it. `en` drifted to two keys behind while it was `Partial`, and a
 * silent fall back to Japanese is worse than an obviously-untranslated string —
 * an English reader cannot tell a missing translation from a deliberate one.
 * See docs/i18n.md.
 *
 * The strings themselves live in `ja/`, one file per area, because 1,800 keys
 * in one object is hard to move around in and TypeScript's duplicate-key error
 * (TS1117) only fires inside a single object literal. Spreading them here would
 * make a key defined twice in two different files silently win by order, so
 * `locales.test.ts` fails on a key that appears in more than one file.
 */
import { JA_APP } from "./ja/app";
import { JA_CHARGEN } from "./ja/chargen";
import { JA_ENGINE } from "./ja/engine";
import { JA_GEAR } from "./ja/gear";
import { JA_HELP } from "./ja/help";
import { JA_MAGIC } from "./ja/magic";
import { JA_RULES } from "./ja/rules";
import { JA_SHEET } from "./ja/sheet";
import { JA_SIDEBAR } from "./ja/sidebar";

export const JA = {
  ...JA_APP,
  ...JA_ENGINE,
  ...JA_SHEET,
  ...JA_SIDEBAR,
  ...JA_RULES,
  ...JA_CHARGEN,
  ...JA_GEAR,
  ...JA_MAGIC,
  ...JA_HELP,
} as const;

export type MsgKey = keyof typeof JA;

/** A complete locale. Adding a key to `JA` fails the build until every other
 *  locale file defines it — that is the whole point of the type. */
export type Catalog = Record<MsgKey, string>;
