# Owner: V3-E — path composition

PATH_ZERO is not FAMILY_ZERO. This package composes local edge verdicts
into a path verdict. It does not certify a family.

`PATH_ZERO` iff every required step is ZERO. Any step NONZERO ⇒
`PATH_NONZERO`. Otherwise `PATH_UNKNOWN`. Empty path is `PATH_UNKNOWN`,
not `PATH_ZERO`.

The rule is imported from `schema.compose_path_verdict` (do not edit
`schema.py`). Family composition is owned by schema + V3-F consistency.

```python
from research.iterated_confluence.compose import compose_path, compose_paths
from research.iterated_confluence.schema import PathCertificate, PathStep, PATH_ZERO

cert = compose_path(["ZERO", "ZERO"], path_id="p", start="A", end="C")
# cert.path_verdict == PATH_ZERO

filled = compose_paths([cert])
# filled[0].path_verdict recomputed from steps
```
