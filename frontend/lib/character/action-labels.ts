import type { MsgKey, UiFn } from "@/lib/i18n";

/**
 * The named actions a dice-pool bonus can point at, in the reader's language.
 *
 * These are not catalog rows. The Matrix actions come from a list this app
 * keeps (`MATRIX_ACTION_OPTIONS` in `data_loader/bonus_extra.py`) because
 * Codeslinger's `<actiondicepool>` carries no name of its own — the player
 * picks one — so there is nothing in `translations` to look them up in, and
 * the dropdown and the sheet both showed them in English. By the line
 * `docs/i18n.md` draws, a string this app wrote belongs to `ui`.
 *
 * Sources, where there is one: 全力防御 is the glossary's, ファイル編集 /
 * ジャックアウト / マトリックス知覚 / マトリックス検索 are the vendored
 * `ja-jp_data.xml`'s, and 強行アクセス / 素早いハッキング / データスパイク /
 * スレッディング are already used by this app's ココフォリア output. The rest
 * follow the same house style — meaning for concept words, katakana for coined
 * ones — and are the first Japanese this app has had for them.
 */
const ACTION_KEYS: Record<string, MsgKey> = {
  "Brute Force": "action.bruteForce",
  "Check Overwatch Score": "action.checkOverwatch",
  "Control Device": "action.controlDevice",
  "Crack File": "action.crackFile",
  "Crash Program": "action.crashProgram",
  "Data Spike": "action.dataSpike",
  "Disarm Data Bomb": "action.disarmDataBomb",
  "Edit File": "action.editFile",
  "Enter/Exit Host": "action.enterExitHost",
  "Erase Mark": "action.eraseMark",
  "Erase Matrix Signature": "action.eraseSignature",
  "Format Device": "action.formatDevice",
  "Full Matrix Defense": "action.fullMatrixDefense",
  "Hack on the Fly": "action.hackOnTheFly",
  Hide: "action.hide",
  "Invite Mark": "action.inviteMark",
  "Jack Out": "action.jackOut",
  "Jam Signals": "action.jamSignals",
  "Jump Into Rigged Device": "action.jumpIn",
  "Matrix Perception": "action.matrixPerception",
  "Matrix Search": "action.matrixSearch",
  "Reboot Device": "action.rebootDevice",
  "Send Message": "action.sendMessage",
  "Set Data Bomb": "action.setDataBomb",
  Snoop: "action.snoop",
  "Spoof Command": "action.spoofCommand",
  "Switch Interface Mode": "action.switchInterface",
  "Trace Icon": "action.traceIcon",
  // the one non-Matrix action a dice-pool bonus names (a paragon's)
  Threading: "action.threading",
};

/**
 * An action name rendered for the reader. `tr` is the fallback rather than the
 * English name: a player's own typing goes in the same field (the list is not
 * exhaustive and the box takes free text), and so would an action a future
 * data update names.
 */
export function actionLabel(name: string, ui: UiFn, tr: (name: string) => string): string {
  const key = ACTION_KEYS[name];
  return key ? ui(key) : tr(name);
}
