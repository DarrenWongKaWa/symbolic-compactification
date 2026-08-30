# R3 Final Review — Symbolic Algebra

## Review decision

The `GATE_BLOCKED` closure is symbolically and operationally sound. The
recorded evidence preserves the three distinctions that matter most:

1. exact equality in the frozen parsed namespace;
2. representation-depth classification of a compiled reference program; and
3. scientific benchmark admission.

Those are not interchangeable. In particular, `C9H4` supplies an admitted,
non-tautological R2 reference representation with exact obligations, while
Q7V3 supplies a mathematically valid R3 diagnostic that fails freshness and
scientific-catalog admission. Neither is a search result. The R4/R5 and R6
records correctly retain proof gaps and packaging gaps instead of converting
them into false mathematical refutations.

Recommended publication decision: **F — STRUCTURED SEARCH ALSO FAILS TO
SUPPORT REPRESENTATION INVENTION**, with a mandatory qualifier: this is a
failure to obtain supporting evidence because the required scientific DEV
suite was not assembled in the bounded frozen experiment. It is not evidence
that structured-search algorithms were executed and failed.

## Scope and evidence authority

This was an independent, read-only symbolic-algebra review. It did not run a
scientific search, call an LLM, construct a new case, or change the parser,
verifier, grammar, scoring policy, manifests, or source artifacts.

Reviewed authority:

| role | commit |
|---|---|
| integrated evidence inspected by the final gate auditor | `a7ad6ab552360b83ad54d315a6774ca6fad7eeaa` |
| final DEV-gate closure | `b54256766054b9ebdeaeaed9bbb6448cc9405ea0` |

Principal exact evidence:

| artifact | SHA-256 |
|---|---|
| `audits/dev_gate_final/GATE_AUDIT.json` | `767ce24dbda3a81a84d62d55e0efcfc6447e3b4a4622b10e6447eaa72c078606` |
| `audits/gap_recovery_admission/INDEPENDENT_GAP_RECOVERY_ADMISSION_AUDIT.json` | `81750690d978f47c41f35bf862cec56604fa3285b3ce04129a1b83f626c2f82a` |
| `evaluation/clearances/C9H4.json` | `0f03b4b26c88862ffd7723247aa882f19ebc215b318b0f7244f03ce062584f92` |
| `audits/r3_missing_final/R3_MISSING.json` | `7c3e3d634968dd109ed02de4270afbb01f5c00669c03dd74fb46900080de04f4` |
| `audits/fresh_r3_q7v3_independent/AUDIT.json` | `f25f40087bdfeeb7ce784a0c763176f39a937403677c584a00cd6ff5689f9c8e` |
| `audits/r4_r5_candidate_recovery/MINING_BOUNDARY.json` | `5066d8d7622f804b6c18350d2205e84eafcfb9711cae3cd486b0b8de72be7d02` |
| `audits/r6_feasibility/INDEPENDENT_R6_FEASIBILITY_AUDIT.json` | `d2b8d9e9a7e2eada6be623e7b13720ac3b407051dca0b60d9ab952a0986f032c` |
| frozen verifier implementation, `src/symbolic_compactification/verifier.py` | `6cbb11ab7f80584c9cc27c16c8e53934d32deb54c53e8c805d68daf356341fe6` |

The final gate validator returned `VALID` with no errors. The seven focused
clearance, gate, R2, R3, R4/R5, and R6 test modules returned **38 passed**.
These checks validate evidence integrity and software behavior only.

## Verdict-semantics audit

The verifier implementation and decisive stored steps agree with the protocol:

- `ZERO` is emitted only when the parsed residual simplifies to exact symbolic
  zero, directly or after exact complex normalization.
- `NONZERO` requires an exact substitution followed by a SymPy proof that the
  exact value is not zero.
- all other cases, including timeouts, unproved special-function identities,
  and exceptional paths, remain `UNKNOWN`.
- session promotion additionally requires `ZERO`, `CERTIFIED`, `PROVEN`,
  exact-zero evidence, matching current/candidate text and hashes, and no
  `HUMAN_REQUIRED` assumption gate.

The orthogonal axes are also used correctly. The polygamma diagnostic D003 is
`UNKNOWN`, `UNVERIFIED`, and `PROOF_REQUIRED`; it is not mislabeled
`HUMAN_REQUIRED`. The log diagnostic D002 is `NONZERO`, `UNVERIFIED`, and
`REFUTED`, with exact point `x=1/2`, `y=-2` and exact residual value
`4*I*pi/25`. The elementary diagnostics D001 and D004 are exact `ZERO` steps,
but their ZERO status is not promoted into benchmark admission.

One important semantic limit must remain explicit in the final report:
`ZERO` certifies the expressions as parsed under the symbol namespace. The
verifier records a supplied assumption contract but does not use arbitrary
relational predicates as a proof engine. Domain admission is therefore a
separate hard gate. This distinction is handled correctly in the closure, but
must not be compressed into a statement that the verifier proved every
source-domain predicate.

## R2 classification and exact evidence

`C9H4` is correctly classified as R2 rather than R1 or R3. Its canonical full
program contains one shared latent scalar kernel

```text
F(z) = 1/sqrt(z)
```

four two-node Newton divided differences, and explicit linear reconstruction
coefficients. The four node lists have distinct labels and contain no repeated
node, so the program does not reach Hermite/R3 structure. Conversely, it is
not merely a parameter-family VALUE map: the common latent is reused across
four non-identical source members through genuine first divided differences.

The primitive ablation expresses the same relations using `VALUE` and
`LINEAR_COMBINATION`, with quotient coefficients made explicit. That shows
that the named `NEWTON_DD` operator is not required for *reference-program
expressibility*. It does not lower the mathematical classification below R2,
and it does not show that primitive search discovered the construction.

All four required obligations are exact ZERO under each of `G_FULL`,
`G_NO_HERMITE`, and `G_PRIMITIVE`. The correct count is therefore four
scientific obligations replayed in three encodings, not twelve independent
scientific identities. The admission audit also correctly records the
factorized public formulas as an easiness risk and limits the package to
`DEV_R2_CALIBRATION_ONLY`.

## R3 classification and freshness boundary

Q7V3 is mechanically R3. Its compiled targets contain arity-four divided
differences with multiplicity partitions `(2,2)` and `(2,1,1)`. Nine stored
obligations across three grammar variants are exact ZERO, and the primitive
variants show that a named `HERMITE_DD` operator is unnecessary for expressing
the reference construction.

The rejection is nevertheless correct because it is an *admission* failure,
not a symbolic one. The public scalar members and matrix-unit specializations
were benchmark-author choices made to isolate those partitions, and the hidden
target is directly contained in the inspected generic old-TEST divided-
difference superfamily `mp-opitz-dd-01`. Thus:

- it is valid to call Q7V3 a non-tautological R3 compiler diagnostic;
- it is invalid to call it a fresh R3 scientific DEV case;
- it is invalid to count its primitive reference program as primitive-search
  success; and
- its rejection does not refute Hermite composition.

The final `R3_MISSING` record is appropriately bounded. It reports that no
screened source survived the simultaneous source-catalog, domain, freshness,
leakage, and operational-depth gates. It does not claim that R3 mathematics
does not exist or that no future source mining could produce an admissible
case.

## R4/R5 exact boundary

The R4/R5 audit handles the branch-sensitive examples correctly:

- D001 proves a first log divided-difference lowering exactly, but that object
  is an old-TEST Newton/Piecewise-DD instance.
- D002 does **not** refute the positive-SPD scientific identity. It refutes the
  proposed lowering on the broader frozen real-symbol domain, where principal
  logarithm branches make `log(x/y) = log(x)-log(y)` false. The exact negative
  point is admissible in that broader namespace and is not singular.
- D003 leaves the digamma recurrence proof-required. The familiar status of
  the recurrence cannot substitute for a repository ZERO verdict.
- D004 proves the historical Hermite-two form only after an external
  positive-domain log lowering; the audit correctly labels it diagnostic and
  not source-member certification.

Consequently `R4_R5: MISSING` is justified. It would be an overclaim to say
that the scientific formulas were false, that special-function recurrence is
unsupported mathematics, or that a ZERO on D004 certifies the original
positive-matrix source member inside the frozen namespace.

## R6 depth and packaging boundary

The R6 result is also reported at the right logical level. The source audit
finds genuine multi-operator mathematics—block exponentials, higher Fréchet
derivatives, `dexp`/Bernoulli constructions, response operators, and tensor or
transfer structures—but frozen M1 gives these no executable matrix, block,
noncommutative, integral, trace, determinant, vector, or tensor semantics.

The available scalar lowerings do not repair this:

- the van der Waals package exposes its Helmholtz master and is an R1
  derivative-response graph;
- the AB/BA scalar package is R2;
- the block-exponential lowering collapses to an ineligible scalar R3 case;
  and
- the Feshbach lowering is R0 shared-denominator CSE.

Exact receipts for those scalar forms certify only the scalar reconstructions.
They cannot certify the missing block/operator semantics or raise the depth of
the programs. `R6_MISSING / PACKAGING_GAP` is therefore correct for the
bounded frozen registry. It must not be restated as mathematical impossibility,
parser inferiority relative to a search method, or evidence that an R6 search
failed.

## Open symbolic-semantic limitation

The repository records an unresolved namespace defect: `real:false` is
implemented as SymPy's *provably non-real* assumption rather than as the
documented complex-probe selector. This can collapse real-axis Piecewise
branches. None of the decisive admitted C9H4 receipts depends on
`real:false`, so this defect does not reverse the final gate decision.
Nevertheless, the final repertoire must keep the limitation visible and may
not generalize the reviewed exactness claims to unrestricted-complex cases
until a separately versioned migration replays them.

## Claims supported and overclaims to prohibit

Supported:

1. `C9H4` is one assumption-complete, non-tautological, exact R2 identity
   admitted only for DEV calibration.
2. Q7V3 is a mechanically exact R3 diagnostic but not a fresh scientific case.
3. The R4/R5 audit contains exact ZERO, NONZERO, and fail-closed UNKNOWN
   diagnostics with the claimed meanings.
4. The frozen executable language did not admit an honest R6 case from the
   bounded hash-bound registry without depth collapse or target exposure.
5. The mandatory DEV suite was incomplete, so the gate correctly prevented
   scientific method execution and TEST freeze.

Prohibited:

1. Treating a reference-program ZERO as evidence that any search found it.
2. Treating Q7V3's primitive construction as grammar-ablation success.
3. Treating D002 as a refutation on the source's positive-SPD domain.
4. Treating D003 UNKNOWN as falsehood, assumption incompleteness, or rejection.
5. Treating `R3_MISSING` or `R6_MISSING` as universal nonexistence results.
6. Treating `PACKAGING_GAP` as search failure or AI advantage.
7. Reporting R2–R8 performance, search-budget curves, grammar advantage,
   verifier-feedback benefit, SOL effect, or AI search advantage; no eligible
   scientific condition ran.
8. Saying that structured search empirically failed the R3 frontier.

## Publication recommendation

Choose exactly **F — STRUCTURED SEARCH ALSO FAILS TO SUPPORT REPRESENTATION
INVENTION**.

This is the only label among A–F that matches the absence of supporting
scientific search evidence without calling the unrun implementation
“promising.” The scientific wording must remain:

> Under the frozen V1 rules, the bounded run could not assemble the mandatory
> fresh scientific DEV calibration suite. Structured representation-program
> search therefore gained no supporting evidence in this experiment; its
> algorithms, AI heuristic, verifier feedback, SOL conditioning, efficiency,
> and held-out generalization were not empirically adjudicated.

That conclusion is a negative closure of this research line, not a symbolic
refutation of representation-program search.
