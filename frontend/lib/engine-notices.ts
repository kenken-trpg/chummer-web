import { type MsgKey, MESSAGES, type UiFn } from "@/lib/i18n";

/**
 * A message from the rules engine: a dictionary key plus its parameters, with
 * the wording living in `lib/i18n/messages.ts` (see `backend/app/notices.py`
 * for why). Parameters are primitives, except for the two wrappers the backend
 * uses to say "this is not literal text":
 *
 * - `{ tr: "Ares Predator V" }` — a catalog name, to run through `tr` so it
 *   reads in the current locale.
 * - `{ ui: "engine.slot.arm" }` — a word from the engine's own fixed
 *   vocabulary (limb slots, host kinds), which is a dictionary key like any
 *   other.
 *
 * A list parameter renders as `a / b / c`.
 */
export type Term = { tr: string };
export type Phrase = { ui: string };
export type NoticeParam = string | number | boolean | Term | Phrase | (string | Term)[];

export interface Notice {
  key: string;
  params?: Record<string, NoticeParam>;
}

const LIST_SEPARATOR = " / ";

function isTerm(v: NoticeParam): v is Term {
  return typeof v === "object" && v !== null && "tr" in v;
}

function isPhrase(v: NoticeParam): v is Phrase {
  return typeof v === "object" && v !== null && "ui" in v;
}

/** A key the dictionary actually has. Anything else renders as itself, which is
 *  how an engine that shipped ahead of the front end shows up: visibly, as
 *  `engine.foo.bar`, rather than as a crash or a blank line. */
export function isMsgKey(key: string): key is MsgKey {
  return key in MESSAGES.ja;
}

function renderParam(value: NoticeParam, ui: UiFn, tr: (name: string) => string): string | number {
  if (Array.isArray(value)) {
    return value.map((item) => renderParam(item, ui, tr)).join(LIST_SEPARATOR);
  }
  if (isTerm(value)) return tr(value.tr);
  if (isPhrase(value)) return isMsgKey(value.ui) ? ui(value.ui) : value.ui;
  if (typeof value === "boolean") return String(value);
  return value;
}

/** One engine notice as a sentence in the reader's locale. */
export function renderNotice(
  notice: Notice,
  ui: UiFn,
  tr: (name: string) => string = (name) => name,
): string {
  const vars: Record<string, string | number> = {};
  for (const [name, value] of Object.entries(notice.params ?? {})) {
    vars[name] = renderParam(value, ui, tr);
  }
  return isMsgKey(notice.key) ? ui(notice.key, vars) : notice.key;
}

/** Several notices as one line — the shape the engine uses when a summary is
 *  a list of independent facts (a drug's effects, say) rather than a sentence. */
export function renderNotices(
  notices: Notice[] | undefined,
  ui: UiFn,
  tr: (name: string) => string = (name) => name,
): string {
  return (notices ?? []).map((n) => renderNotice(n, ui, tr)).join(LIST_SEPARATOR);
}

/** A vehicle mod slot category (`Powertrain`, `Weapons`, …) as a label. The
 *  engine ships the category, not a translated name — the same key the
 *  over-capacity notice uses. */
export function vehicleSlotLabel(category: string, ui: UiFn): string {
  const key = `engine.vehicleSlot.${category}`;
  return isMsgKey(key) ? ui(key) : category;
}
