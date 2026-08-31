# Brillouin-zone integration by parts

These parents are **not** engine ZERO. SymPy did not evaluate a BZ integral.
Certificate = local Leibniz `ZERO` + declared `BZ_TORUS_PERIODICITY` on
`BRILLOUIN_ZONE_TORUS`. Missing periodicity would be `ASSUMPTION_REQUIRED`.

| Paper step | Local identity | Global rule | Assumptions | Status |
| --- | --- | --- | --- | --- |
| Eq. (D-114) → Eq. (D-119) | `D.leibniz-product-rule` ZERO | BZ periodic IBP | periodic smooth gauge-invariant integrand on BZ torus | `CERTIFIED_BY_RULE` |
| Eq. (D-123) → Eq. (D-124) | `D.leibniz-product-rule` ZERO | BZ periodic IBP | periodic smooth gauge-invariant integrand on BZ torus | `CERTIFIED_BY_RULE` |
