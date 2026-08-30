# Independent R6 feasibility audit

Disposition: **`R6_MISSING`**, with failure class **`PACKAGING_GAP`**.

No scientific package was created. This audit independently confirms the
bounded conclusion in commit `80d84e7`: the mined registry contains plausible
multi-operator mathematics, but no identity can currently be made into an
honest R6 calibration case under the frozen parser and Program IR while also
passing source, freshness, leakage, and depth gates.

This is a repository-scoped result, not a proof that R6 representations do not
exist. It does not authorize a parser, verifier, grammar, method, manifest, or
TEST change.

## Bound scope

The audit recomputes and hashes all of the following at integrated tree
`009bd2acfab00c770bacdd71e597e9a40e2b8904`:

| Registry | Count | Canonical registry SHA-256 |
|---|---:|---|
| current case JSON | 53 | `6a79dde9b4384ec5651671001c26a704e2d138f304542117baf15b596508f46a` |
| current scientific dossiers | 39 | `6bc8b0d0eb5cc4c280c388aff87ee2bab7a5d7259623a9184c9b8aa90904bb71` |
| current package manifests | 19 | `07bbce9e9f6e11adb0d4faaa0fb512ec28dea6f522052457646dfaf688d48034` |
| historical duplicate corpus | 79 | `a2dd7c4d6f31608160c70b9b1973f26567e3fa3c39129a969aaf90ec16f34f12` |
| historical dossiers labelled R6 | 14 | `511eebfc793f9248ba2f9d66b2f1ee471cdadcb4136e37f5a814c46f6875b4d5` |

The 39 current scientific dossiers audit to 14 R6, 8 R8, 7 R5, 4 R4,
2 R2, 2 R1, 1 R3, and 1 R7. The 14 R6 dossiers consist of 12
`PACKAGING_GAP`, one `DUPLICATE_REVIEW`, and one
`PROBLEM_UNDERSPECIFIED`. Every current dossier has zero frozen source
artifacts and no admission package in the dossier-level audit. Higher-depth
tensor/theta dossiers are not silently substituted for R6; they remain
packaging gaps or finite-index diagnostics.

Commit `80d84e7` correctly recorded 18 package manifests at its own point in
time. The present integrated tree has 19 because the later `rps-case-q7v3`
candidate was added. That later R3 package does not alter R6 feasibility.

## Frozen executable language

`RepresentationGrammarV1` names `MATRIX_FUNCTION`, but the M1 constructor
parses every latent core as a scalar SymPy expression. The label does not add
matrix multiplication, block projection, spectral calculus, trace,
determinant, matrix order, commutators, curl, tensor contraction, or vector
basis semantics.

The parser admits `exp`, `polygamma`, and structural `Sum`. It rejects the
required surface forms `Matrix`, `Trace`, `Determinant`, `Integral`,
`Commutator`, Hurwitz `zeta`, and `factorial` under the frozen function
policy. Declaring an otherwise unknown function would provide an opaque head,
not the missing mathematical identity. `RESOLVENT`, `GENERATING_FUNCTION`,
and `BLOCK_OPERATOR` remain optional-later names and are not active V1
operators.

## Requested candidate families

### Block exponentials and Fréchet coefficients

The primary Higham–Relton paper explicitly gives the four-block lift in
equation (3.4), Theorem 3.5 states that the upper-right block of `f(X_k)` is
the kth Fréchet derivative, and the following paragraph specializes it to the
second derivative. This is sound R6-like mathematics. It still fails this
experiment because:

- frozen M1 cannot state block matrices, matrix functions, or block
  projection;
- `rps-dp-relton-second-frechet` is structurally historical with
  `mp-mathias-block-01` and `sciml-vanloan-blockexp-01`;
- the strict recovered package `rps-candidate-j2-001` compiles only after
  lowering to a generic scalar R3 repeated-node program, which is itself
  ineligible and is not R6;
- no R6 package stores the primary source bytes under a hash-bound source
  artifact.

Thus a scalar block entry is a verifier diagnostic, not an operational block
master.

### Matrix functional calculus

The general AB/BA, Kronecker, sign/square-root, Riccati/geometric-mean,
Hadamard-adjoint, Cauchy–Dunford, Lyapunov, and state-transition candidates
all require matrix or operator semantics absent from M1. The only packaged
AB/BA reduction, `mx-abba-exp-fixed-r6`, does not load under strict M1 and is
independently R2: one Newton divided difference plus linear reconstruction.
Its proposer-visible `G0005` is exactly the shared Newton quotient, so it also
fails the public source-member-master gate.

### dexp, inverse dexp, Bernoulli, and Magnus

The Iserles–Munthe-Kaas–Nørsett–Zanna source explicitly defines `ad` in
(2.40)–(2.41), `dexp` in (2.42)–(2.44), its Bernoulli-series inverse in
(2.45)–(2.46), and the Magnus `dexp^{-1}` equation in (4.3). This is a
genuine multi-operator master. It cannot be packaged honestly because the
required noncommutative adjoint tower, operator exponential/inverse, Bernoulli
semantics, and spectral invertibility condition have no frozen executable
meaning. The scalar commuting probe reduces to a reciprocal product and
erases the representation depth.

### Thermal and polygamma

DLMF 25.11.12 gives the Hurwitz-zeta/polygamma bridge with the stated
`Re(a)>0` subsection domain. Frozen M1 has `polygamma` but not Hurwitz-zeta or
factorial semantics. More importantly, the displayed bridge is one
special-function relation, not a reused multi-operator master. Fixed-order or
fixed-point lowerings fall at R5 or below. The existing recurrence and
alternating-series packages likewise remain R1/R2/R5 or proof-required; none
is R6.

### Response and differentiable-physics masters

Feshbach, Krein, Birman–Schwinger, Weyl–Titchmarsh, Lehmann, Lippmann–Schwinger,
Liouville, and state-transition candidates require operator spectra,
projectors, determinants/traces, boundary values, ODE solutions, or integrals.
The scalar Feshbach package is independently R0 shared-denominator CSE. The
van der Waals package is the strongest fully M1-compiling apparent R6 case,
but the public `G0001` is exactly its Helmholtz master and the other members
are a first-derivative/response graph; independent depth is R1.

### Debye, transfer-matrix, and tensor controls

The Debye Maxwell source genuinely uses curl, curl-of-curl, time derivative,
and vector spherical-harmonic reconstruction. The Potts source genuinely uses
matrix powers, eigenvalue reconstruction, trace, and determinant. These are
clean examples of scientific R6-like objects blocked by the current
scientific IR. Publishing their full reconstruction as a public member would
expose the master, while fixed-component/fixed-width scalarization destroys
the independent depth.

The R8 tensor candidates do not rescue R6: their existing packages are
finite-index diagnostics without symbolic projector, tensor, or
all-component reconstruction proofs.

## Exact package probes

| Package | M1 result | Independent depth | Hard failure |
|---|---|---|---|
| `mx-abba-exp-fixed-r6` | `PACKAGE_ARTIFACT_MANIFEST_INVALID` | R2 | Newton DD plus linear reconstruction; public quotient |
| `rps-r-feshbach-optical-heff` | `PACKAGE_ARTIFACT_MANIFEST_INVALID` | R0 | shared denominator CSE |
| `gf-vdw-2013-eq1` | compiles, zero schema deltas | R1 | public Helmholtz master; derivative-response graph |
| `rps-candidate-j2-001` | compiles, zero schema deltas | ineligible R3 | historical block source lowered to scalar repeated nodes |

None stores the primary R6 source bytes as a package-contained hash-bound
artifact. Exact verifier receipts for the scalar packages certify those
scalar reconstructions only; they do not certify R6 depth.

## Verdict

`R6_MISSING / PACKAGING_GAP` is the only defensible outcome. A qualifying
case would need newly stored primary source bytes and executable scientific IR
for a fresh identity, or a fresh scalar identity whose exact M1 lowering
retains at least two independent operator types without exposing the master.
Neither exists in the bounded mined registry.

No package, parser, verifier, grammar, search method, shared manifest, or TEST
artifact was changed by this audit.
