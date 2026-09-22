/**
 * Image types a portrait may be. The backend keeps only these as a `data:`
 * URI (`models.clean_portrait`) — the file picker and the upload check use the
 * same list so a picture is refused here rather than silently dropped there.
 */
export const PORTRAIT_TYPES: readonly string[] = [
  "image/png",
  "image/jpeg",
  "image/gif",
  "image/webp",
];

/** How many portraits a character keeps — Chummer's first three mugshots. */
export const MAX_PORTRAITS = 3;

/** Every portrait of `ch`, the main one first. */
export function portraitsOf(ch: { portrait?: string; extra_portraits?: string[] }): string[] {
  return [ch.portrait ?? "", ...(ch.extra_portraits ?? [])].filter(Boolean);
}

/**
 * The patch that stores `pics` (main one first). Both fields always go
 * together, so taking the main one away moves the next one into its place.
 */
export function portraitsPatch(pics: readonly string[]): {
  portrait: string;
  extra_portraits: string[];
} {
  return { portrait: pics[0] ?? "", extra_portraits: pics.slice(1, MAX_PORTRAITS) };
}
