"""Frozen public-input and provenance contract for read-only SOL replay."""
from __future__ import annotations

import hashlib
from typing import Any

from research.representation_program_search.search import PublicCase

SOL_REPLAY_POLICY_VERSION = "RPSSOLReplayPolicyV1"
SOL_CONTAINER_SCHEMA = "RPSPublicMemberContainerV1"
SOL_REPLAY_BACKEND_PRESET = "relations"
SOL_REPLAY_BACKENDS = ("sympy", "matchpy", "lgg", "egglog")
SOL_REPLAY_STATUS_BACKENDS = (
    "sympy", "matchpy", "egglog", "lgg", "cadabra", "form", "metatheory",
)
SOL_REPLAY_TIMEOUT_SECONDS = 12.0


def replay_member_order(case: PublicCase) -> tuple[str, ...]:
    return tuple(sorted(item.member_id for item in case.members))


def replay_wrapper_functions(case: PublicCase) -> dict[str, str]:
    """Return opaque, deterministic wrappers that cannot reveal member roles."""
    by_id = {item.member_id: item for item in case.members}
    return {
        member_id: (
            f"RPS_SOL_MEMBER_{index:04d}_{by_id[member_id].sha256[:12]}"
        )
        for index, member_id in enumerate(replay_member_order(case), 1)
    }


def structural_container_text(case: PublicCase) -> str:
    """Embed each exact member string as one opaque unary-function argument.

    No member text is normalized, stripped, reserialized, or algebraically
    combined. The surrounding Add is an observation-only container and never
    becomes a scientific expression or verifier input.
    """
    by_id = {item.member_id: item for item in case.members}
    wrappers = replay_wrapper_functions(case)
    members = "\n+\n".join(
        f"{wrappers[member_id]}({by_id[member_id].expression})"
        for member_id in replay_member_order(case)
    )
    return "(\n" + members + "\n)"


def structural_container_metadata(case: PublicCase) -> dict[str, Any]:
    text = structural_container_text(case)
    return {
        "construction": "OPAQUE_UNARY_WRAPPER_ADD",
        "expression_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "member_bytes_embedded": True,
        "member_order": list(replay_member_order(case)),
        "member_sha256": {
            item.member_id: item.sha256
            for item in sorted(case.members, key=lambda item: item.member_id)
        },
        "schema_version": SOL_CONTAINER_SCHEMA,
        "wrapper_functions": replay_wrapper_functions(case),
    }


def replay_policy_payload() -> dict[str, Any]:
    return {
        "backend_preset": SOL_REPLAY_BACKEND_PRESET,
        "requested_backends": list(SOL_REPLAY_BACKENDS),
        "timeout_seconds": SOL_REPLAY_TIMEOUT_SECONDS,
        "version": SOL_REPLAY_POLICY_VERSION,
    }
