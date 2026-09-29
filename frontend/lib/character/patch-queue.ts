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
 * person asked for. Anything else — a different control, a row added or
 * removed, two fields at once — is not that, and is still dropped, which is
 * what this app did to all of them until now.
 */

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
 */
function leafDiffs(a: unknown, b: unknown, limit: number): number {
  if (a === b) return 0;
  if (isRecord(a) && isRecord(b)) {
    const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
    if (keys.size !== Object.keys(a).length || keys.size !== Object.keys(b).length) return limit;
    let n = 0;
    for (const k of keys) {
      n += leafDiffs(a[k], b[k], limit - n);
      if (n >= limit) return limit;
    }
    return n;
  }
  if (Array.isArray(a) && Array.isArray(b)) {
    if (a.length !== b.length) return limit;
    let n = 0;
    for (let i = 0; i < a.length; i++) {
      n += leafDiffs(a[i], b[i], limit - n);
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
 *
 * Two bodies that are identical count too: re-sending is harmless, and a
 * control that fires twice with the same value is not worth a special case.
 */
export function advancesOneLeaf(
  sent: Record<string, unknown>,
  next: Record<string, unknown>,
): boolean {
  return leafDiffs(sent, next, 2) < 2;
}
