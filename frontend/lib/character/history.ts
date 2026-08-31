import { useRef, useState } from "react";
import type { Character } from "@/lib/types";

const MAX_DEPTH = 50;

export type CharacterHistory = {
  /** Counts for enabling/disabling UI controls. */
  counts: { undo: number; redo: number };
  /** Push a pre-change snapshot; clears the redo stack. */
  record: (snapshot: Character) => void;
  /** Drop all history (character switch, fresh load). */
  reset: () => void;
  /** Move one step back: returns the snapshot to restore, or null. */
  stepBack: (current: Character) => Character | null;
  /** Move one step forward: returns the snapshot to restore, or null. */
  stepForward: (current: Character) => Character | null;
};

/**
 * Client-side undo/redo stack for the character editor.
 *
 * Snapshots are full `Character` objects taken just before a patch is sent to
 * the server. Undo/redo replays a snapshot back through the normal patch path so
 * the server recomputes `derived`.
 */
export function useCharacterHistory(): CharacterHistory {
  const undo = useRef<Character[]>([]);
  const redo = useRef<Character[]>([]);
  const [counts, setCounts] = useState({ undo: 0, redo: 0 });

  const sync = () => setCounts({ undo: undo.current.length, redo: redo.current.length });

  return {
    counts,
    record(snapshot) {
      undo.current.push(snapshot);
      if (undo.current.length > MAX_DEPTH) undo.current.shift();
      redo.current = [];
      sync();
    },
    reset() {
      undo.current = [];
      redo.current = [];
      sync();
    },
    stepBack(current) {
      const snap = undo.current.pop();
      if (!snap) return null;
      redo.current.push(current);
      sync();
      return snap;
    },
    stepForward(current) {
      const snap = redo.current.pop();
      if (!snap) return null;
      undo.current.push(current);
      sync();
      return snap;
    },
  };
}
