"""P1 prompts. Same scientific rules as P0; members must be catalog IDs."""

SYSTEM_PROMPT = """You are NOT a verifier.

You propose grounded mathematical representations.
You do not claim exact equivalence.
You do not invent physical names (no Phi_Gamma, Hermite, PRB).
The verifier decides ZERO / NONZERO / UNKNOWN.

A representation hypothesis is incomplete without source instances.
You MUST identify members by source_node_id from the provided catalog.

Forbidden member names: S1_True, S1_Eq_mn, branch_generic, O2(n,m),
or any alias that is not a catalog id (G0001, G0002, ...).

Prefer hypotheses that explain multiple non-identical catalog members
via one latent object and explicit operators (identity, specialize,
permute, d/dtheta, limit / confluence).

Return JSON only:
{
  "abstain": false,
  "abstain_reason": "",
  "hypotheses": [
    {
      "representation_type": "confluent_representation|divided_difference|derivative_family|symmetry_invariant|repeated_kernel|parameterized_family|other_structured",
      "latent_object": "<template or F(z)=...>",
      "generic_member": "Gxxxx",
      "degenerate_member": "Gyyyy",
      "limit_variable": "epsilon(m) -> epsilon(n) or empty",
      "member_maps": [
        {
          "source_node_id": "Gxxxx",
          "role": "generic|degenerate|instance",
          "source_fingerprint": {
            "functions": ["h1","h2"],
            "indices": ["m","n"],
            "branch_condition": "True"
          }
        }
      ],
      "operators": [{"member": "Gxxxx", "O": "identity|limit|specialize|permute|d/dtheta"}],
      "proof_obligations": ["limit(Gxxxx, epsilon(m), epsilon(n)) == Gyyyy"],
      "required_assumptions": [],
      "rationale": "<structural, not physical>",
      "confidence": 0.0
    }
  ]
}
"""


def build_p1_user_prompt(
    *,
    expression: str,
    catalog_text: str,
    packets_text: str = "",
    scientific_context: list | None = None,
    symbols: list | None = None,
    functions: list | None = None,
) -> str:
    ctx = "\n".join(f"- {c}" for c in (scientific_context or [])) or "(none)"
    parts = [
        "CONDITION: P1_GROUNDED (same SOL packets as A2; members must be catalog IDs)",
        "TASK: Propose grounded representation hypotheses for non-identical families.",
        "Do not simplify the full expression.",
        "",
        "DECLARED SYMBOLS:",
        repr([s.get("name") if isinstance(s, dict) else s for s in (symbols or [])]),
        "DECLARED FUNCTIONS:",
        repr(list(functions or [])),
        "SCIENTIFIC CONTEXT:",
        ctx,
        "",
        catalog_text,
        "",
        "RAW EXPRESSION:",
        expression,
    ]
    if packets_text:
        parts.extend([
            "",
            "STRUCTURAL OBSERVATION PACKETS (frozen SOL; observation only):",
            packets_text,
        ])
    parts.append("\nRespond with JSON only. Every source_node_id must be in the catalog.")
    return "\n".join(parts)
