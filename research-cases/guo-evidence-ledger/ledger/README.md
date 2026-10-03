# Step ledger for Appendix D

`steps.yaml` records twelve steps of Appendix D as "Eq. X -> Eq. Y, using R".
Every formula is a verbatim quote of `../input/source_anchors/main.tex`; the
relations a step uses (metric-velocity relation, epsilon_21 = -epsilon_12,
Feynman-Hellmann identity, Berry curvature of band 1) are quoted from the text.
`conventions.yaml` names the matrix elements and the names written right before
a bracket that multiplies it.

```bash
symbolic-compactification manybody ledger research-cases/guo-evidence-ledger/ledger/steps.yaml --out /tmp/guo-ledger
```

Result: 12 VALID. Seven are exact algebra; five hold under the quoted
relations, each with explicit cofactors. The hand-transcribed relations in
`../evidence/RELATIONS_FROZEN.yaml` cover the same steps (R039, R041, R042,
R048, R051, R052-R056 and neighbours); here nothing is retyped.
