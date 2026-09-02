"""Guard for the improvements/nodes/ domain split: every tag the pipeline
claims to implement must be handled by some domain module, even the ones no
character-level test exercises.
"""

from app.improvements import apply_bonus_nodes, empty_effects
from app.improvements._common import IMPLEMENTED


def test_every_implemented_tag_has_a_handler() -> None:
    effects = empty_effects()
    nodes = [{"tag": tag} for tag in sorted(IMPLEMENTED)]
    apply_bonus_nodes(nodes, effects, "guard")
    unhandled = sorted({row["tag"] for row in effects["unimplemented"]})
    assert unhandled == [], f"IMPLEMENTED tags with no domain handler: {unhandled}"


def test_weaponcategorydice_accepts_both_upstream_shapes() -> None:
    # legacy: <weaponcategorydice><category><name>Bows</name><value>1</value></category>
    legacy = empty_effects()
    apply_bonus_nodes([{"tag": "weaponcategorydice", "nested": {"category": ["Bows", "1"]}}], legacy, "legacy")
    assert legacy["weapon_category_dice"] == [{"category": "Bows", "dice": 1, "source": "legacy"}]

    # current: <weaponcategorydice><name>Bows</name><bonus>1</bonus></weaponcategorydice>
    current = empty_effects()
    apply_bonus_nodes([{"tag": "weaponcategorydice", "fields": {"name": "Bows", "bonus": "1"}}], current, "current")
    assert current["weapon_category_dice"] == [{"category": "Bows", "dice": 1, "source": "current"}]
