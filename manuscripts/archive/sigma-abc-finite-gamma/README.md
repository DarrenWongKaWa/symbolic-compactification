# Manuscript audit: finite-Γ σ_abc

Source: `symbolic-compactification-clean-test/main5.pdf` plus
`symbolic-compactification-clean-test/supplement.pdf`
(Kawa Wong, *Quantum geometry of nonlinear DC transport at finite dissipation*,
31 August 2026).

The supplement is used to lower *coefficient* identities of the weak-Γ
Laurent analysis (explicit \(M_0\), \(T_0\), \([\omega^2]\) recipe, Anan
dictionary) to two-sided residuals. The remainder statement
\(\sigma(\Gamma)=B/\Gamma+O(\Gamma)\) stays `UNKNOWN`: the supplement itself
calls this a weak-Γ asymptotic reduction, not a pointwise exact identity.

This is a **Mode A** audit: verify the manuscript’s stated derivation edges.
It does not propose new representations and does not rewrite the physics to
chase a green board.

```text
LaTeX/PDF manuscript
    → equation inventory
    → typed derivation edges
    → machine-readable obligations
    → ZERO / NONZERO / UNKNOWN
    → reviewer package
```

Not every adjacent equation pair is `E_i - E_{i+1} = 0`. Edges are typed:

| type | what is checked |
|---|---|
| `algebra` | exact symbolic identity |
| `index_swap` | dummy-index / permutation identity |
| `definition` | expanded form vs defined compact form |
| `symmetry` | explicit TRS / mirror map |
| `limit` | Γ→0 or ω→0; **not** a naked difference |
| `asymptotic` | coefficient plus remainder order |
| `integration` | integrand identity, boundary assumption, integrated claim |

Limits and remainder claims are fail-closed: finite Laurent matching is not
an exact limit. Those edges stay `UNKNOWN` unless a remainder certificate
exists. `NONZERO` is treated as a manuscript defect signal, not a test
failure to be edited away.

## Run

```bash
cd verification
./reproduce.sh
```

Requires the v0.1 research-preview package on Python 3.12.
See `verification/reports/SUMMARY.md` and
`verification/reports/TABLE_S_VERIFICATION.md` after a run.

## Audit claim (frozen)

Exact algebraic, coefficient-level, permutation, and local symmetry identities
that were lowered to executable residuals were checked under the declared
symbolic semantics; all currently executable residuals evaluate to ZERO and
none to NONZERO. Definitions, integral-level arguments, and asymptotic
remainder claims are tracked separately rather than being misreported as
algebraic identities.

This package is frozen at that stopping criterion. Remainder claims such as
`σ = B/Γ + O(Γ)` are left UNKNOWN on purpose.
