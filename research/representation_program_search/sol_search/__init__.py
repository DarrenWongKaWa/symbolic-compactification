"""S3 frozen-SOL-conditioned deterministic representation search."""

from .authority import (
    SOL_AUTHORITY_MANIFEST_SHA256,
    SOL_AUTHORITY_SOURCE_SHA256,
    authority_manifest,
    validate_local_authority,
)
from .controller import sol_conditioned_search
from .heuristic import SOLPriorityPolicy, route_legal_child
from .model import (
    SOL_ARTIFACT_SCHEMA,
    SOL_AUTHORITY_COMMIT,
    SOL_LAYER,
    SOL_PRIORITY_POLICY_VERSION,
    SOL_ROUTING_UNITS,
    ProjectedSOLRelation,
    SOLContribution,
    SOLProjection,
    SOLRoutingDecision,
    SOLSearchResult,
)
from .projection import load_sol_projection
from .replay import (
    SOLReplayError,
    SOLReplayPolicy,
    SOLReplayResult,
    build_sol_replay_artifact,
)
from .replay_contract import (
    SOL_CONTAINER_SCHEMA,
    SOL_REPLAY_BACKENDS,
    SOL_REPLAY_BACKEND_PRESET,
    SOL_REPLAY_POLICY_VERSION,
    SOL_REPLAY_STATUS_BACKENDS,
    SOL_REPLAY_TIMEOUT_SECONDS,
    replay_policy_payload,
    structural_container_metadata,
    structural_container_text,
)

__all__ = [
    "SOL_ARTIFACT_SCHEMA",
    "SOL_AUTHORITY_COMMIT",
    "SOL_AUTHORITY_MANIFEST_SHA256",
    "SOL_AUTHORITY_SOURCE_SHA256",
    "SOL_LAYER",
    "SOL_PRIORITY_POLICY_VERSION",
    "SOL_ROUTING_UNITS",
    "SOL_CONTAINER_SCHEMA",
    "SOL_REPLAY_BACKENDS",
    "SOL_REPLAY_BACKEND_PRESET",
    "SOL_REPLAY_POLICY_VERSION",
    "SOL_REPLAY_STATUS_BACKENDS",
    "SOL_REPLAY_TIMEOUT_SECONDS",
    "SOLReplayError",
    "SOLReplayPolicy",
    "SOLReplayResult",
    "ProjectedSOLRelation",
    "SOLContribution",
    "SOLPriorityPolicy",
    "SOLProjection",
    "SOLRoutingDecision",
    "SOLSearchResult",
    "authority_manifest",
    "build_sol_replay_artifact",
    "load_sol_projection",
    "route_legal_child",
    "replay_policy_payload",
    "sol_conditioned_search",
    "structural_container_metadata",
    "structural_container_text",
    "validate_local_authority",
]
