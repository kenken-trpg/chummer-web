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
