"""Frozen proposer prompts. Do not tune on TEST."""
from __future__ import annotations

from typing import Any, Optional, Sequence

from research.llm_abstraction.config import FROZEN
from research.llm_abstraction.schema import HYPOTHESIS_TYPES

SYSTEM_PROMPT = """You are NOT a verifier.

You propose speculative mathematical structure from symbolic expressions.
You do not claim exact equivalence.
You do not invent physical interpretation unless it is supplied in the context.
The verifier, not you, decides truth.

Prefer structural hypotheses that explain multiple non-identical expressions.
Avoid introducing arbitrary interpolation, geometry, latent spaces, decoders,
geodesics, or other auxiliary machinery unless the expression structure requires it.
Do not linearly interpolate between two instances (for example z*A+(1-z)*B)
unless the source expression itself is an interpolation.

Every proposal must specify:
1. which expressions it explains;
2. the latent object;
3. how each expression is generated from the latent object;
4. what exact proof obligations would certify the claim.

If no non-trivial shared structure is warranted, abstain.

Return a single JSON object (no markdown fences) with this shape:
{
  "abstain": false,
  "abstain_reason": "",
  "hypotheses": [
    {
      "hypothesis_type": "<one allowed type>",
      "target_members": ["<expr>", "<expr>"],
      "latent_object": "<symbolic template>",
      "parameters": ["<name>", "..."],
      "operators": [{"member": "<expr>", "O": "identity|d/dtheta|permute|specialize"}],
      "instance_maps": [{"member": "<expr>", "theta": {"<param>": "<value>"}}],
      "construction_plan": "<how to instantiate>",
      "required_assumptions": ["<assumption>"],
      "proof_obligations": ["<member> - O[latent] = 0"],
      "rationale": "<structural reason, no physical story unless given>",
      "confidence": 0.0
    }
  ]
}

Allowed hypothesis_type values:
""" + ", ".join(HYPOTHESIS_TYPES) + """

confidence is a number in [0, 1].
Do not emit more than """ + str(FROZEN["n_hypotheses_max"]) + """ hypotheses.
Do not name hidden gold objects.
Do not claim ZERO, proven, or certified.
"""

GENERIC_TASK = (
    "Identify a small number of latent mathematical objects or representation "
    "changes that could explain multiple non-identical structural families. "
    "Do not simplify the full expression. For each hypothesis: identify members; "
    "define the latent object; specify operators/maps; provide a construction "
    "plan; list proof obligations."
)


def _join_context(ctx: Optional[Sequence[str]]) -> str:
    if not ctx:
        return "(none beyond the generic task)"
    return "\n".join(f"- {c}" for c in ctx)


def build_user_prompt(
    *,
    condition: str,
    expression: str,
    symbols: list,
    functions: list,
    assumptions: Optional[Sequence[str]] = None,
    scientific_context: Optional[Sequence[str]] = None,
    basic_summary: Optional[dict] = None,
    packets_text: Optional[str] = None,
    extra_instruction: str = "",
) -> str:
    cond = condition.upper()
    parts = [
        f"CONDITION: {cond}",
        "TASK:",
        GENERIC_TASK,
        "",
        "DECLARED SYMBOLS:",
        repr([s.get("name") if isinstance(s, dict) else s for s in (symbols or [])]),
        "DECLARED FUNCTIONS:",
        repr(list(functions or [])),
        "DECLARED ASSUMPTIONS:",
        repr(list(assumptions or [])),
        "SCIENTIFIC CONTEXT (may be empty; do not invent physics):",
        _join_context(scientific_context),
    ]
    if extra_instruction:
        parts.extend(["", extra_instruction])

    include_full = cond in {"A0", "A1", "A2", "L0", "L1", "L2", "G0", "G1", "G2", "RAW"}
    include_summary = cond in {"A1", "A2", "L1", "L2", "G1", "G2"}
    include_packets = cond in {"A2", "A3", "L2", "L3", "G2", "G3"}
    packets_only = cond in {"A3", "L3", "G3"}

    if include_full and not packets_only:
        parts.extend(["", "RAW EXPRESSION:", expression])
    if include_summary and basic_summary:
        parts.extend(["", "BASIC STRUCTURAL SUMMARY (not an interpretation):",
                      _fmt_summary(basic_summary)])
    if include_packets:
        parts.extend([
            "",
            "STRUCTURAL OBSERVATION PACKETS:",
            "These are relations reported by existing symbolic backends.",
            "They are observations, not scientific names, and not proofs.",
            packets_text or "(no packets)",
        ])
        if packets_only:
            parts.extend([
                "",
                "The full raw expression is intentionally omitted.",
                "Use only the member expressions inside the packets.",
            ])
    parts.extend([
        "",
        "Respond with JSON only.",
    ])
    return "\n".join(parts)


def _fmt_summary(s: dict[str, Any]) -> str:
    keys = (
        "ops", "n_ops", "count_ops", "free_symbols", "functions",
        "n_piecewise", "piecewise", "n_sums", "indexed_names",
        "n_indexed", "n_branches",
    )
    lines = []
    for k in keys:
        if k in s:
            lines.append(f"- {k}: {s[k]}")
    # always dump remaining small scalars
    for k, v in s.items():
        if k in keys:
            continue
        if isinstance(v, (int, float, str, list)) and k != "text":
            if isinstance(v, list) and len(v) > 24:
                v = v[:24] + ["..."]
            lines.append(f"- {k}: {v}")
    return "\n".join(lines) if lines else str({k: s[k] for k in list(s)[:12]})
