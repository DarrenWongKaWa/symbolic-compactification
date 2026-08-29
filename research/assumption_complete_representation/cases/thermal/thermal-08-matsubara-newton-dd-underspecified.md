# thermal-08-matsubara-newton-dd-underspecified

**Rejected: yes.** Reason: `PROBLEM_UNDERSPECIFIED`. Ladder if it were specified: `R2_newton_dd`. `is_guo`: false.

This dossier is preserved, not deleted (admission gate). It is not Guo and must not be repaired by importing Guo pole-exclusion.

## Expression (as written in the source table)

\[
S_\eta=\frac1\beta\sum_{i\omega}g(i\omega),\qquad
g(i\omega)=\frac{1}{(i\omega-\xi_1)(i\omega-\xi_2)},
\]

\[
S_\eta=-\eta\frac{n_\eta(\xi_1)-n_\eta(\xi_2)}{\xi_1-\xi_2},
\qquad
n_\eta(\xi)=\frac{1}{e^{\beta\xi}-\eta},\quad \eta=\pm 1.
\]

Repeated-node sibling row:

\[
g(i\omega)=(i\omega-\xi)^{-2}
\quad\Rightarrow\quad
S_\eta=-\eta\, n_\eta'(\xi)=\beta n_\eta(\xi)\,(\eta+n_\eta(\xi)).
\]

## Source

Wikipedia *Matsubara summation* (redirect from Matsubara frequency), “Table of Matsubara frequency summations”, <https://en.wikipedia.org/wiki/Matsubara_frequency>.

DECLARED on the page, but **not attached to the table row**:

- \(\beta=\hbar/k_{\mathrm{B}}T\); separate “Zero temperature limit \(\beta\to\infty\)”.
- Convergence slogan: \(g(z)\) faster than \(z^{-1}\) at infinity.
- Green’s-function weighting paragraph: \(0<\tau<\beta\) for the factor \(e^{-z\tau}\).
- Footnote: the simple-pole sum \((i\omega-\xi)^{-1}\) “does not converge” and “may differ upon different choice of the Matsubara weighting function.”

NOT_DECLARED, and needed by a verifier:

- \(\xi_1\neq\xi_2\) (Newton quotient denominator).
- \(\xi_1,\xi_2\notin\{i\omega_n\}\) (poles of \(g\) disjoint from Matsubara poles of the weighting function).
- \(\xi\) not an occupancy pole \(e^{\beta\xi}=\eta\).
- \(\beta>0\) as an inequality on the table identities.

## Latent structure (why it was mined)

This **would** be first Newton divided difference of the Fermi/Bose function, with Hermite confluence to \(n'\). Beyond CSE. Admission is blocked by missing analytic-domain predicates, not by trivial algebra.

## Why PROBLEM_UNDERSPECIFIED

A task whose verifier needs NOT_DECLARED analytic-domain hypotheses is PROBLEM_UNDERSPECIFIED, not DISCOVERY_FAILURE (`ASSUMPTION_CONTRACT.md`, `SUCCESS.md`). Completing \(\xi_1\neq\xi_2\) or Matsubara pole-exclusion from physical folklore, or from another sealed problem, is forbidden.

## Proposer leak risk

Do not re-pose with gold names “Newton divided difference” / “Hermite”. Do not silently fill the domain.

## Notes

Independent Wikipedia gap. Do not import Guo’s missing pole-exclusion. Do not insert \(\beta>0\) or real \(\varepsilon\) from folklore.
