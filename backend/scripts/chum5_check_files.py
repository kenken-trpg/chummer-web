#!/usr/bin/env python3
"""Write check files: Chummer's test saves exported by this app, to open in
Chummer itself and compare the karma, nuyen and essence it shows with this
app's (docs/export-verification.md).

Each save named on the command line (the file in ``vendor/chummer-tests``
of that name, else the first whose name contains it) is imported, exported
and written to ``--out`` as ``<prefix>-<name>.chum5``, with that as its alias
too. Chummer runs as a single instance and saves a file again when it is
closed, so a fresh prefix per round keeps a reading from coming off a file
Chummer has rewritten. This app's own figures are printed beside each file.

``--split`` also writes one file per item kind (only that kind's items kept,
plus ``none`` with no items at all): when the whole character disagrees, the
file that disagrees on its own names the kind to look at. Chummer then asks
about the improvements the removed items made ("Orphaned Improvements"),
which is expected for these files only.

    python scripts/chum5_check_files.py BLUE Soma --out ../rt --prefix A
    python scripts/chum5_check_files.py BLUE --out ../rt --prefix B --split
"""

from __future__ import annotations

import argparse
import copy
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.characters import import_character  # noqa: E402
from app.chummer_export import state_to_chum5  # noqa: E402
from app.chummer_import import chum5_to_state  # noqa: E402

_SAVES = Path(__file__).resolve().parents[1] / "vendor" / "chummer-tests"
#: The item lists `--split` empties in turn.
_KINDS = ("cyberwares", "gears", "weapons", "armors", "vehicles")


def _write(root: ET.Element, out: Path, alias: str) -> None:
    node = root.find("alias")
    if node is None:
        node = ET.SubElement(root, "alias")
    node.text = alias
    (out / f"{alias}.chum5").write_bytes(ET.tostring(root, encoding="utf-8", xml_declaration=True))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="+", help="part of a test save's file name")
    ap.add_argument("--out", type=Path, required=True, help="folder Chummer can open the files from")
    ap.add_argument("--prefix", default="C", help="file and alias prefix, new for each round")
    ap.add_argument("--split", action="store_true", help="also one file per item kind")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    for name in args.names:
        saves = sorted(_SAVES.glob("*/*.chum5"))
        path = next((p for p in saves if p.stem == name), None) or next((p for p in saves if name in p.stem), None)
        if path is None:
            print(f"{name}: no test save matches (fetch them with scripts/chum5_reconcile.py first)")
            return 1
        state, _ = chum5_to_state(path.read_bytes())
        character = import_character(state)
        derived = character.derived
        root = ET.fromstring(state_to_chum5(character))
        stem = "".join(c for c in path.stem.split(".")[0] if c.isalnum())
        _write(copy.deepcopy(root), args.out, f"{args.prefix}-{stem}")
        print(
            f"{args.prefix}-{stem}: karma left {derived['karma']['remaining']}, "
            f"nuyen left {derived['nuyen']}, essence {derived.get('essence')}"
        )
        if args.split:
            for keep in ("none", *_KINDS):
                part = copy.deepcopy(root)
                for kind in _KINDS:
                    holder = part.find(kind)
                    if kind != keep and holder is not None:
                        for child in list(holder):
                            holder.remove(child)
                _write(part, args.out, f"{args.prefix}-{stem}-{keep}")
            print(f"  + {len(_KINDS) + 1} files, one per item kind (this app's per-kind prices: --items {name})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
