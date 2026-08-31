# E9 — Release demos handoff

## Scope

Implemented exactly three standalone v0.1 researcher workspaces:

1. `demos/demo_a_zero` — a simple exact factorization (`ZERO`).
2. `demos/demo_b_grounded_newton_dd` — all four frozen C9H4 Newton-DD
   obligations (`ZERO`).
3. `demos/demo_c_unknown` — the frozen order-two polygamma recurrence proof
   gap (`UNKNOWN`).

No frozen research artifact was edited. Demo B explicitly says it is a
verification demonstration rather than discovery evidence. Demo C reuses the
historical `PROOF_REQUIRED` identity and treats `UNKNOWN` as a valid
fail-closed result.

## Engineering behavior

- Each workspace contains `project.yaml`, expressions, notes, assumptions,
  references, `hypotheses/hypothesis.json`, and `runs/.gitkeep`.
- No generated runtime record is committed.
- `demos/run_demos.py` copies inputs to a new execution root before calling
  the public `load_workspace`, `verify_hypothesis`, and `generate_report`
  APIs.
- The runner checks source hashes, modes, and mtimes before and after each
  run; it emits a stable summary without runtime-dependent paths or timings.
- A retained replay is opt-in through `--output-root`, which refuses an
  existing path.

## Integration notes

- The demo workspaces are already compatible with the required workspace CLI
  surface. `DEMOS.md` lists the final `inspect`, `verify`, and `report`
  commands to exercise after E3 is integrated.
- The v0.1 assumptions schema cannot encode arbitrary relational predicates
  or excluded discrete sets. Demo B and Demo C state those domain boundaries
  prominently rather than silently repairing them.
- `tests/test_release_demos.py` is the focused release regression for the
  exact inventory, workspace validity, outcomes, provenance/report creation,
  and source immutability.

## Scientific boundary

- C9H4 canonical program id:
  `0002761432e0bd2c6c0ea2050622b287ea817d00769555c30a08ee3022dd5b66`.
- C9H4 remains an exact R2 reference object, not a search result.
- The polygamma example remains `UNKNOWN`; no recurrence or special-function
  capability is newly claimed.
