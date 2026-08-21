# Long example (σ_abc input)

Raw Guo exact-DC σ_abc source. See `SOURCE.md` for hash and provenance.

```bash
symbolic-compactification inspect \
  examples/long/Guo_Sigma_abc_dc_exact.txt \
  --format wolfram --json
```

JSON `text` is the full native translation (not the 200-character preview).
Write that to `current.txt` before `init-session` / `step`. This inspects
structure only. It does not certify a compact rewrite.
