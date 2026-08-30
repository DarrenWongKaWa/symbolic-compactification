# `real:false` namespace contract defect

Status: **OPEN — fail closed; verifier/parser unchanged**

Detected during strict DEV-package recovery, before any scientific search run.

## Contract

`AGENTS.md` states that the `real` field selects the verifier probe lattice
(real versus complex probes). Its example permits
`{"name":"a","real":false,"nonzero":true}`.

## Implementation

`src/symbolic_compactification/parser.py::_symbol_locals` passes the Boolean
value directly to `sympy.Symbol(..., real=value)`. In SymPy, `real=False`
means **provably not real**; it does not mean an assumption-free symbol that
may take arbitrary complex values.

Consequences observed with the repository's pinned SymPy:

```text
Symbol("z", real=False): Eq(z, 0) -> False
Piecewise((1, Eq(z, 0)), (2, True), evaluate=False) -> 2
Symbol("z", real=False, nonzero=True) -> InconsistentAssumptions
```

The first two outcomes silently exclude the real axis, including zero. The
third makes the documented complex/nonzero declaration unparsable.

## Scientific impact

- A Piecewise removable-value branch at a complex-domain node can disappear
  during parsing and create an apparent ZERO that does not certify the stated
  complex-domain claim.
- A ZERO receipt under `real:false` is bound to SymPy's non-real assumption,
  not automatically to the contract's intended unrestricted complex domain.
- Exact package claims using `real:false` require contract-defect review even
  when their residual happened to simplify to zero.

The attempted phi-function recovery case was rejected as `PACKAGING_GAP`; its
collapsed-branch evidence is ineligible and is not retained as a scientific
success.

## Required disposition

Do not change the parser or verifier inside Representation Program Search V1.
Do not replace the declared complex domain with a real domain. Do not count an
apparent ZERO caused by branch collapse. Keep affected cases out of fair DEV
or TEST comparison until the human resolves the contract and a separately
versioned verifier migration replays them.

