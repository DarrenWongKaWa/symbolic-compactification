# Owner: Subagent C — Experimental obligation IR / compiler

New experimental language under this package.
Do **not** edit `research/obligation_ir/schema.py` or historical verifier
semantics.

Kinds: EQUALITY, SUBSTITUTION, PERMUTATION, DERIVATIVE, LIMIT,
NEWTON_DD, HERMITE_DD, CONFLUENCE, RECURRENCE, MASTER_INSTANCE,
BASIS_RECONSTRUCTION.

`COMPILE_FAILURE` ≠ `UNKNOWN`. Adversarial mutations must not false-ZERO.

Every obligation carries member ids, expressions, variables, assumptions,
operator, expected relation, provenance.
