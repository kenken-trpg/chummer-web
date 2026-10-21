/**
 * Whether a patch that arrived while another was in flight can be sent after
 * it, instead of being dropped.
 *
 * The editor sends one patch at a time: `api.patch` applies the body to the
 * character as *stored*, so two in parallel would race. What it did with an
 * edit that arrived during that window was drop it silently — and the window
 * is not small. Measured against the dev stack on localhost, with an empty
 * character (the most favourable case there is), ten changes 30 ms apart
 * reached the server seven times, and at 50 ms six. The control that loses
 * them most is a number input, whose `value` comes from the character, so a
 * dropped change does not sit there unsaved: it springs back.
 *
 * Queueing them instead is not simply better, because the bodies are not
 * deltas. A component builds the whole field from the character it can see —
 * `{ attributes: { ...ch.attributes, BOD: 3 } }` — so a body composed against
 * a character that has since moved on would put the old value of everything
 * else back. Dropping loses the second edit; queueing blindly would undo the
 * first.
 *
 * What makes it safe is a narrower question than "can these be merged":
 *
 *   is the second body the first one with a single leaf moved on?
 *
 * That is what holding a key down produces — the same control, one step
 * further — and there the stale base cannot do any harm, because the two
 * bodies agree everywhere except the one value the later one means to set.
 * Sending the later body after the earlier has landed leaves exactly what the
 * person asked for.
 *
 * There is a second shape that is safe, for a different reason. Two bodies
 * that name no field in common cannot undo each other at all: a body sets the
 * keys it carries and leaves the rest of the stored character alone, so
 * `{ career: true }` sent after `{ name: … }` has landed keeps the name. The
 * stale base is irrelevant because nothing in the later body was composed
 * from what the earlier one changed. This is the case the editor was losing
 * most visibly — rename a character, then press 作成完了（キャリア）, and the
 * switch did nothing and said nothing.
 *
 * "One leaf" is not quite enough on its own, though. Two *adds* to a list
 * built from the same stale list differ in one place too — ticking two
 * rulebooks quickly gave `[SR5, RF]` then `[SR5, DTR]`, and holding the second
 * as "one step on" unticked RF. What tells them apart from a dropdown picked
 * twice is the character as saved: a value moved on leaves the list as long
 * as it was, while an add or a remove does not. So a list whose length differs
 * from the saved one is never one step on.
 *
 * Anything else — the same field composed twice against different characters,
 * a row added or removed — is still dropped.
 *
 * A control that cannot afford either outcome sends an `Updater` instead: a
 * function the editor calls with the character as last saved, just before it
 * sends the body. Nothing in that body is stale, so it always waits its turn.
 * Ticking two rulebooks in a row is the case that needs it — the second tick,
 * built from the list the first had not reached yet, differs from the first
 * in one element, passes for "one step on", and used to untick the first.
 */

import type { Character } from "@/lib/types";

/** What `api.patch` sends: the top-level fields it replaces. */
export type PatchBody = Record<string, unknown>;

/** A body composed from the character as saved at the moment it is sent. */
export type Updater = (saved: Character) => PatchBody;

/** What the editor's `patch` takes. */
export type PatchInput = PatchBody | Updater;

/** A plain `{}` object, as opposed to an array or a primitive. */
function isRecord(v: unknown): v is Record<string, unknown> {
  return typeof v === "object" && v !== null && !Array.isArray(v);
}

/**
 * Count the leaves at which `a` and `b` differ, giving up at `limit`.
 *
 * Returns `limit` for any difference in *shape* — a key one side does not
 * have, an array of another length, an object where the other has a list.
 * A shape change is a different edit (a row added, a control that appeared),
 * never the same one a step on, so it never needs to be counted precisely.
 *
 * `saved` is the same place in the character as saved, walked alongside: a
 * list that differs in length from it was added to or taken from, by both.
 */
function leafDiffs(a: unknown, b: unknown, saved: unknown, limit: number): number {
  if (a === b) return 0;
  if (isRecord(a) && isRecord(b)) {
    const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
    if (keys.size !== Object.keys(a).length || keys.size !== Object.keys(b).length) return limit;
    const below = isRecord(saved) ? saved : {};
    let n = 0;
    for (const k of keys) {
      n += leafDiffs(a[k], b[k], below[k], limit - n);
      if (n >= limit) return limit;
    }
    return n;
  }
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return limit;
    // an unset list saves as nothing, which a first add also lengthens
    if (a.length !== (Array.isArray(saved) ? saved.length : 0)) return limit;
    let n = 0;
    for (let i = 0; i < a.length; i++) {
      n += leafDiffs(a[i], b[i], (saved as unknown[])[i], limit - n);
      if (n >= limit) return limit;
    }
    return n;
  }
  // A value that changed kind — a string where the other has a list, a list
  // where the other has an object — is a shape change like the ones above,
  // not one value moved on.
  const container = (v: unknown) => typeof v === "object" && v !== null;
  if (container(a) || container(b)) return limit;
  // Two primitives that differ: this is the leaf, and there is nothing below
  // it to look at.
  return 1;
}

/**
 * Whether `next` is `sent` with exactly one leaf changed — the same control,
 * one step on — so that sending `next` once `sent` has landed is right.
 * `saved` is the character both were composed against, as saved.
 *
 * Two bodies that are identical count too: re-sending is harmless, and a
 * control that fires twice with the same value is not worth a special case.
 */
export function advancesOneLeaf(
  sent: Record<string, unknown>,
  next: Record<string, unknown>,
  saved: unknown,
): boolean {
  return leafDiffs(sent, next, saved, 2) < 2;
}

/**
 * Whether `sent` and `next` name no field in common, so that `next` applied
 * after `sent` has landed leaves both edits standing.
 *
 * Top level only, which is the level `api.patch` replaces: two bodies that
 * both carry `attributes` overlap even if they move different ones, because
 * each was built from the whole attribute block as its author saw it.
 */
export function disjointKeys(
  sent: Record<string, unknown>,
  next: Record<string, unknown>,
): boolean {
  const keys = Object.keys(next);
  if (!keys.length) return false;
  return !keys.some((k) => k in sent);
}
