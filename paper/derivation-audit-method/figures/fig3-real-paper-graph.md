# Figure 3 — Public real-paper derivation graph

**Source.** Guo et al., PRL 136, 206303 (2026), arXiv:2511.16422v2.
Evidence branch `engineering/real-paper-validation-arxiv-2511-16422`
(`69ad474`), workspace `examples/real_papers/arxiv_2511_16422/`.

**Caption (draft).** Selected equation-level edges from the public
supplement, coloured by certificate class. 25 paper-selected steps plus one
shared local Leibniz child used by the two Brillouin-zone IBP parents.
This figure is an audit graph, not a proof of the paper.

Colour key:

| Class | Meaning |
|---|---|
| DIRECT_EXACT | unsubstituted engine ZERO |
| SUBSTITUTION_EXACT | ZERO after a declared identity is substituted |
| RULE_CERTIFICATE | local ZERO + declared `BZ_TORUS_PERIODICITY` |
| STRUCTURAL | definition / split / bookkeeping |
| ASYMPTOTIC / UNKNOWN | remainder not rewritten as an exact residual |

Suggested spine (Appendix D, printed numbers; local D-1 = printed D-57):

```text
(D-57)  ASYMPTOTIC UNKNOWN
(D-59)→(D-60)  DIRECT_EXACT     K1A regroup
(D-60)         SUBSTITUTION     metric-velocity pair
(D-60)→(D-61)  DIRECT_EXACT     TA prefactor
(D-66)→(D-67)  SUBSTITUTION     ε21 = −ε12
(D-61)+(D-67)→(D-68) DIRECT     TA + TBgeo cancel
(D-71)→(D-72)  DIRECT_EXACT     C12 regroup
(D-73)         DIRECT_EXACT     Vab expand / ε21 algebra
(D-74)         DIRECT_EXACT     A antisym
(D-74)→(D-75)  SUBSTITUTION     A → Ω definition
(D-70)→(D-77)  DIRECT_EXACT     σ^(−1) I·I cancel
(D-77)→(D-78)  SUBSTITUTION     Ω² = −Ω¹
(D-114)→(D-119) RULE            BZ IBP T0  (child: Leibniz ZERO)
(D-119) local  DIRECT_EXACT     T0 sign algebra
(D-120)→(D-121) DIRECT_EXACT    T0+T1 regroup
(D-123)→(D-124) RULE            BZ IBP T2  (same Leibniz child)
(D-122)+(D-124)→(D-125) DIRECT  geo after declared T2
(D-125)→(D-126) SUBSTITUTION    ε21 symmetrize
(D-126)→(D-127) SUBSTITUTION    f' = 2 f0' compact rewrite
```

Do not include unpublished local manuscripts. Do not add unaudited edges
to make the graph look complete.
