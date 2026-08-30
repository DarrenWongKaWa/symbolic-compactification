# Representation-search falsifier V1

This directory is an **evaluator-only negative-control suite**. Its six traps
are synthetic attacks on the search and scoring implementation. They are not
scientific case dossiers and may never enter DEV, TEST, CHALLENGE, or any
claim of representation depth.

The suite separates three failure stages:

1. `PRE_VERIFICATION_INELIGIBLE`: an exact reconstruction is screened out as
   tautological or strictly dominated. Its candidate bytes equal the source
   member bytes, so there is no proposed transformation and no verifier step.
2. `COMPILE_FAILURE`: the program/action sequence is structurally ill-typed
   and must not reach the exact verifier.
3. `VERIFIER_NONZERO`: a well-typed-looking program compiles to an equality
   that the engine refutes with an exact residual and rational
   counterexample. Every such equality has a retained session record.

`positive_control/` is the only case permitted to produce `ZERO`. It checks
that the evidence reader recognizes one ordinary certified transformation.
The six traps themselves never receive a `ZERO` promotion.

## Traps

| id | expected gate |
|---|---|
| `tautological-member-memorization` | exact but `TAUTOLOGICAL_PROGRAM` |
| `wrong-hermite-multiplicity` | `COMPILE_FAILURE/HERMITE_NODE_MULTIPLICITY` |
| `false-recurrence` | exact `NONZERO/FALSE_RECURRENCE` |
| `overcomplex-memorizing-master` | exact but `DOMINATED_STATE` |
| `attractive-wrong-basis` | two exact `NONZERO/WRONG_BASIS` obligations |
| `near-correct-divided-difference` | exact `NONZERO/NEAR_CORRECT_DD` |

Run the deterministic checks with:

```bash
python -m research.representation_program_search.falsifier.validate
pytest -q tests/test_rps_search_falsifier.py
```

The adapter in `adapter.py` deliberately has no dependency on M1 code. The
explicit compatibility map relates its Hermite class to M1's implemented
`HERMITE_REPEATED_NODE_REQUIRED` failure prefix. An integration adapter can
later map `RepresentationProgramAdapterV1` into canonical M1 IR; the frozen
expected outcomes and engine receipts remain the oracle.
