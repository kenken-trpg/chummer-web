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
