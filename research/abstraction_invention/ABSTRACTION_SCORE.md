# Abstraction quality score (domain-neutral)

Used to rank LGG hypotheses. **No gold labels.** Not tuned on TEST.

## Description length

\[
\mathrm{DL}(e) = 1 + \mathrm{count\_ops}(e)
\]

For a hypothesis with template \(F\) and instance maps \(\{m_i\}\):

\[
\mathrm{gain} = \sum_i \mathrm{DL}(A_i) - \mathrm{DL}(F) - \sum_i \mathrm{DL}(m_i)
\]

Negative gain ⇒ compression-losing (typical of F1 junk).

## Other axes (all in \([0,1]\) or \(\mathbb{R}\))

| Axis | Rule |
|---|---|
| coverage | \(n_{\mathrm{members}}/2\) clipped to 1 |
| reuse | 1 if \(n\geq 3\) else \(n/3\) |
| coherence | fraction of holes filled by a single symbol or `f(symbol)` |
| depth | \(\mathrm{ops}(F) / (1+\max_i \mathrm{ops}(A_i))\) |
| named_ops | 1 if template retains polygamma/Sum/AppliedUndef, else 0.3 if any non-hole symbol, else 0 |

## Scalar used for ranking

\[
S = 0.25\,\mathrm{gain} + 3\cdot\mathrm{depth} + 2\cdot\mathrm{coherence} + 4\cdot\mathrm{named\_ops}
\]

Filter (B2): keep if `named_ops = 1` **or** (\(\mathrm{gain}\ge 0\) and \(\mathrm{depth}\ge 0.2\)).

Weights chosen on DEV Guo templates only (junk vs polygamma family), not TEST.

Success criterion (DEV Guo + DEV LGG hyps): the polygamma-pair template
ranks above `I*mu*theta0` without gold.
