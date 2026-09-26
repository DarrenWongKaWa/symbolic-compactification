# Table 4 — Capability boundary

| Surface | Status | Notes |
|---|---|---|
| Typed equation-to-equation graph | SUPPORTED | frozen edge catalogue |
| Exact local residual (`lhs−rhs`) | SUPPORTED | engine `0.3.0`, route `python_sympy_exact_v1` |
| `ZERO` / `NONZERO` / `UNKNOWN` | SUPPORTED | fail-closed; no narrative promotion |
| Generated reviewer tables | SUPPORTED | inclusion functions only |
| Hash-bound provenance | SUPPORTED | source, residual, assumptions, obligation |
| Reviewer package + `reproduce.sh` | SUPPORTED | tables regenerated from bound run |
| BZ periodic IBP rule certificate | SUPPORTED | one field-driven rule; parent ≠ engine `ZERO` |
| Pairwise / projector / index relabel | PARTIAL | local kernel yes; global sums not swallowed |
| Completeness reconstruction | PARTIAL | only with explicit residual + declared rule |
| Special-function identities | PARTIAL | only inside the declared verifier catalogue |
| Limit claims | PARTIAL | naked limits are not identities |
| Integral arguments in general | UNSUPPORTED | generic `INTEGRAL_ARGUMENT` is `NOT_LOWERED` |
| Asymptotic remainder proof | UNSUPPORTED | coefficient `ZERO` ≠ remainder certificate |
| Parameter identities as assumptions | UNSUPPORTED | must be substituted and labelled `SUBSTITUTION_EXACT` |
| Complex-domain certification | UNSUPPORTED | `real: false` rejected |
| Full manuscript proof | UNSUPPORTED | equation-level audit only |
| Physical-conclusion verification | UNSUPPORTED | out of scope |
| Autonomous discovery / representation invention | UNSUPPORTED | scientific campaigns closed |
| General theorem proving | UNSUPPORTED | rule growth is field-driven and narrow |
