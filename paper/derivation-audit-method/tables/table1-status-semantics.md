# Table 1 — Status / certificate semantics

Certificate class describes provenance, not truth ranking.

| Class / status | How it is obtained | Enters `TABLE_VERIFIED`? |
|---|---|---|
| `DIRECT_EXACT` | Engine `ZERO` on an unsubstituted residual | yes, if integrity-ok executable `ZERO` |
| `SUBSTITUTION_EXACT` | Engine `ZERO` after a declared identity is written into the residual | yes, same machine bar; overlay cannot add a row |
| `CERTIFIED_BY_RULE` | Local child `ZERO` + declared theorem/domain | **no** (structural / IBP table) |
| `DEFINITION` / `RECORDED` / `SPLIT` | Typed non-executable tracking | no (`TABLE_STRUCTURAL`) |
| `UNKNOWN` | No exact proof either way | no (`TABLE_UNCERTIFIED`) |
| `NONZERO` | Exact probe of a nonzero residual | no (`TABLE_NONZERO`) |
| `NOT_LOWERED` | No executable residual / missing rule child | no (`TABLE_UNCERTIFIED`) |
| `ASSUMPTION_REQUIRED` | Required declared rule or assumption missing | no |

Invariant: `ZERO ≠ CERTIFIED_BY_RULE`.
