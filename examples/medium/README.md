# Medium example

Neutral `Sum` compactification. `current.txt` is two identical sums;
`candidate.txt` factors the coefficient; `mutation.txt` is a wrong
coefficient (NONZERO).

```bash
symbolic-compactification verify \
  --current examples/medium/current.txt \
  --candidate examples/medium/candidate.txt \
  --symbols examples/medium/symbols.json
```
