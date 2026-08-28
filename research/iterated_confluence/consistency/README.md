# Owner: V3-F — order-of-limits path consistency

Compare two iterated one-parameter paths with a common start and end.
Never treat iterated limits as a joint limit unless this auditor returns
`CONSISTENT_ZERO`. Timeout, size-guard (`count_ops > 80`), and CAS failure
are `UNKNOWN`, never `CONSISTENT_ZERO`.

```python
from research.iterated_confluence.consistency import (
    check_two_paths,
    family_zero_blocked,
    CONSISTENT_ZERO,
    INCONSISTENT_NONZERO,
    CONSISTENCY_UNKNOWN,
)

result = check_two_paths(expr, path_a_steps, path_b_steps, symbols=None)
# result.verdict      CONSISTENT_ZERO | INCONSISTENT_NONZERO | UNKNOWN
# result.provenance   deciding reason
```

Each step is `(variable, target_value)` or `PathStep`. One-parameter steps
reuse `research.scalable_verification.confluence.check_limit`. Paths are
evaluated independently; identical-looking coordinates are not assumed to
commute.

`family_zero_blocked(verdicts, require_path_independence=True)` is true
unless every verdict is `CONSISTENT_ZERO` when independence is required.
`INCONSISTENT_NONZERO` always blocks `FAMILY_ZERO`.
