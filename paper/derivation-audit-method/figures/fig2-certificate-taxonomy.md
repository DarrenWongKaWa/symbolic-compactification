# Figure 2 — Certificate taxonomy

**Caption (draft).** Certificate class describes **provenance**, not a
ranking of mathematical truth. `DIRECT_EXACT` is an unsubstituted engine
`ZERO`. `SUBSTITUTION_EXACT` is engine `ZERO` after a declared upstream
identity is written into the residual. `RULE_CERTIFICATE` is a local child
`ZERO` plus a declared theorem/domain; the parent is never engine `ZERO`.
`STRUCTURAL` records definitions, splits, and bookkeeping.
`ASYMPTOTIC` / `UNKNOWN` is a remainder or other claim the engine cannot
certify.

```text
Claim
  ├─ Engine certificate
  │    ├─ DIRECT_EXACT
  │    └─ SUBSTITUTION_EXACT
  ├─ Rule certificate          CERTIFIED_BY_RULE
  ├─ Structural record         DEFINITION / RECORDED / SPLIT
  └─ Uncertified claim         UNKNOWN / NOT_LOWERED / ...
```

Do not draw these as a pyramid of decreasing credibility.
