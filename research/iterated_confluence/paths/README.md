# Owner: V3-B — one-parameter path enumerator

Enumerate covering paths between existing `G####` members of each frozen
V3 family. Each step imposes exactly one index equality
(`epsilon(a) -> epsilon(b)`).

Evaluation-only. Verdicts stay `UNKNOWN` / `PATH_UNKNOWN`. No LLM.
Does not invent intermediate members.

Output: `PATH_CANDIDATES.json`.

## Public API

```python
from research.iterated_confluence.paths import enumerate_family, enumerate_all, write

fam = enumerate_family(hyp)
blob = enumerate_all()
write()
```

`enumerate_family` returns `family_id`, `paths`, `rejected_multi_parameter`.
Two-parameter generic→triple star edges are rejected with
`reason="not_one_parameter"`. Substitution (`G0005 -> G0009`) is listed
under `substitutions`, not mixed into confluence paths.

## Lattice (5-member families)

Members: generic `True`; pairwise `Eq(m,n)`, `Eq(ell,n)`, `Eq(ell,m)`;
`And` of two equalities.

- generic --{m,n}--> Eq(m,n) --{ell,n}--> And
- generic --{ell,n}--> Eq(ell,n) --{m,n}--> And
- generic --{ell,m}--> Eq(ell,m) --{m,n}--> And

After `Eq(ell, m)` the remaining free coordinate is `Eq(m, n)`.
Incomparable diagonals are not joined. Individual covering edges are
emitted as one-step paths.

## Ranking

`n_steps` ascending, then max source/target op count ascending, then
True→`Eq(m,n)` one-step shape (Track V pair shape) ahead of other ties,
then `path_id` lexicographic. Ranking does not read edge verdicts.
