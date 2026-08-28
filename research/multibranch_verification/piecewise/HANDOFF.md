# HANDOFF — Track V2 Subagent V2-F (piecewise family normalizer)

Parent: `4dee916170f0282f8b0e5fee171a8bf4a3934646`
Branch: `work/v2-piecewise-normalizer`

Commit message: `Normalize Piecewise families without inferring confluence.`

## Owned

- `research/multibranch_verification/piecewise/**`
- `tests/test_mb_piecewise.py`

Did not edit `schema.py`, `FROZEN_INPUTS_V2.json`, frozen run JSON, or
`api.py`. No LLM. No Guo gold identities.

## What was implemented

`normalize_piecewise_family(members)` assigns roles from **conditions
only** and reports a common AppliedUndef spectator only when it exactly
divides every member.

| condition | role |
|---|---|
| `True` | `generic` |
| pairwise `Eq` of two index symbols | `diagonal` |
| `And`/`Eq` involving three or more index symbols | `higher-degeneracy` |
| `Ne`, inequalities, unparsed, non-symbol sides | `unknown` |

Spectator path:

1. explicit `Mul` args that are `AppliedUndef`
2. else `factor._peel_applied_undef` when `count_ops ≤ 80`
3. n-way intersection; reconstruction `S * local = member`
4. two-member families must agree with `split_multiplicative` on the
   AppliedUndef part

Units and polynomial-only gcds are not spectators. Branches are never
merged. The payload always has `collapsed=False` and
`confluence_inferred=False`. It does not emit `FAMILY_ZERO`, limit
edges, or a reconstruction rule.

## Tests

`tests/test_mb_piecewise.py`

Command: `.venv/bin/python -m pytest tests/test_mb_piecewise.py -q`
Result: **20 passed**

## Remaining risks

- Roles are syntactic. `Eq(m, n+1)`, `Or`, and `Eq(epsilon(m), epsilon(n))`
  stay `unknown`; they are not guessed as diagonals.
- `Symbol('m', real=True)` vs `Symbol('m')` in AppliedUndef args will not
  match; spectator certification fails closed.
- Guo-scale kernels are not peeled with `cancel` (`ops` cap 80). Explicit
  trailing `h1*h1*h1` factors still extract if the member is already a
  `Mul`. Frozen V2 members ship `text_sha256` only, so freeze payloads
  certify roles and not a spectator.
- A leading `True` branch makes SymPy's `Piecewise` constructor collapse
  to that expr; pass the member list (or keep `True` last) to preserve
  branches.
- This is not a confluence engine. Diagonal / higher-degeneracy labels
  do not mean the branch is a regularized limit of the generic member.
