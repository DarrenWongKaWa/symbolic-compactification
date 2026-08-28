"""Path composition for Track V3.

Composes local edge verdicts into ``PathCertificate.path_verdict``.
PATH_ZERO of one path is not a family verdict. The rule is
``schema.compose_path_verdict``; this module only packages its output.
"""
from __future__ import annotations

from typing import Any, Mapping, Sequence

from research.iterated_confluence.schema import (
    UNKNOWN,
    PathCertificate,
    PathStep,
    compose_path_verdict,
)

_PROVENANCE = "schema.compose_path_verdict"

_STEP_FIELDS = (
    "source",
    "target",
    "variable",
    "target_value",
    "spectator_map",
    "local_kernel_id",
    "old_ops",
    "local_ops",
    "verdict",
    "provenance",
    "relation",
    "obligation_id",
)

StepLike = PathStep | str | Mapping[str, Any]


def _as_path_step(step: StepLike) -> PathStep:
    if isinstance(step, PathStep):
        return step
    if isinstance(step, str):
        return PathStep(source="", target="", verdict=step)
    if isinstance(step, Mapping):
        kwargs = {k: step[k] for k in _STEP_FIELDS if k in step}
        kwargs.setdefault("source", str(step.get("source") or ""))
        kwargs.setdefault("target", str(step.get("target") or ""))
        kwargs.setdefault("verdict", str(step.get("verdict") or UNKNOWN))
        return PathStep(**kwargs)
    raise TypeError(f"unsupported path step: {type(step)!r}")


def _step_verdict(step: StepLike) -> str:
    if isinstance(step, PathStep):
        return str(step.verdict)
    if isinstance(step, str):
        return step
    if isinstance(step, Mapping):
        return str(step.get("verdict") or UNKNOWN)
    raise TypeError(f"unsupported path step: {type(step)!r}")


def compose_path(
    steps: Sequence[StepLike] | None = None,
    path_id: str = "",
    start: str = "",
    end: str = "",
    *,
    provenance: Sequence[str] | None = None,
) -> PathCertificate:
    """Compose one path from local step verdicts.

    ``steps`` may be ``PathStep`` objects or edge-verdict strings
    (``ZERO`` / ``NONZERO`` / ``UNKNOWN``). Empty ``steps`` is
    PATH_UNKNOWN, not PATH_ZERO. Does not certify a family.
    """
    raw = list(steps or [])
    path_steps = [_as_path_step(s) for s in raw]
    path_verdict = compose_path_verdict([_step_verdict(s) for s in raw])
    start_member = start
    end_member = end
    if not start_member and path_steps:
        start_member = path_steps[0].source
    if not end_member and path_steps:
        end_member = path_steps[-1].target
    prov = list(provenance or [])
    if _PROVENANCE not in prov:
        prov.append(_PROVENANCE)
    return PathCertificate(
        path_id=path_id,
        start_member=start_member,
        end_member=end_member,
        steps=path_steps,
        path_verdict=path_verdict,
        provenance=prov,
    )


def compose_paths(paths: Sequence[PathCertificate]) -> list[PathCertificate]:
    """Fill ``path_verdict`` on each certificate from its steps.

    Does not compose a family verdict.
    """
    out: list[PathCertificate] = []
    for path in paths:
        filled = compose_path(
            list(path.steps),
            path_id=path.path_id,
            start=path.start_member,
            end=path.end_member,
            provenance=path.provenance,
        )
        path.steps = filled.steps
        path.path_verdict = filled.path_verdict
        path.provenance = filled.provenance
        if not path.start_member:
            path.start_member = filled.start_member
        if not path.end_member:
            path.end_member = filled.end_member
        out.append(path)
    return out
