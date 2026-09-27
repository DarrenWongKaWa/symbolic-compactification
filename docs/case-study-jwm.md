# Case study: reviewing a classic Keldysh paper

I reviewed the following paper with step cards drafted from its LaTeX
source:

> A.-P. Jauho, N. S. Wingreen and Y. Meir, *Time-dependent transport in
> interacting and non-interacting mesoscopic systems*, Phys. Rev. B **50**,
> 5528 (1994), arXiv:cond-mat/9404027.

The workspace is `examples/case-studies/jwm1994/`. The paper is not
shipped with this repository. The script downloads the arXiv TeX source
and runs the review:

```bash
examples/case-studies/jwm1994/fetch_and_run.sh /tmp/jwm1994-review
MUTATE=1 examples/case-studies/jwm1994/fetch_and_run.sh /tmp/jwm1994-mutated
```

## What the tool could check

`manybody draft` turned the 88 displayed environments into 137 candidate
steps. Most are Keldysh Green-function relations with time integrals,
matrix structure in the leads, or Bessel-function sums. None of the
checks covers these forms, so they stay outside the review. Three steps
are checkable with the current checks, and the cards quote them verbatim:

| Step | Check | Result |
|---|---|---|
| Long-time limit of Eq. (Aabrupt): `A(ε, t → ∞) = [ε − (ε₀ + Δ) + iΓ/2]⁻¹` | `remainder` at t → ∞ (exponential-decay route) | valid after bracket erratum |
| Short-time form: `A(ε, t) ≃ (1 − iΔδt)/(ε − ε₀ + iΓ/2)` | `remainder` at δt → 0, order 2 | valid after bracket erratum |
| Appendix relation `Σ_{n≥0} 1/((n+a)(n+b)) = [Ψ(a) − Ψ(b)]/(a − b)` | `series` (digamma rule) | **CERTIFIED_BY_RULE** |

## A typesetting defect the tool found

As printed in the arXiv source, Eq. (Aabrupt) cannot be read:

```tex
[1-\exp{[i(\epsilon-(\epsilon_0+\Delta)+i\Gamma/2)(t-t_0)}]
```

It opens two square brackets and closes one. TeX does not check that
brackets pair up, so the defect survives typesetting. The tool refuses to
guess (`SOURCE_BRACKETS_UNBALANCED`), so neither step that uses this
equation is decided for the printed text. The cards declare the obvious
bracket-only erratum, a closing `]`, and both limits hold for the
corrected formula. The reviewer page shows the printed and corrected forms
side by side, and it gives the verdict as "VALID after bracket erratum",
never plain VALID.

## Planted errors are caught

`MUTATE=1` flips two signs, both in the paper and in the cards' quotes:
- in the digamma relation, `[Ψ(b) − Ψ(a)]`;
- in the short-time form, `1 + iΔδt`.

The review then reports:
- the digamma relation as `NONZERO`, with a counterexample and the
  diagnosis `claim = -(computed)`;
- the short-time form as invalid after the erratum.

The long-time limit is unchanged and still passes.

## What this shows

- **The review is honest about coverage.** The tool decides 3 of 137
  drafted relations, which cover the paper's closed-form claims in its
  wide-band limit and its appendix. The report does not claim that the
  rest of the paper is verified.
- **Nothing was retyped.** Each expression comes from a verbatim quote,
  located by line, equation number and `\label`. The hand-written part is
  `cards/conventions.yaml`: the symbols, the time origin `t₀ = 0`,
  `δt = t − t₀`, and `Ψ` = digamma. It is listed on the reviewer page so
  it can be checked once.
- **Printed-formula defects are findings, not failures.** A formula that
  cannot be parsed as printed is reported as such, together with the
  verdict under a declared bracket-only correction.
