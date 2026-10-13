import type { Character } from "@/lib/types";

/**
 * Reading and writing one quality's chosen targets.
 *
 * `quality_extras` is a flat map keyed by the quality's id, or by
 * `"<id>:<what>"` for a quality that chooses more than one thing (a spell
 * category *and* a spirit, four attribute slots, a contact). Every control in
 * the panel used to spread the whole map inline to change one key, thirty-odd
 * times over, which is also where a spread that dropped the other keys would
 * hide.
 *
 * `commit` patches the character, which round-trips to the engine; `draft`
 * only sets local state. A free-text box needs both — patching per keystroke
 * would re-render the panel from the server on every letter — so it drafts on
 * change and commits on blur.
 */
export function qualityExtras(
  ch: Character,
  patch: (body: Record<string, unknown>) => void | Promise<void>,
  setCharacter: (next: Character) => void,
) {
  const merged = (key: string, value: string) => ({ ...(ch.quality_extras || {}), [key]: value });
  return {
    read: (key: string) => ch.quality_extras?.[key] || "",
    commit: (key: string, value: string) => patch({ quality_extras: merged(key, value) }),
    draft: (key: string, value: string) =>
      setCharacter({ ...ch, quality_extras: merged(key, value) }),
  };
}

export type QualityExtras = ReturnType<typeof qualityExtras>;
