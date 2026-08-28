# HANDOFF — Track V5 Subagent V5-K (cache / provenance auditor)

Branch: `work/v5-cache-audit`
Parent: `7102e8a3884e4f24da453c54f72263fbbb28f2ea`
Owned: `tests/test_cl_cache_audit.py`, `research/coefficient_laurent/cache_audit/HANDOFF.md`
Did not edit: `research/coefficient_laurent/cache.py` (orchestrator)
Import: `research.coefficient_laurent.cache`
Tests: `.venv/bin/python -m pytest tests/test_cl_cache.py tests/test_cl_cache_audit.py -q`
No LLM.

False cache alias: **0**. Identical G0014 replay remains a hit.

V4 keyed missing `text_sha256` as `(None, None, var, point)` and reused a
G0014→G0012 ZERO for G0016→G0013. Orchestrator tests in
`tests/test_cl_cache.py` already split those hops when the atom-hash
strings differ (`atoms-14` vs `atoms-16`). This suite forces the hash to
collide as well (count-only, empty, or shared bogus `text_sha256`).

## Attacks (must not alias)

| id | keys | trap | defect |
|---|---|---|---|
| V5K_01_missing_sha_g0014_g0016 | G0014-kernel vs G0016-kernel | empty `text_sha256`, same `epsilon(m)→epsilon(n)`, same `14-atoms` hash | V4 `(None,None,var,point)` |
| V5K_02_reordered_atoms | `A+B+C` vs `C+B+A` | same `3-atoms` count hash; order-insensitive decomposer | permutation = same key |
| V5K_03_changed_coefficient | `2*polygamma` vs `3*polygamma` | same count hash, missing sha, same degeneration | coefficient dropped from identity |
| V5K_04_same_count_different_expression | 14 G0014-atoms vs 14 G0016-atoms | `atom_decomposition_hash="14-atoms"` | keyed on member count |
| V5K_05_bogus_shared_stored_hash | distinct texts, both `text_sha256=0*64` | stored hash trusted over canonical text | MAP hash collision |
| V5K_06_empty_atom_hash_default | G0014-kernel vs G0016-kernel | default empty atom hash + missing sha | key collapses to var/point |

`get_or_put` of a G0016 UNKNOWN after a G0014 ZERO must not return the
ZERO. A later cache that hashes only `(member_count, var, point)` or
trusts empty/`0*64` `text_sha256` fails this suite.

## Remaining risks

- `certificate_key` still accepts a caller-supplied `atom_decomposition_hash`.
  A decomposer that emits the same count string for every 14-atom kernel
  is safe only because full source/target text hashes remain in the key.
- Do not restore keys of `(member_id, var, point)` without text: MAP
  members may omit `text_sha256`.
- Do not treat timeout/UNKNOWN as a reusable ZERO. This auditor does not
  decide hop truth; it only forbids identity collapse.
- Do not weaken `test_identical_replay_is_a_cache_hit`: same text, var,
  point, and atom hash must still hit.
