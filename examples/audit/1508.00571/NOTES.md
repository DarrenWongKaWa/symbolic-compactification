# NOTES — arXiv:1508.00571

One pass. Prefer fewer honest edges.

This PRL source has no derivation appendix (`\\appendix` is absent). The 19 display equations are the full numbered set in `NonLin-Halleffect.tex`. Extra material is footnotes and a figure, not numbered eqs.

Refused to green:
- Boltzmann → f1/f2 (xx): solving the RTA ODE was not compiled.
- (vel),(xx) → (ja0): k-space integrals, not a local residual.
- Semiclassical χ terms “forced to vanish” under TR: claimed cancel; Sign button; not auto-green.
- Ω_s from H and Berry: 2×2 Berry curvature not compiled this pass.
- D_y closed form: Fermi-surface integral after an area-preserving map; special/integral, not local algebra.
- Point-group classification of D^±: representation theory, not numbered algebra.
- BZ / Fermi-surface integrals generally.

Greened only:
- H_sΛ eigenvalues under A: s^2 = 1 (paper states s = ±1). sympy det(H − λI) = k_y^2 v_y^2 (1 − s^2). ZERO_UNDER_SUBSTITUTION. Does not prove s = ±1.

missing_declared_moves: not certified. Prose-only Onsager/linear-response remarks out of scope.
