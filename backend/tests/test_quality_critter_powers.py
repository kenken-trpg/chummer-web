"""The critter powers a quality grants do what their `<bonus>` says.

Chummer creates each power a quality's `<critterpowers>` names at the rating
and pick given there and runs its bonus (AddImprovementCollection.critterpowers,
CritterPower.Create); the one optional power is made at rating 0. Here the
powers were listed on the quality and their bonuses never collected, so a
drake's Hardened Armor was shown and not worn — and, never collected, no
unhandled tag among them could show up in `unimplemented_bonuses` either.
"""

from __future__ import annotations

from app.data_loader import catalog
from app.engine import compute
from app.engine.compute.qualities import _critter_power_sources
from app.engine.constants import quality_optional_power_extra_key
from tests.engine_support import _human, _quality_id


def _derived(*names: str) -> dict:
    return compute(_human("cp", quality_ids=[_quality_id(n) for n in names])).derived


def test_a_drakes_hardened_armor_is_worn_at_its_rating() -> None:
    assert _derived().get("armor") == 0
    assert _derived("Dracoform (Western Drake)")["armor"] == 2  # Hardened Armor 2


def test_the_quality_and_its_power_both_count_as_in_chummer() -> None:
    # Fomoraig carries <armor>1 itself and Armor 1 as a power: Chummer makes
    # two improvements, so does this
    assert _derived("Infected Optional Power: Armor")["armor"] == 1
    assert _derived("Infected: Fomoraig")["armor"] == 2


def test_regeneration_bars_the_ware_grades_it_names() -> None:
    out = _derived("Infected Optional Power: Regeneration")
    assert "Alphaware" in out["disabled_cyberware_grades"]


def test_the_optional_power_counts_only_once_picked() -> None:
    q = {
        "id": "q1",
        "critter_power_effects": [
            {
                "label": "Armor",
                "optional": False,
                "rating": "2",
                "bonus": [{"tag": "armor", "value": "Rating"}],
            },
            {
                "label": "Immunity (Toxins)",
                "optional": True,
                "rating": "",
                "bonus": [{"tag": "selecttext"}],
            },
        ],
    }
    assert _critter_power_sources(q, {}) == [("Armor", [{"tag": "armor", "value": "2"}])]
    picked = _critter_power_sources(q, {quality_optional_power_extra_key("q1"): "Immunity (Toxins)"})
    assert [label for label, _ in picked] == ["Armor", "Immunity (Toxins)"]


def test_every_power_granting_quality_computes_with_nothing_left_unhandled() -> None:
    granting = [q for q in catalog()["qualities"] if q.get("critter_power_effects")]
    assert len(granting) > 50  # Infected, Dracoform, Free Insect Spirit
    for q in granting:
        optional = [e["label"] for e in q["critter_power_effects"] if e["optional"]]
        extras = {quality_optional_power_extra_key(q["id"]): optional[0]} if optional else {}
        out = compute(_human("cp", quality_ids=[q["id"]], quality_extras=extras)).derived
        assert not out.get("unimplemented_bonuses"), q["name"]
