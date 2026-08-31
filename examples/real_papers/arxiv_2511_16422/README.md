# Public real-paper field validation — arXiv:2511.16422v2

This directory is a **Derivation Audit v0.2** workspace for the *public* paper

> Zhichao Guo, Xing-Yuan Liu, Hua Wang, Li-kun Shi, Kai Chang,
> “Dissipation-Shaped Quantum Geometry in Nonlinear Transport,”
> Phys. Rev. Lett. 136, 206303 (2026), [arXiv:2511.16422v2](https://arxiv.org/abs/2511.16422v2).

It is a field validation of the frozen product `derivation-audit-v0.2.0-alpha`.
It is **not** a verification of the entire paper, a novelty referee report, or
a proof of the physics.

Public authority is the arXiv v2 source. The PDF and source tarball are **not**
committed; reconstruct them from `SOURCE.yaml`.

## What was audited

A frozen set of 25 derivation edges from the public supplement:

- local algebraic rearrangements and index rewrites that lower to executable
  residuals;
- stated identities recorded as definitions;
- one $\Gamma$ asymptotic remainder claim that is **not** rewritten as an
  exact residual;
- two Brillouin-zone integration-by-parts steps classified as integral
  arguments, not local zeros.

Only engine `ZERO` rows may appear in `TABLE_VERIFIED.md`. LLM text cannot
create that table.

## Equation numbering

The compiled HTML/PDF numbers **do not reset** at each appendix
(`\theequation = \thesection-\arabic{equation}` without a per-section reset).
Appendix D therefore begins at printed Eq. (D-57), not (D-1).

`equations/CATALOG.yaml` records both the **printed** number and the
**appendix-local** index (local `D-1` = printed `(D-57)`). Citations in
reviewer tables use the printed public numbers.

## Reproduce

From a checkout with `symbolic-compactification` 0.2.0-alpha installed:

```sh
./reproduce.sh
```

Equivalent:

```sh
symbolic-compactification audit inventory .
symbolic-compactification audit inspect .
symbolic-compactification audit verify .
symbolic-compactification audit table .
symbolic-compactification audit report .
symbolic-compactification audit package .
```

Read `reports/TABLE_VERIFIED.md` for machine-verified identities.
Read `TABLE_STRUCTURAL.md`, `TABLE_UNCERTIFIED.md`, and `TABLE_NONZERO.md`
for everything else.

## Wording

We machine-verified selected executable equation-level identities from this
public derivation under the declared symbolic semantics. No machine-verified
row is authored by an LLM. Global integration and asymptotic claims are
reported separately when they fall outside the local exact verifier.

This package does **not** say the paper is fully verified, and it does **not**
say the physics is correct.

## Assumptions that were substituted, not machine-enforced

v0.2 assumptions.yaml can declare `real` / `nonzero` symbols only. Paper
identities used in residuals were **substituted into the native text**:

- $\epsilon_{21}=-\epsilon_{12}$
- $\Omega_{ab}^{2}=-\Omega_{ab}^{1}$
- $f_n'=2 f_{0,n}'$
- the two-band metric-velocity pair when inserting $g_{ab}$

Those substitutions are documented on the corresponding edges.

## Layout

```
SOURCE.yaml                 bibliographic provenance
FROZEN_EDGES.yaml           frozen edge set (predictions are not authority)
audit.yaml                  v0.2 workspace config
manuscript/source.tex       equation-only public stub (not the paper)
equations/                  curated ids + full printed-number catalog
edges/edges.yaml            typed derivation graph
expressions/                native-text residuals
assumptions/assumptions.yaml
reports/                    generated tables and REPORT.md
reviewer-verification-package/   generated package with reproduce.sh
```
