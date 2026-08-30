# R2/R6 candidate mining audit

## Outcome

Two candidate-only packages survived the bounded mining pass. Neither was
placed in a benchmark partition or shared manifest.

| candidate | proposed depth | exact obligations | M1 deltas | disposition |
|---|---:|---:|---:|---|
| `gf-cr3bp-2017-eq28` | R2 | 4 ZERO | 0 | pass to independent admission review |
| `gf-vdw-2013-eq1` | R6 | 8 ZERO | 0 | pass to independent **depth** and admission review |

## R2: operational gravitational divided differences

Wan, Bihlo, and Nave derive conservative finite-difference schemes for real
ODE systems. In Section 5.3 they apply divided-difference calculus to the
planar restricted three-body problem. Their displayed equations give four
factorized coordinate-wise divided differences of reciprocal gravitational
distance terms. Appendix B defines the divided difference and states the
calculus rules used in the derivation.

- Primary source: Andy T. S. Wan, Alexander Bihlo, and Jean-Christophe Nave,
  “Conservative methods for dynamical systems,” *SIAM Journal on Numerical
  Analysis* 55(5), 2255–2285 (2017), DOI
  [10.1137/16M110719X](https://doi.org/10.1137/16M110719X),
  [open source text](https://arxiv.org/html/1612.02417v1).
- Exact locus: Section 5.3, equations after Eq. (27), especially the four
  displayed identities corresponding to source lines 544–553; Appendix B,
  Definition 31 and Theorem 33.
- Domain: real coordinates, positive relative masses, noncollision, distinct
  old/new coordinate and induced squared-distance nodes. Positivity and
  denominator nonvanishing are DECLARED or DERIVED in the exact assumption
  contract.

The package has one `SCALAR_KERNEL`, four distinct two-node structures, four
`NEWTON_DD` operations, and four chain-rule `LINEAR_COMBINATION` operations.
It is operational because the four members are actual components of a
conservative scientific discretization, not a standalone textbook quotient.

This remains a named-operator R2 calibration candidate. Its success would not
by itself demonstrate primitive-grammar invention.

## R6: Helmholtz thermodynamic graph

The second package starts from the real van der Waals Helmholtz free energy
`F(T,V,N)` at fixed `N`. It builds two derivative branches (`p` and `S`),
reconstructs `U` and `H`, differentiates `U` for `C_V`, differentiates `p` for
the isothermal bulk modulus, and composes a reciprocal kernel for isothermal
compressibility.

- Source expression: Markus Deserno, “Van der Waals equation, Maxwell
  construction, and Legendre transforms,” Eq. (1), Carnegie Mellon University
  Department of Physics (2013), [PDF](https://www.cmu.edu/biolphys/deserno/pdf/van-der-Waals-and-Maxwell.pdf).
- Helmholtz derivative semantics: NIST,
  [“Thermodynamic Derivatives — teqp”](https://pages.nist.gov/teqp-docs/en/latest/derivs/derivs.html).
- Response definition: Gennady Y. Gor and Alexander V. Neimark,
  “Modulus-pressure equation for confined fluids,” *Journal of Chemical
  Physics* 145, 164505 (2016), DOI
  [10.1063/1.4964683](https://doi.org/10.1063/1.4964683), Eqs. (5)–(6),
  [NIST-hosted PDF](https://tsapps.nist.gov/publication/get_pdf.cfm?pub_id=921308).

The scientific scope is one homogeneous real branch with `T>0`, `V>N*b`, and
fixed `N` and model constants. The compressibility member additionally excludes
the zero-bulk-modulus spinodal. The package makes no Maxwell-construction,
coexistence, or stability claim.

Why it is a plausible R6 candidate:

- eight nontrivial source/derived members;
- two latent objects, with the reciprocal object used only where physically
  required;
- five operator types and a branching, reused dependency graph;
- all operators are available in `G_PRIMITIVE`, so no named MASTER or
  thermodynamics-specific grammar primitive supplies the answer;
- no member-specific latent object and no independent expression memorization.

Why it is not yet an admitted R6:

- the exact Helmholtz formula is from an institutional note rather than a
  peer-reviewed primary article (the derivative/response semantics have
  authoritative and peer-reviewed corroboration);
- a reviewer may judge the family as a familiar thermodynamic derivative graph
  rather than a new R6 master abstraction;
- `PACKAGE_READY` certifies the exact lowerings, not the representation-depth
  label.

## Freshness and leakage

The frozen structural audit compared the exact source-member expressions and
public projections against:

- 79 historical benchmark/case documents, including the previous
  assumption-complete corpus;
- 47 current mined case dossiers;
- 13 existing RPS packages.

Neither candidate produced an exact, renamed, grammar-syntax, hidden-role,
Guo, trivial-CSE, or first-order-LGG finding. The nearest weighted similarities
were 0.278 for R2 and 0.406 for R6, both below the frozen 0.58 review threshold.
Natural scientific source names remain private in `source_manifest.json`; the
public proposer view contains only member ids, paths, hashes, and the exact
assumption/catalog links.

This is a gold-free screening result, not an automatic admission verdict.

## Integrity boundary

- No TEST identity, evaluator label, or reference program was used for mining.
- Guo remained sealed and was not run.
- No parser, verifier, grammar, search method, or benchmark manifest changed.
- Every equality has a recorded main-agent `HYPOTHESIS` step followed by an
  exact `CERTIFIED`/`ZERO` verifier step.
- Web search and Codex-assisted filtering were used for discovery. Generated
  prose was not accepted as evidence; retained claims are source-located and
  exact equations are machine-verified.
