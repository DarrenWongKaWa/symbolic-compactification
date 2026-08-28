# HANDOFF — Track V2 Subagent V2-E (latent-F consistency)

Parent: `4dee916170f0282f8b0e5fee171a8bf4a3934646`
Branch: `work/v2-latent-consistency`

Commit message: `Add latent-F consistency checks (not discovery).`

## Owned

- `research/multibranch_verification/latent/**`
- `tests/test_mb_latent.py`

Did not edit `schema.py`, frozen run JSON, `FROZEN_INPUTS_V2.json`, or Guo catalogs.
Did not construct Guo gold masters. No LLM.

## API

```
latent_compatible(hyp | fields) -> True | False | UNKNOWN
check_latent_consistency(...) -> LatentConsistency
as_bool(verdict) -> bool
```

Fields used: `latent_object`, `operators`, `member_roles`, and optional
`latent_variables`, `nodes`, `member_ids`, `representation_type`.

This is consistency of a *claimed* F with operators and roles. It does not
invent F, instantiate catalog members, run `sympy.limit`, or certify ZERO.

`UNKNOWN` is fail-closed. The string is truthy in Python; callers must use
`as_bool` before `compose_family_verdict`.

## Checks

| check | False when | UNKNOWN when |
|---|---|---|
| argument compatibility | operator var / substitution not in F args or nodes; perm arity; d/dn of polygamma order | missing F args; kind `other`; missing analytic var on a multi-arg F |
| derivative order | order &lt; 1; Hermite order ≠ multiplicity−1 | unparsed order |
| special-function head | polygamma vs gamma recurrence; algebraic F vs polygamma op head; Φ_Γ / L4–L7 | unparsed F with derivative/DD |
| shared vars | operator vars disjoint from latent vars | no latent vars; kind `other` |
| multiplicity | Hermite mult &lt; 2; coincident Newton as repeated; repeated without coalescence/DD | unparsed multiplicity |
| recurrence compatibility | recurrence on a non-argument; `recurrence_family` without shift | missing var/delta |
| member roles | generic/degenerate swap; repeated identity; unknown role/kind | missing roles |

Empty `latent_object` or empty operators → `UNKNOWN`. Catalog pointers such as
`F(m,n,ell)=G0016 (...)` are matched on the signature only; G0016 is not loaded.

## Tests

```
.venv/bin/python -m pytest tests/test_mb_latent.py -q
```

## Remaining risks

- Signature matching treats `epsilon(m)` as compatible with latent index `m`.
  That is name-level, not a proof that the node is `epsilon(m)`.
- Unparsed prose F with only identity/limit operators can be True on the
  signature. That is not a family ZERO.
- Special-function family grouping (polygamma vs gamma vs other) is lexical
  plus a short parse. It does not verify polygamma fdiff identities (Track V5).
- `kind=other` is always UNKNOWN, never True.
- Does not bind G#### texts or discharge reconstruction `A_i = O_i[F]`.

## Out of scope

Did not edit `schema.py`, `freeze_v2.py`, `FROZEN_INPUTS_V2.json`,
`research/representation_invention/llm/runs/`, or SOL.
