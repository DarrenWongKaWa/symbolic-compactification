# Gap recovery handoff

## Disposition

- R2: `CANDIDATE_FOR_INDEPENDENT_REVIEW`; no admission performed.
- R6: `NO_DEFENSIBLE_R6_CANDIDATE`; no package created.
- Branch: `work/rps-gf-r6-recovery`.
- Commit: the commit containing this handoff; coordinator should use the
  reported git SHA.

## R2 candidate

Package: `rps-candidate-k9-001`.

Public case/member IDs are `C9H4` and `M9H1`–`M9H4`. The proposer view does
not expose the source identity, target type, operator names, member roles, or
the rejected predecessor ID. The unavoidable factorized form of the public
expressions remains an easiness risk for independent review.

The actual public loader returns:

- namespace provenance `EXACT_PROPOSER_REFERENCE`;
- eight exact hash-bound symbols, all `real:true`, none `real:false`;
- assumption statuses `DECLARED, DECLARED, DECLARED, DERIVED`;
- exactly the proposer view, assumptions, catalog, symbols, and four member
  files—no evaluator or verification path.

The old package name incorrectly referred to Eq. 28. The primary arXiv v1 TeX
source proves that the four retained identities are unnumbered lines 705–708
inside an `align*` block. The new dossier binds the surrounding source labels
with exact excerpts and states the correction. Six stored excerpts match the
upstream `CM_dynSys.tex` bytes. Provenance hashes are:

- arXiv source archive: `698a6b496e375aa6a31e0b4750dbe59a438f69bd205a807dca8913269b8a1d4a`;
- `CM_dynSys.tex`: `59ad6a8047c13cd4a8dd1f7c595194f5734aa5049a0949828b23c55ccbcacbc3`.

The assumption contract does not claim positive relative masses. It retains
the paper's real domain and `alpha+beta=1`, plus an explicit positive,
nondegenerate radicand stratum tied to the exact Appendix B rule hypotheses.

M1 results:

| arm | program | obligations | result |
|---|---|---:|---|
| `G_FULL` | named two-node operations + linear reconstruction | 4 | all ZERO |
| `G_NO_HERMITE` | same legal program | 4 | all ZERO |
| `G_PRIMITIVE` | VALUE + LINEAR_COMBINATION composition | 4 | all ZERO |

All programs compile non-tautologically, `load_case_package()` reports no
schema deltas, and every obligation has a recorded HYPOTHESIS step followed by
an exact ZERO/CERTIFIED step.

Freshness/leakage result:

- 79 historical/previous-benchmark documents audited;
- 53 current case JSON documents and 18 package manifests included in the
  bounded recovery audit;
- Guo appears only as a sealed diagnostic reference and was not run;
- four exact matches, all and only the rejected predecessor members;
- zero unexpected exact or alpha-renamed matches;
- zero public target/operator/source-name findings.

The rejected predecessor is preserved as 33 exact files with canonical tree
hash `0943a6ae269d81af89daf96202303e183d7c75f8383a959f67c149501b04fdc0`.

Self-assessment: the package defects are repaired and the case is suitable for
independent DEV admission review as an R2 calibration candidate. It is not a
fresh scientific identity, and its visible algebra may make it easy; neither
fact is hidden. This handoff does not admit it.

## R6 mining

The bounded scan retained no R6 candidate. The strongest fresh source-backed
near-misses were:

1. Greengard–Hagstrom–Jiang Debye potentials, pp. 2–3, Eqs. (3)–(7): real
   multi-operator vector reconstruction, but it needs curl/curl-composition,
   time differentiation, and vector-basis semantics absent from frozen M1;
   Eq. (3) also directly states the representation.
2. Chang–Shrock Potts transfer matrices, arXiv `cond-mat/0506274`, Eq. (5):
   needs matrix power, spectral reconstruction, trace, and determinant; the
   source directly exposes the transfer representation.
3. DLMF Rayleigh formulas 10.49.14–16: parser-feasible only as a short
   derivative ladder and overlaps `rps-real-c8q2`.
4. Higham–Relton higher matrix-exponential derivatives: already mined,
   derivative/response shaped, directly block-exposed, and outside scalar M1.
5. The historical van der Waals candidate: independently downgraded to R1.

Forcing any of these would require a forbidden parser/grammar change, reuse a
current identity, or manufacture R6 depth through scalarization.

## Validation commands

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. \
  /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m pytest -q tests/test_rps_gap_recovery.py

PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. \
  /Users/kawawong/Projects/symbolic-compactification/.venv/bin/python \
  -m pytest -q
```

No grammar, search, parser, verifier, shared manifest, or TEST artifact was
modified.

The collection is deliberately under `research/representation_program_search/recovery/`
rather than the frozen `packages/**` discovery surface. This preserves the
reproducibility of the predecessor's committed global freshness/admission audit;
the new validator separately and explicitly records the four expected exact
repair matches.
