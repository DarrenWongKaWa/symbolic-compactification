# STATUSES

Copied into HTML. JavaScript must not infer ZERO.

| Status | Colour | Chip |
|---|---|---|
| `EXACT` | dark green `#2d6a4f` | Exact |
| `EXACT_IF_ASSUMPTIONS` | hatched green | Exact if A |
| `STRUCTURAL` | blue `#2e5a88` | Structural |
| `CITED_RULE` | blue | Cited rule |
| `GAP` | orange `#b86a12` | Gap |
| `HUMAN_REVIEW` | orange | Human review |
| `ASYMPTOTIC_UNCERTIFIED` | orange (dotted chip) | Asymptotic, uncertified |
| `NUMERICAL_SUPPORT` | orange | Numerical support |
| `UNCERTIFIED` | orange | Uncertified |
| `NONZERO_RESIDUAL` | dark red `#9b2c2c` | Nonzero residual |

`NUMERICAL_SUPPORT` is not a fifth colour.
Human Accept / Reject / Needs derivation is UI-only. It does not change
`audit.json` and does not turn a parent claim Exact.
