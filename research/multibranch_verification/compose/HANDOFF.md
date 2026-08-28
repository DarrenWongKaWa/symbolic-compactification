# HANDOFF — Track V2-D (family composition)

Parent: `4dee916170f0282f8b0e5fee171a8bf4a3934646`
Branch: `work/v2-family-composition`

## What was implemented

Family composition under `research/multibranch_verification/compose/`.
`schema.py` is not edited. The global rule is imported:

```python
from research.multibranch_verification.schema import compose_family_verdict
```

`certify_family(...)` only computes inputs to that rule. Majority vote is
not implemented and cannot produce `FAMILY_ZERO`.

Public API (`from research.multibranch_verification.compose import ...`):

| symbol | role |
|---|---|
| `certify_family` | wrap `compose_family_verdict` with graph / path / multiplicity / latent checks |
| `path_consistency` | two A↝B paths must compose to agreeing operators |
| `compose_operators` | left-to-right name-map composition |
| `operators_agree` | `ZERO` / `NONZERO` / `UNKNOWN` |
| `required_graph_connected` | undirected connectivity of required members |
| `multiplicities_consistent` | positive ints; conflicting claims fail |

`FAMILY_ZERO` iff connected required graph, all required edges ZERO,
recurrence ZERO, path consistency ZERO, multiplicities consistent, latent
compatible. Any required `NONZERO` ⇒ `FAMILY_NONZERO`. Else `FAMILY_UNKNOWN`.

Pairwise ZERO is not `FAMILY_ZERO`: a triangle of ZERO edges whose two
A↝B operator paths disagree is `FAMILY_NONZERO`; 4 ZERO + 1 UNKNOWN is
`FAMILY_UNKNOWN`.

Path consistency: algebraic limit/substitution maps that differ are
`NONZERO`. Opaque or uncomposable operators (including Hermite recurrence
vs a plain limit) are `UNKNOWN`, never ZERO. Vacuous (≤1 path) is ZERO.
Operators compose in a common name basis (no silent push-forward of later
targets, no Guo identities, no `sympy.limit`).

## Tests

`tests/test_mb_compose.py`

Command: `.venv/bin/python -m pytest tests/test_mb_compose.py -q`

## Remaining risks

- Name-map algebra does not prove that a limit exists; edge ZERO is owned
  by V2-B.
- `F[x,x] = lim_{y→x} F[x,y]` is not claimed here (V2-C recurrence).
- `latent_compatible` is a consumed boolean (V2-E). Default matches schema
  (`True`); callers must pass `False` when the latent is not compatible.
- Path enumeration of simple directed paths is capped (`max_path_length=8`);
  truncation fail-closes to UNKNOWN, not ZERO.
- Remaining coalescence edges must be labeled in the original name basis.

## COMMIT SHA

Parent `4dee916170f0282f8b0e5fee171a8bf4a3934646`.
Branch `work/v2-family-composition`.
Message: `Add family composition rules; no majority ZERO.`
