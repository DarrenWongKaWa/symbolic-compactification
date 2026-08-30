# J2 Real-Domain DEV-Candidate Recovery Handoff

Implementation commit: `7e5203693dd88d5eba396a2617333d19204cbcbe`

Branch: `work/rps-dev-recovery`

Coordinator synchronization merge: `56c6386`

## Disposition

No package was admitted and no shared DEV/TEST manifest was changed. The strict
validator result is `VALID_CANDIDATE_SET`, but both retained packages are labeled
only `CANDIDATE_FOR_INDEPENDENT_REVIEW`. `PACKAGE_READY` in their frozen package
headers means machine packaging is complete; it is not `ADMISSION_READY`.

| Slot | Result | Package | Evidence summary |
|---|---|---|---|
| R2 | `MISSING` | none | Bounded real-domain divided-difference identities were historical Daleckii-Krein/resolvent variants. |
| R3 | review candidate | `rps-real-c3j9` | Real-SPD second-order matrix-log components; 3 obligations x 3 grammar variants = 9 ZERO receipts. |
| R4/R5 | review candidate | `rps-real-c8q2` | Real nonzero radial special-function orders 0--2; 3 obligations x 3 grammar variants = 9 ZERO receipts. |
| R6 | `MISSING` | none | The defensible SO(3) master candidate needs a zero stratum blocked by the frozen latent-symbol real/non-real defect; scalar alternatives collapsed below R6. |

The missing-slot rationale is machine-readable in
`packages/real_domain_recovery/RECOVERY_GAPS.json`.

## Candidate C3J9 (R3)

Primary source: Emanuel H. Rubensson, *A Unifying Framework for Higher Order
Derivatives of Matrix Functions*, arXiv `2306.15814`, published in SIAM J. Matrix
Anal. Appl. 45(1), 504--528 (2024), DOI `10.1137/23M1580589`.

- Retrieved PDF SHA-256:
  `732b25ee69191ccd32a936ad3f61bced8e97e2f77e59b79da94bea0acc2e281e`.
- Exact locator: PDF pages 9--10, equations (4.3)--(4.5); the real `A,E`
  statement below (5.2) was also checked.
- The retrieved PDF hash was independently reproduced, pages 9--10 were
  rendered with Poppler at 150 dpi, and the displayed equations were visually
  inspected.
- The fixed instance is an affine real-symmetric perturbation of
  `diag(x,y)`, with `x,y>0` and `x!=y`; affine dependence explicitly makes the
  `U^(alpha)` term in (4.5) zero.
- G_FULL uses `NEWTON_DD` and two structurally distinct repeated-node
  `HERMITE_DD` objects. G_NO_HERMITE and G_PRIMITIVE reconstruct all three
  members using only primitive value, derivative, substitution, and linear
  combination operations. A named Hermite primitive is therefore not required.
- Risk retained: visible log-kernel reuse and strong thematic/formula overlap
  with historical first-order and Hermite benchmark families. The structural
  audit found no exact or alpha-renamed member match, but admission still
  requires an independent scientific/depth decision.

## Candidate C8Q2 (R5 claim under review)

Primary authority: NIST Digital Library of Mathematical Functions, sections
10.49, 10.51, and 10.73(ii).

- Exact retrieved TeX artifacts and SHA-256 hashes are stored in the package
  for 10.49.E3a, E3b, E3c, E14a, and 10.51.E1a.
- The authoritative 10.73(ii) HTML retrieval is recorded with SHA-256
  `419e460696027ff105fbcd0302ac0ccf774ba4c870e85d51cc93fc0f8f5f3045`.
- The retained source domain is explicitly narrowed to real `x!=0`; no
  zero-limit continuation or complex-domain receipt is used.
- One latent `sin(u)/u` kernel gives order 0 by value and order 1 by its
  differential generator; the source order relation reconstructs order 2.
  Full, no-Hermite, and primitive programs are identical and non-tautological.
- Risk retained: this is a fixed three-order slice with visible trigonometric
  atoms. An independent reviewer may downgrade it below R5 or decide that a
  symbolic heuristic/CSE baseline already captures the useful structure. The
  package makes no admission or invention claim.

## Integrity gates

- Strict `artifact_hashes` cover every package artifact except the
  self-referential `package.json` exclusion documented by the schema.
- Both packages load through M1 with zero schema deltas.
- Full, no-Hermite, and primitive variants compile with explicit output links,
  exact source-member references, and `tautological=false`.
- Every variant/obligation run records an init session, main-agent HYPOTHESIS
  step, exact verification step, and hash-bound ZERO/PROVEN/CERTIFIED receipt.
- Proposer-visible IDs are opaque. The proposer projection contains source
  members/catalog, assumptions, and structural observations, but no source
  names, gold program, operator sequence, target depth, or verdict.
- Duplicate audit used 79 historical/current references, explicitly including
  the sealed Guo diagnostic. Neither candidate has an exact or alpha-renamed
  member match in the current package pool.
- Existing complex Relton/phi recovery artifacts were not modified or
  retrofitted.

Audit artifacts:

- `research/representation_program_search/audits/real_domain_recovery/REAL_DOMAIN_RECOVERY_AUDIT.json`
- `research/representation_program_search/audits/real_domain_recovery/REAL_DOMAIN_RECOVERY_AUDIT.md`

## Verification

- Focused recovery tests: `9 passed`.
- Program/package/leakage/assumption cluster: `54 passed`.
- Exact committed tree full suite, with bytecode writes disabled to prevent a
  neighboring test from treating `__pycache__` as a package: `1785 passed in
  227.38s`.

Recommended next action: cherry-pick the implementation and handoff commits,
then assign independent source/domain, depth/CSE, and leakage/duplicate review.
Do not add either package to DEV until those reviews pass and a coordinator
performs the explicit admission step.
