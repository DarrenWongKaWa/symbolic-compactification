# HANDOFF — Subagent C (experimental obligations)

Parent: `45b2b4dc7c823901f4b79713d279c6be7bae2859`
Branch: `work/representation-obligations`
Commit: (filled after commit)
Tests: `.venv/bin/python -m pytest tests/test_representation_obligations.py -q`

## Semantics

`COMPILE_FAILURE` ≠ `UNKNOWN` ≠ `ZERO`.

- Compiler never assigns a verification verdict. `CompileResult.to_dict()` has `n_ok` / `n_fail` / `compile_status`, not `n_unknown`.
- Missing reconstruction (nodes, F, var/point, rhs, basis coefficients, catalog member) → `compile_status=COMPILE_FAILURE`.
- `verify_obligation` on a compile failure returns `verdict=None` with `compile_status=COMPILE_FAILURE`. It does **not** convert that into `UNKNOWN`.
- `UNKNOWN` is only for a compiled (`COMPILE_OK`) obligation the engine cannot decide (e.g. unevaluated `sympy.limit`).

Kinds match `research.representation_invention.schema.OBLIGATION_KINDS`. Historical `research.obligation_ir` is untouched.

## DD constructors

`research.representation_invention.dd` does not yet export `newton_first` / `hermite_nodes` / `repeated_diagonal`. Local fallback is used (`CompileResult.notes` includes `dd_local_fallback`):

- Newton: `(F(x)-F(y))/(x-y)`
- `F[x,x] = F'(x)`
- `F[x,x,x] = F''(x)/2`
- `F[x,x,y] = (F[x,x]-F[x,y])/(x-y)`

If package `dd` later exposes those names, compile/verify will call them.

## Phase 5 positives

| case | verdict |
|---|---|
| Newton first DD `F=z**2` vs `(x**2-y**2)/(x-y)` | ZERO |
| Newton first DD `F=z**3` vs `(x**3-y**3)/(x-y)` | ZERO |
| Repeated node `F[x,x]=F'(x)` (`F=z**2`, member `2*x`) | ZERO |
| Derivative limit `lim_{y→x} F[x,y] = F'(x)` | ZERO |
| Hermite `F[x,x,y]` (`F=z**3`, member `2*x+y`) | ZERO |
| Hermite `F[x,x,x]` (`F=z**3`, member `3*x`) | ZERO |
| Piecewise generic vs diagonal as CONFLUENCE (`limit x→y`) | ZERO |
| `F=polygamma(0,z)` Newton vs explicit `(ψ(x)-ψ(y))/(x-y)` | ZERO |
| Substitution / permutation / derivative / equality | ZERO |
| Recurrence `F(n)=n**2`, `F(n+1)-F(n)=2n+1` | ZERO |
| Master instance `F(a)=a**2` | ZERO |
| Basis `1+2x+3x**2` | ZERO |

## Documented unsupported (not ZERO)

- No extra polygamma identity (harmonic / series rewrite) is claimed. The explicit difference form is ZERO via `_equal`. A wrong special-function member (`polygamma(1,x)`) is NONZERO, not ZERO. If `_equal` cannot decide a rewrite, that path is UNKNOWN, never ZERO.
- Package `dd/` constructors were not available; local formulas only.
- Prose `proof_obligations` strings are not compiled; typed drafts or operators are required.

## Adversarial (false ZERO = 0)

Sign error, coefficient error, wrong node multiplicity, wrong derivative order, wrong limit value, wrong branch/member swap, wrong recurrence: all `NONZERO` (or compile-failure), never ZERO.

## Remaining risks

- `_equal` is expand/simplify of the difference. Polynomials and the explicit polygamma difference are decided. Hard special-function identities may be UNKNOWN.
- `parse_expression(evaluate=True)` collapses `Piecewise((..., True), ...)` when `True` is first; catalog piecewise must follow Eq-branch-then-True (engine convention).
- Permutation obligations accept only swapped candidates (unpermuted member is NONZERO).
