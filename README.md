# symbolic-compactification

A standalone symbolic compactification engine: strict whitelist SymPy parser,
exact residual verifier with fail-closed verdicts, and JSON session records.

**Requirements:** Python ≥ 3.10 and SymPy. Nothing else.

Agents operating this repo should read [`AGENTS.md`](AGENTS.md) first.

---

## 5-minute quickstart

### 1. Install

```bash
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

This installs the package and the `symbolic-compactification` CLI.

### 2. Run the tests

```bash
.venv/bin/pytest tests/ -q
```

### 3. CLI walkthrough

Create two expression files and a symbol declaration:

```bash
printf 'x**2 + 2*x*y + y**2' > current.txt
printf '(x+y)**2'            > candidate.txt
printf '{"symbols": ["x", "y"]}' > symbols.json
```

Inspect the input (hash, symbols, size):

```bash
symbolic-compactification inspect current.txt --symbols symbols.json
```

Verify the candidate against the current expression:

```bash
symbolic-compactification verify \
    --current current.txt --candidate candidate.txt --symbols symbols.json
# verdict: ZERO — exit code 0
```

Run the same transformation inside a recorded session:

```bash
symbolic-compactification init-session \
    --current current.txt --symbols symbols.json
# run_id: 20260819T000000Z-a1b2c3

symbolic-compactification step --run 20260819T000000Z-a1b2c3 \
    --candidate candidate.txt --symbols symbols.json
# verdict: ZERO → promoted: workspace/runs/<run-id>/final/current.json
```

Every step (whatever its verdict) is recorded under
`workspace/runs/<run-id>/steps/`. A candidate is promoted only on a ZERO
verdict.

### 4. Python API

```python
from symbolic_compactification import verify_equivalent

result = verify_equivalent("x**2 + 2*x*y + y**2", "(x+y)**2", ["x", "y"])
print(result.verdict)               # "ZERO"
print(result.residual)              # "0"
print(result.evidence)              # [{"kind": "exact_symbolic_zero", ...}]
```

`verify_equivalent(current, candidate, symbols)` parses both sides through
the strict whitelist parser, computes `expand(current - candidate)`, and
returns a `VerificationResult` with `verdict`, `residual`,
`simplified_residual`, `evidence`, and (on NONZERO) `counterexample`. It
never raises — every failure path returns UNKNOWN.

For file-based ingestion use `load_expression(path, symbols)`, which hashes
the raw bytes (SHA-256) and parses strictly; the file + hash owns the
canonical expression.

## Verdict semantics

| Verdict   | Meaning                                               | Exit code |
|-----------|-------------------------------------------------------|-----------|
| `ZERO`    | Difference simplified to exact symbolic zero          | `0`       |
| `NONZERO` | Difference proven nonzero at an exact rational probe  | `2`       |
| `UNKNOWN` | Undecided — no proof either way (fail closed)         | `3`       |

(Parse, load, or usage errors exit with `4`.)

- ZERO requires exact symbolic proof (directly or after complex
  normalization). No numeric tolerance.
- NONZERO requires SymPy to *prove* a probe value nonzero. Approximate or
  "looks nonzero" evidence never counts.
- Everything else is UNKNOWN: promotion is blocked, and the decision goes
  back to the caller (or the human).

## Design principles

- **Deterministic verification.** Every transformation is adjudicated by the
  same exact pipeline: `expand(current - candidate) → simplify → complex
  normalization → exact rational probes`. Same inputs, same verdict.
- **Fail closed.** Only an exact symbolic zero yields ZERO; only a proven
  exact counterexample yields NONZERO; every undecided or exceptional path
  returns UNKNOWN, and UNKNOWN never promotes.
- **Exact Rational probes.** The probe lattice uses exact rationals and
  Gaussian integers — never floats — so counterexamples are proofs, not
  measurements.
- **No LLM decides math.** Language models propose candidates and read
  residuals; they never certify equivalence. Proof belongs to the verifier.
- **Provenance by construction.** Expressions are ingested from files with
  SHA-256 hashes, and every step — success or failure — lands in the run
  record.
