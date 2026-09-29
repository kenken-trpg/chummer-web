#!/usr/bin/env python3
"""Check the .chum5 import against the saves Chummer itself wrote.

Chummer ships real characters in ``Chummer.Tests/TestFiles``. Each is run
through ``chum5_to_state`` -> ``import_character`` and compared with what the
save already says, so the answer comes from Chummer rather than from this
app's own export (a round trip passes when both sides share a mistake).

For a character still in creation (``<created>False``), ``<karma>`` and
``<nuyen>`` are what Chummer computed as *left*: the one place a save states
the result of the whole build. A mismatch there means an item, a price or a
rule differs, without having to find which one first. In career mode the same
elements are the running balance, which the import meets by construction: the
adjustment it needed (`karma_adjust` / `nuyen_adjust` — rent, purchases at
their own prices, or a price this app gets wrong) is listed instead, with
what the save's own expense log spent beside it.

Two limits on that. The test saves were written by Chummer 5.18x-5.202, which
kept the creation remainder there; current Chummer only sets `<nuyen>` when
creation is finished, so a newer save says nothing about it. And a character
over budget is saved with `0`, not the deficit: when the save says 0 and this
app is below zero as well, both agree the build is overspent — marked `over`
and left out of the mismatches, since by how much cannot be told.

``--locate NAME`` narrows one save's nuyen gap to the pieces that disagree:
the save's own price for every item beside this app's, and then the arithmetic
that says what each bucket would have to be if all the others were right. A
bucket whose every item matches the save cannot be the one, which usually
leaves a single candidate. Lifestyles are the common answer, because a save
records no lifestyle total to check against.

A save stores the karma it paid for a quality, not a reference to the price
list, so a save written against an older `qualities.xml` states a price this
app will never reproduce — the difference lands in the karma left. `-v` lists
those qualities, and a row whose whole karma gap is exactly that is marked
`qdrift`: Miko's single point is `Functional Tail (Prehensile)`, saved at 7
where the catalogue now says 6. Same for `College Education` (saved 4, now 2).

The same drift happens to gear: a save records each item's own cost, so
`Ghile Mear`'s whole 2,000 nuyen gap is `Reakt`, saved at 75,000 where the
catalogue now says 73,000. A row whose nuyen gap is exactly that is marked
`gdrift`, and `-v` lists the items.

Lifestyles are where `--locate` points most often, and the trail ends in the
saves rather than in this app. Chummer 5.202 did not compute these the way its
own current source does (`Lifestyle.CostPreSplit`, which this app follows):
`Ocelot2.0` needs 605 where every documented order of operations gives 600 or
621, and `Harmony` and `Ushi Resub` carry *byte-identical* lifestyles — Low,
Standard, `Cramped`, a Grid Subscription — yet one agrees with this app's 1,800
and the other wants 2,000. One configuration, two answers, so the difference
cannot be a rule either side is applying consistently. Matching it would mean
reproducing a version's arithmetic against its own documentation, and these
saves are the only thing that would confirm it. Left alone deliberately, and
recorded here so the next reader does not spend the afternoon on it again.

One thing did come out of that hunt: only `Street` defines `costforarea` /
`costforcomforts` / `costforsecurity` in `lifestyles.xml`, so for every other
lifestyle this app raises comforts at no charge while the saves record 50
apiece. Chummer keeps the saved value (its legacy sweep only overwrites the
field when the data file has one), which is worth knowing before trusting a
lifestyle line here.

A build over the 25 karma of negative qualities is marked `negcap`. Chummer's
default settings refund all of it and call the build invalid, which is what
this app does; the 5.202 saves stored the remainder as if the refund stopped
at 25, so their karma differs by the excess (Barrett by 53, Blindfire by 15).
That stop is the `ExceedNegativeQualities` + `ExceedNegativeQualitiesNoBonus`
house rule (`GetNegativeQualityKarmaAsync`): turned on here, it gives six of the
eight saves' karma to the point. A save does not record either flag, so the
import cannot tell a table that used it from a build that is simply over;
guessing from the karma left would also catch saves off for other reasons.
Left as Chummer's defaults judge it.

`prime`'s 13 karma is its settings, not its build. It was saved under a
5.202 Prime Runner that gave 35 build karma and 6 contact points per Charisma
(`<buildkarma>` / `<contactmultiplier>` in the save); today's `settings.xml`
Prime Runner gives neither, and current Chummer no longer reads those two
fields, so it opens the character at 25 and x3 too — 10 + 3 short, as here.

`Ocelot2.0`'s power points over (6 / 5) is the same kind of leftover. The
5.202 save carries an `AdeptPowerPoints` +1 improvement from its Cat mentor
spirit, which no data file grants — neither the Cat's `<specificpower>`
(free Light Body levels, which this app does apply) nor anything else in
today's `mentors.xml`. Chummer keeps saved improvements as they are on load,
so it still counts that point; worked out from the data, MAG 5 is the limit.

The files are fetched once into ``vendor/chummer-tests/`` (gitignored), at the
same chummer5a ref as the game data::

    python scripts/chum5_reconcile.py             # table + summary
    python scripts/chum5_reconcile.py -v          # + each file's warnings / errors
    python scripts/chum5_reconcile.py --dir DIR   # other saves instead
    python scripts/chum5_reconcile.py --roundtrip # + export / re-import check
    python scripts/chum5_reconcile.py --items Mittens   # one save, item by item
    python scripts/chum5_reconcile.py --fidelity  # export vs. the save Chummer wrote

`--roundtrip` writes each save back out and reads it again: what it holds
(gear by bucket, ware, vehicle mods — with whether each sits in a parent) and
what it spent must come back the same. It catches what an import reads but the
export has nowhere to write.

`--fidelity` answers the question `--roundtrip` cannot. Reading the export
back with this app's own importer is blind by construction to anything
Chummer needs and this app does not: a field neither side reads comes back
unchanged because neither side looked, and the round trip calls that a pass.
Chummer is the other reader of these files, and the only statement of what it
expects is the save it wrote — so this compares the original against the
export, field by field, over the character's own header (who they are, what
they were built with, what the build was allowed to spend), plus the two
things Chummer keeps exactly one of and loads field by field: the tradition
and the mentor spirit. Everything else a save holds is a list this app
rebuilds from its own catalogue, which is supposed to differ.

It fails on a field *both* sides state with different text, and on one
Chummer states and reads back that the export leaves out. A field Chummer
writes and never reads back — an attribute's `totalvalue`, recomputed on load
— is named in `_ACCEPTED_DROPS` with the reason, and printed rather than
counted against the export. Nothing else is: a field this app has not thought
about fails the run, which is what makes this a gate (CI's `fidelity` job)
rather than a reading to work down.

`--items` lists what this app charges for each piece of one save (the first
file whose name contains the text), to set beside the save's own `<cost>`
expressions when a nuyen total disagrees.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.reconcile.cli import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main(__doc__))
