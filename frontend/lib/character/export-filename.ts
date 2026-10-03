/**
 * What a downloaded file is called.
 *
 * Every export used to be `<名前>.<拡張子>`, so a second export of the same
 * character landed as "Ghile Mear (1).chum5" — the browser's numbering, which
 * says nothing about which save is which or which came first. A character is
 * exported repeatedly while it is being built, and the file sits in the
 * downloads folder next to every earlier attempt, so the name has to carry
 * when it was written.
 */

/** `20261003-191230` — local time, because the player reads it against their
 *  own clock, not UTC. Sorts chronologically as text. */
export function exportStamp(at: Date = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, "0");
  const date = `${at.getFullYear()}${pad(at.getMonth() + 1)}${pad(at.getDate())}`;
  const time = `${pad(at.getHours())}${pad(at.getMinutes())}${pad(at.getSeconds())}`;
  return `${date}-${time}`;
}

/**
 * A character name reduced to something a filesystem will take. Windows
 * forbids `\ / : * ? " < > |`, every system dislikes a path separator, and a
 * trailing dot or space is silently dropped on Windows — so the stamp would
 * end up glued to the extension. Control characters are stripped outright.
 *
 * `a.download` is only a hint: the browser sanitises it too, but each one does
 * so differently, and what it hands back is not something we can read. Doing
 * it here is what makes the name predictable.
 */
export function safeStem(name: string): string {
  const cleaned = Array.from(name || "")
    .filter((ch) => !/[\u0000-\u001f\u007f]/.test(ch))
    .join("")
    .replace(/[\\/:*?"<>|]/g, "_")
    .replace(/\s+/g, " ")
    .trim()
    .replace(/[.\s]+$/, "");
  // A name that was nothing but punctuation leaves an empty stem, and a file
  // called ".chum5" is a hidden file with no name on every unix.
  return cleaned || "character";
}

/**
 * The name a download is offered under: `Ghile Mear_20261003-191230.chum5`.
 *
 * `tag` distinguishes two exports that share an extension — the app's own
 * JSON and the Foundry VTT JSON are both `.json`, and told apart only by
 * what is inside them.
 */
export function exportFilename(
  name: string,
  ext: string,
  opts: { tag?: string; at?: Date } = {},
): string {
  const tag = opts.tag ? `-${opts.tag}` : "";
  return `${safeStem(name)}${tag}_${exportStamp(opts.at)}.${ext}`;
}
