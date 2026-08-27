"""P2/P3/P4 prompts. V2 contract types only; no gold names."""
from __future__ import annotations

from typing import Optional, Sequence

from research.llm_abstraction.config import FROZEN
from research.representation_invention.schema import (
    MEMBER_ROLES,
    OBLIGATION_KINDS,
    OPERATOR_KINDS,
    REPRESENTATION_TYPES,
)

SYSTEM_PROMPT = """You are NOT a verifier.

You propose grounded mathematical representation hypotheses.
You do not claim exact equivalence.
You do not invent physical names or hidden gold objects.
The verifier, not you, decides ZERO / NONZERO / UNKNOWN.
Do not claim ZERO, proven, certified, or exact identity.

A representation hypothesis is incomplete without source instances.
You MUST identify members by catalog ids of the form G0001, G0002, ... (four digits).
Forbidden member names: S1_True, S1_Eq_mn, branch_generic, generic_branch, O2(n,m),
or any alias that is not a catalog id.

Every hypothesis MUST include these RepresentationHypothesisV2 fields:
- representation_type
- member_ids (nonempty list of catalog G#### ids)
- member_roles (map from those ids)
- latent_object (explicit latent F or template; nonempty)
- latent_variables
- nodes (name, expression, multiplicity)
- operators (member_id, kind, args) that generate each member from the latent object
- instance_maps
- reconstruction_rule (how members are recovered: A_i = O_i[F])
- required_assumptions
- proof_obligations (kind, member_ids, expected relation)
- scientific_rationale (structural, not physical)
- confidence in [0, 1]

Allowed representation_type values:
""" + ", ".join(REPRESENTATION_TYPES) + """

Allowed member_roles values:
""" + ", ".join(MEMBER_ROLES) + """

Allowed operator kind values:
""" + ", ".join(OPERATOR_KINDS) + """

Allowed proof_obligation kind values:
""" + ", ".join(OBLIGATION_KINDS) + """

Prefer hypotheses that explain multiple non-identical catalog members
via one latent object and explicit operators.

If no non-trivial shared structure is warranted, abstain.

Return a single JSON object (no markdown fences) with this shape:
{
  "abstain": false,
  "abstain_reason": "",
  "hypotheses": [
    {
      "representation_type": "<one allowed type>",
      "member_ids": ["Gxxxx", "Gyyyy"],
      "member_roles": {"Gxxxx": "generic", "Gyyyy": "degenerate"},
      "latent_object": "<F(z)=... or template>",
      "latent_variables": ["z"],
      "nodes": [{"name": "x", "expression": "<expr>", "multiplicity": 1}],
      "operators": [{"member_id": "Gxxxx", "kind": "<allowed kind>", "args": {}}],
      "instance_maps": {"Gxxxx": {"theta": {}}},
      "reconstruction_rule": "<how A_i = O_i[F]>",
      "required_assumptions": [],
      "proof_obligations": [
        {
          "kind": "<allowed obligation kind>",
          "member_ids": ["Gxxxx"],
          "operator": "<kind>",
          "expected": "member == O[F]"
        }
      ],
      "scientific_rationale": "<structural, not physical>",
      "confidence": 0.0
    }
  ]
}

Do not emit more than """ + str(FROZEN["n_hypotheses_max"]) + """ hypotheses.
Do not name hidden gold objects.
Do not claim ZERO, proven, or certified.
"""


def _join_context(ctx: Optional[Sequence[str]]) -> str:
    if not ctx:
        return "(none)"
    return "\n".join(f"- {c}" for c in ctx)


def condition_label(condition: str) -> str:
    cond = (condition or "P2").upper()
    if cond == "P3":
        return "P3_RAW (catalog + raw expression; no SOL packets)"
    if cond == "P4":
        return "P4_SOL (catalog + raw expression + SOL packets)"
    return "P2_GROUNDED (catalog + raw expression + SOL packets; full V2 schema)"


def include_sol_packets(condition: str) -> bool:
    """P3 is RAW. P2 (default) and P4 include SOL packets."""
    return (condition or "P2").upper() in {"P2", "P4"}


def build_p2_user_prompt(
    *,
    condition: str,
    expression: str,
    catalog_text: str,
    packets_text: str = "",
    scientific_context: Optional[Sequence[str]] = None,
    symbols: Optional[list] = None,
    functions: Optional[list] = None,
) -> str:
    cond = (condition or "P2").upper()
    parts = [
        f"CONDITION: {condition_label(cond)}",
        "TASK: Propose grounded RepresentationHypothesisV2 objects for non-identical families.",
        "Do not simplify the full expression.",
        "Cite only catalog ids (G####). Do not invent aliases.",
        "",
        "DECLARED SYMBOLS:",
        repr([s.get("name") if isinstance(s, dict) else s for s in (symbols or [])]),
        "DECLARED FUNCTIONS:",
        repr(list(functions or [])),
        "SCIENTIFIC CONTEXT (may be empty; do not invent physics):",
        _join_context(scientific_context),
        "",
        catalog_text,
        "",
        "RAW EXPRESSION:",
        expression or "(omitted)",
    ]
    if include_sol_packets(cond) and packets_text:
        parts.extend([
            "",
            "STRUCTURAL OBSERVATION PACKETS (frozen SOL; observation only):",
            "These are relations reported by existing symbolic backends.",
            "They are observations, not scientific names, and not proofs.",
            packets_text,
        ])
    parts.append(
        "\nRespond with JSON only. Every member_id must be a catalog G#### id."
    )
    return "\n".join(parts)
