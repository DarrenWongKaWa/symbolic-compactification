# Track V5-J — numeric falsifier

High-precision numeric samples of \(\lim_{t \to 0} E_{\mathrm{gen}}\) vs
\(E_{\mathrm{diag}}\).

This package is **not a verifier**. Numeric agreement is never `ZERO`.
Strong mismatch is `SUSPECT_NONZERO` for investigation only; an exact
path is still required.

```python
from research.coefficient_laurent.numeric import numeric_probe

numeric_probe(e_gen, e_diag)  # "agree" | "disagree" | "undecided"
```

No LLM. Timeout / parse / size-guard → `undecided`.
