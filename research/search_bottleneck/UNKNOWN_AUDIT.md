# UNKNOWN audit (hard DEV, seed 0)

UNKNOWN is fail-closed, not success. This table is for H4
(verifier incompleteness) vs wrong/unparseable hypotheses.

| Item | Candidate class | Verdict | Evidence kind | Interpretation |
|---|---|---|---|---|
| D2-weighted `s(n)` / `r(n)` | unexpanded auxiliary | UNKNOWN | construction or undecided | **packing**: name not substituted; not a missing identity |
| D2-shared Lorentzian `-I g / (Δ^2+g^2)` | extra symmetry claim | UNKNOWN | simplification_undecided | extra physics; not linearity. Could be H4 *or* false |
| D2-shared symmetrized G | extra symmetry | UNKNOWN | simplification_undecided | same |
| D3 `PsiThermal(zP,zM)` | unexpanded Function | UNKNOWN | construction/undecided | packing |
| D3 `-A*pi*cot(pi*zP)` | reflection without `zP+zM=1` | UNKNOWN | **construction_or_parse_failed** (`cot` not in parse whitelist) | **parser**, not polygamma prover gap. Would also be scientifically illegal without a new assumption |
| D4 `K(x,y)` drop Piecewise | confluence | UNKNOWN | simplification_undecided_no_exact_counterexample | **H4-shaped**: engine cannot prove generic-K continuity, and cannot refute it with exact probes. Blank claimed proven |
| D4 `Limit(...)` | confluence written as Limit | UNKNOWN/parse | Limit not in whitelist | **parser / unsupported op** |
| D5 `X(n,m)+X(m,n)` | named generator unexpanded | UNKNOWN | undecided | packing; expanded tautology would be ZERO |
| D5 prose / Hadamard | not an expression | n/a | not parsed | search output not a candidate |
| Fermi `-1/z` off-diagonal | polygamma recurrence | not ZERO (UNKNOWN here; NONZERO if `z` nonzero at `-1/2`) | not an identity on the declared domain | **wrong extra identity**, not a missing sound rule to add blindly |
| Guo drop Piecewise / contour residues | L5-style slogan | unverified (no bytes) | — | same UNKNOWN as 2026-08-21 `TIME_BUDGET_EXCEEDED` on a crude drop |

## H4 verdict

Do **not** treat this as a mandate to add `polygamma(0,z)-polygamma(0,z+1)=1/z`
or “delete Piecewise” to the engine. The recurrence is domain-sensitive
(NONZERO at a pole). Generic `K(x,y)` confluence is genuinely undecidable
in this residual engine (UNKNOWN is correct).

UNKNOWN mass is dominated by:

1. unexpanded names / prose (proposer packaging);
2. unsupported syntax (`cot`, `Limit`);
3. true incompleteness for confluence of *generic* kernels;
4. historically, timeout on huge Guo drop-Piecewise.

(1) and (2) are proposer/IR problems. (3) is verifier incompleteness of a
class that needs assumptions + analysis, i.e. `HUMAN_REQUIRED` or a new
proof mechanism — not a silent ZERO. (4) is resource + same confluence
issue.
