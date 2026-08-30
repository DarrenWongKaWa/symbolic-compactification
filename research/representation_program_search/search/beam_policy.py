"""Shared deterministic merge policy for per-parent ranked beam frontiers."""
from __future__ import annotations

BATCHED_BEAM_MERGE_POLICY_VERSION = "RPSPerParentRankMergeV1"
BANDED_BATCHED_BEAM_MERGE_POLICY_VERSION = "RPSFeedbackBandPerParentRankMergeV1"
MATCHED_PER_PARENT_BATCH_SIZE = 32
MATCHED_LAYER_BEAM_WIDTH = 32
CROSS_PARENT_PRIORITY_FIELDS = (
    "local_rank",
    "parent_state_hash",
    "child_state_hash",
)
BANDED_CROSS_PARENT_PRIORITY_FIELDS = (
    "feedback_priority_band",
    *CROSS_PARENT_PRIORITY_FIELDS,
)


def cross_parent_rank_key(
    local_rank: int,
    parent_state_hash: str,
    child_state_hash: str,
) -> tuple[int, str, str]:
    """Return the one frozen S4/S5/matched-S2 cross-parent priority key."""
    if (
        not isinstance(local_rank, int)
        or isinstance(local_rank, bool)
        or local_rank < 0
    ):
        raise ValueError("BATCHED_BEAM_LOCAL_RANK_INVALID")
    if not parent_state_hash or not child_state_hash:
        raise ValueError("BATCHED_BEAM_STATE_HASH_INVALID")
    return (local_rank, parent_state_hash, child_state_hash)


def banded_cross_parent_rank_key(
    feedback_priority_band: int,
    local_rank: int,
    parent_state_hash: str,
    child_state_hash: str,
) -> tuple[int, int, str, str]:
    """Prefix the shared merge key with S6's exact feedback priority band."""
    if (
        not isinstance(feedback_priority_band, int)
        or isinstance(feedback_priority_band, bool)
        or feedback_priority_band < 0
    ):
        raise ValueError("BATCHED_BEAM_FEEDBACK_BAND_INVALID")
    return (
        feedback_priority_band,
        *cross_parent_rank_key(local_rank, parent_state_hash, child_state_hash),
    )
