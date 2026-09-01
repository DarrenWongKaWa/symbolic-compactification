# FINAL REPORT — approximation authority v1

**Verdict:** `FOUR_DIAGNOSTIC_CASES_DISTINGUISHED`

Product: `derivation-audit-v0.2.1-alpha` peel `783ec64`.
Engine: `python_sympy_exact_v1` / `0.3.0`.
`src/` was not modified. Engine `ZERO` was not weakened.

## Question

Not: can an approximation be made to return `ZERO`?

\[
\text{who authorized the approximation?}
\quad+\quad
\text{after it is adopted, does later algebra still hold exactly?}
\]

## Invariant

\[
\texttt{ZERO}=\text{exact ZERO}
\]

A parent that packages a declared approximation plus a child `ZERO` is
recorded only as the experiment overlay

\[
\texttt{CERTIFIED\_UNDER\_DECLARED\_APPROXIMATION}
\]

never as engine `ZERO`. Same epistemic split as
`CERTIFIED_BY_RULE` \(\neq\) `ZERO`.

Observed: `parent_overlay_called_ZERO = []`.

## Four diagnostic cases

| Case | Task | Provenance | Naive \(E_0-E_1\) | After \(T_A\) | Overlay |
|---|---|---|---|---|---|
| 1 author + downstream holds | AA-01 | `AUTHOR_DECLARED` | `NONZERO` | `ZERO` | `CERTIFIED_UNDER_DECLARED_APPROXIMATION` |
| 2 author + downstream fails | AA-02 | `AUTHOR_DECLARED` | `NONZERO` | `NONZERO` | `REFUSED_DOWNSTREAM_NONZERO` |
| 3 author + remainder uncertified | AA-03 Guo (D-57) | `AUTHOR_DECLARED` | not lowered | n/a | `ASYMPTOTIC_DECLARED_ONLY` (`UNKNOWN`) |
| 4 undeclared hidden approx | AA-04 | `NONE` | `NONZERO` | hidden probe `ZERO` | `UNDECLARED_APPROXIMATION_REQUIRED` |

All four distinguished: **true**. All nine frozen tasks distinguished: **9/9**.

Naive `NONZERO` on AA-01 is **not** a manuscript error. It is the remainder
\(G^2 R\). The author-declared arrow is \(E_0\rightsquigarrow\widetilde E_0\);
the machine-checked arrow is \(\widetilde E_0-E_1=0\).

AA-04 is the audit use case: the same bytes as AA-01, without authorization,
must not promote as an exact identity.

## Contrasts (must not be swallowed by approximation)

- AA-05 Guo \(K_{1A}\) regroup: exact `ZERO`. No approximation.
- AA-06 Guo \(T_{B,\mathrm{geo}}\) \(e_{21}=-e_{12}\): substitution/assumption
  gap from Forward RQ1, **not** an approximation.
- AA-07 model-proposed truncation: downstream `ZERO`, overlay
  `MODEL_APPROX_NOT_AUTHORIZED`.
- AA-08 remainder encoded as exact equivalence: `NONZERO` (threat model).
- AA-10 \(G^0\) coefficient child `ZERO`; remainder still not certified (NR-004).

## What this does not claim

- That remainders are now certified.
- That a product status was added.
- That hidden-approximation detection is a general search procedure.
- That this is a core claim of the current Technique paper.

It is an **RQ4 candidate**. Paper Discussion may mention the principle;
the abstract and contribution list stay unchanged.

## Principle

\[
\text{Approximation may be authorized; its consequences must still be verified.}
\]

Parallel to: an AI may propose; it may not certify itself.
Parallel to: `CERTIFIED_BY_RULE` is not engine `ZERO`.
