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

__all__ = [
    "SOL_ARTIFACT_SCHEMA",
    "SOL_AUTHORITY_COMMIT",
    "SOL_AUTHORITY_MANIFEST_SHA256",
    "SOL_AUTHORITY_SOURCE_SHA256",
    "SOL_LAYER",
    "SOL_PRIORITY_POLICY_VERSION",
    "SOL_ROUTING_UNITS",
    "ProjectedSOLRelation",
    "SOLContribution",
    "SOLPriorityPolicy",
    "SOLProjection",
    "SOLRoutingDecision",
    "SOLSearchResult",
    "authority_manifest",
    "load_sol_projection",
    "route_legal_child",
    "sol_conditioned_search",
    "validate_local_authority",
]
