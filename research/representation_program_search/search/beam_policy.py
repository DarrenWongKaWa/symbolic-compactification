"""Shared deterministic merge policy for per-parent ranked beam frontiers."""
from __future__ import annotations

BATCHED_BEAM_MERGE_POLICY_VERSION = "RPSPerParentRankMergeV1"
MATCHED_PER_PARENT_BATCH_SIZE = 32
MATCHED_LAYER_BEAM_WIDTH = 32
CROSS_PARENT_PRIORITY_FIELDS = (
    "local_rank",
    "parent_state_hash",
    "child_state_hash",
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
