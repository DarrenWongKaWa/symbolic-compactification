# Many-body equivalence mini-benchmark (v0)

This benchmark asks how often a strong agent working on its own accepts a
many-body identity that it should not, compared with the same claims
checked by this tool.

## Items

`items.yaml` holds 29 claims with declared assumptions, in four groups:

| Group | n | What it tests |
|---|---:|---|
| `exact-true` | 6 | textbook Matsubara sums (fermionic and bosonic bubbles, a double pole, a convergence factor, a mixed-order pole) |
| `seeded-error` | 8 | the same identities, or Langreth and Lindblad identities, with one planted error: a sign, `β` versus `β/2`, the wrong convergence factor, the wrong statistics, a wrong Keldysh component, or the sign of `H_eff` |
| `hypothesis-trap` | 8 | claims that need a hypothesis the declaration omits: a bosonic pole at `ν₀`, a `1/z` tail without a convergence factor, `Γ > 0`, a one-sided versus two-sided limit, poles that may sit on the Matsubara axis, or an overstated remainder order |
| `asymptotic-operator-true` | 7 | a high-frequency tail, a large-argument digamma expansion, a Laurent series, Langreth rules, the Lindblad generator versus `H_eff`, and a Fermi–Lorentzian digamma integral |

The ground truth is fixed by `verify_ground_truth.py`, which does not use
the tool. It uses brute-force symmetric Matsubara sums with mpmath,
quadrature, the growth of the remainder quotient, and random-matrix
instances for the operator and Keldysh items. For each conditional item it
records where the claim breaks. Result: 14 claims are usable as stated and
15 are not.

## Arms

| Arm | Setup |
|---|---|
| Whiteboard agent | frontier model (same class as the model that built this tool), question sheet only, no tools |
| Agent + Python | same model, free use of SymPy, mpmath and numpy, no access to this package |
| symbolic-compactification | `run_tool.py` runs each item's `symbolic-compactification manybody ...` command and maps statuses to answers |

The agents saw a blinded sheet with the claim, the declared assumptions
and the shared conventions. They did not see the truth labels or the tool
encodings.

## Scoring

`score.py` asks one question per item: can the claim be used exactly as
stated? The headline number is **false certifications**, i.e. answering TRUE
for a claim that is FALSE or CONDITIONAL. The tool may abstain
(`UNKNOWN`, `NUMERICAL_SUPPORT`). An abstention counts as neither right nor
wrong and shows up as lower coverage.

## Results (2026-09-26)

| Arm | Answered | Correct: usable as stated? | False certifications | Exact 3-way label |
|---|---:|---:|---:|---:|
| Whiteboard agent (reasoning only) | 29/29 | 29/29 | 0 | 26/29 |
| Agent + Python | 29/29 | 29/29 | 0 | 26/29 |
| symbolic-compactification | 26/29 | 26/26 | 0 | 26/26 |

**v0 does not separate the arms.** A frontier model gets every one of these
single-step textbook identities right, with or without Python. It also gets
the hypothesis traps right. The tool is also never wrong, but it abstains on
three items: `C3` (numerical support only, which does show the sign problem),
`C4` (limit undecided without a sign on `c`) and `D7` (numerical support
only). The only label differences are FALSE versus CONDITIONAL on `C2`,
`C4` and `C5`, where the labels overlap by definition.

The differences show up elsewhere:
- **Evidence.** The agents return a sentence per item. The tool returns a
  status, the derived closed form or limit, and a certificate hash, and
  inside an audit a replayable record.
- **What was actually checked.** The Python arm ran no computation on
  6 of 29 items (C4, C5, C6, C8, D1, D3) and answered those
  by reasoning.
- **Stated confidence.** On the traps the agents were right but reported
  confidence 0.5–0.85.
- **Usability.** Running the benchmark exposed a CLI bug: an expression
  starting with `-` was read as a flag. It is fixed and has a test.

The conclusion for the product is that its value is not accuracy on
textbook identities, which frontier models have saturated. A v1 benchmark
should use long, non-textbook derivation chains with mixed conventions,
where published evaluations still find frequent model errors.

Raw answers are in `results/arm_*.json`. The scores are in
`results/scores.json` and [`results/SUMMARY.md`](results/SUMMARY.md).

## Reproduce

```bash
python3 verify_ground_truth.py   # independent numerics -> results/ground_truth.json
python3 run_tool.py              # tool arm -> results/arm_tool.json
python3 score.py                 # -> results/scores.json, results/SUMMARY.md
```

The agent arms were run once each, by hand, from the blinded sheet. Their
answers are stored as they were returned.

## Limitations

- **Small and single-run.** There are 29 items and one run per agent arm,
  so there is no estimate of variance.
- **Authored by the tool's side.** The items were written with knowledge of
  what the tool can check, which favours the tool. The categories where the
  tool must abstain (`C3`, `C4`, `D7`) are kept on purpose.
- **Encoding not tested.** The tool arm uses hand-written encodings. In real
  use an agent writes them, and a wrong encoding can "verify" the wrong
  claim.
- **Overlapping labels.** FALSE and CONDITIONAL overlap. Only the binary
  "usable as stated" score should be compared across arms.
