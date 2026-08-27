"""Master-object induction: A_i = O_i[F], gold-free quality."""

from research.representation_invention.master.instantiate import instantiate_operator
from research.representation_invention.master.quality import (
    UNIT_INTERVAL_AXES,
    score_master_hypothesis,
)

__all__ = [
    "score_master_hypothesis",
    "instantiate_operator",
    "UNIT_INTERVAL_AXES",
]
